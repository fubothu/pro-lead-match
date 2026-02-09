import json
import pandas as pd
import concurrent.futures
from typing import List, Dict, Optional, Callable
from ..models import Lead, EnrichmentResult
from ..scorer import LeadScorer


def _address_from_result(res: EnrichmentResult) -> Optional[str]:
    """Extract a single address string from Google or Yelp raw response."""
    if res.raw_google and res.raw_google.get("formattedAddress"):
        return res.raw_google["formattedAddress"]
    if res.raw_yelp:
        loc = res.raw_yelp.get("location") or {}
        parts = [
            loc.get("address1"),
            loc.get("city"),
            loc.get("state"),
            loc.get("zip_code"),
        ]
        formatted = ", ".join(str(p) for p in parts if p)
        return formatted or None
    return None


def _google_url_from_result(res: EnrichmentResult) -> Optional[str]:
    """Build a Google Maps URL to verify the business (place_id link)."""
    if not res.raw_google:
        return None
    place_id = res.raw_google.get("id")
    if not place_id:
        return None
    # API may return "places/ChIJ..." or just "ChIJ..."
    pid = str(place_id).replace("places/", "").strip()
    if not pid:
        return None
    return f"https://www.google.com/maps/place/?q=place_id:{pid}"


def _yelp_url_from_result(res: EnrichmentResult) -> Optional[str]:
    """Build a Yelp business URL to verify the business."""
    if not res.raw_yelp:
        return None
    biz_id = res.raw_yelp.get("id")
    if not biz_id:
        return None
    return f"https://www.yelp.com/biz/{biz_id}"


class BatchProcessor:
    @staticmethod
    def process_csv(
        file,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        failed_rows_callback: Optional[Callable[[int, List[str]], None]] = None,
    ) -> pd.DataFrame:
        """
        Reads a CSV file-like object and processes rows in parallel.
        Expected columns: 'business_name', 'phone', 'zip_code', 'email'
        progress_callback(done_count, total_count) is called after each row is processed.
        failed_rows_callback(row_index, api_errors) is called when a row has API errors (e.g. 400, 429) or an exception.
        """
        try:
            # Force all columns to be strings to prevent phone/zip corruption (e.g. dropping leading + or 0)
            df = pd.read_csv(file, dtype=str)
            # Normalize column names to lower case
            df.columns = df.columns.str.lower().str.strip()

            required_cols = {'business_name', 'phone', 'zip_code', 'email'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")

            total_rows = len(df)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Prepare futures
                future_to_row = {}
                for index, row in df.iterrows():
                    zip_val = row['zip_code']
                    if pd.isna(zip_val) or str(zip_val).strip().lower() == 'nan':
                        zip_val = ''
                    else:
                        zip_val = str(zip_val)
                    phone_val = row['phone']
                    if pd.isna(phone_val) or str(phone_val).strip().lower() == 'nan':
                        phone_val = ''
                    else:
                        phone_val = str(phone_val)
                    lead = Lead(
                        business_name=str(row['business_name']),
                        phone=phone_val,
                        zip_code=zip_val,
                        email=str(row['email']) if pd.notna(row['email']) else ""
                    )
                    future = executor.submit(LeadScorer.enrich_and_score, lead)
                    future_to_row[future] = index

                # Collect results and report progress as each completes
                processed_data = {}  # Map index to result for verified order
                for future in concurrent.futures.as_completed(future_to_row):
                    index = future_to_row[future]
                    try:
                        res: EnrichmentResult = future.result()
                        processed_data[index] = {
                            "score": res.score,
                            "quality_tier": res.quality_tier,
                            "verified_name": res.verified_business_name,
                            "google_website": res.website,
                            "match_reasons": "; ".join(res.match_reasons),
                            "sources": ", ".join(res.sources),
                            "google_validated": res.google_validated,
                            "yelp_validated": res.yelp_validated,
                            "address": _address_from_result(res),
                            "google_url": _google_url_from_result(res),
                            "yelp_url": _yelp_url_from_result(res),
                            "raw_google": json.dumps(res.raw_google, default=str) if res.raw_google else "",
                            "raw_yelp": json.dumps(res.raw_yelp, default=str) if res.raw_yelp else "",
                            "google_similarity": f"{res.google_similarity:.4f}" if res.google_similarity is not None else "",
                            "yelp_similarity": f"{res.yelp_similarity:.4f}" if res.yelp_similarity is not None else "",
                            "google_similarity_matched_name": res.google_similarity_matched_name or "",
                            "yelp_similarity_matched_name": res.yelp_similarity_matched_name or "",
                        }
                        if res.api_errors and failed_rows_callback:
                            failed_rows_callback(int(index), res.api_errors)
                    except Exception as e:
                        processed_data[index] = {
                            "score": 0,
                            "quality_tier": "Error",
                            "verified_name": None,
                            "google_website": None,
                            "match_reasons": str(e),
                            "sources": "",
                            "google_validated": "Failed",
                            "yelp_validated": "Failed",
                            "address": None,
                            "google_url": None,
                            "yelp_url": None,
                            "raw_google": "",
                            "raw_yelp": "",
                            "google_similarity": "",
                            "yelp_similarity": "",
                            "google_similarity_matched_name": "",
                            "yelp_similarity_matched_name": "",
                        }
                        if failed_rows_callback:
                            failed_rows_callback(int(index), [f"exception:{str(e)}"])
                    if progress_callback:
                        progress_callback(len(processed_data), total_rows)

            # Append results to original DataFrame (use suffixes if input has same column names)
            result_df = pd.DataFrame.from_dict(processed_data, orient='index')
            final_df = df.join(result_df, lsuffix="_input", rsuffix="")
            # Prefer our result columns when we added both; drop input duplicates
            overlap = [c for c in result_df.columns if c in df.columns]
            for col in overlap:
                final_df.drop(columns=[f"{col}_input"], inplace=True)
            return final_df

        except Exception as e:
            raise e
