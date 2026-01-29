import pandas as pd
import concurrent.futures
from typing import List, Dict
from ..models import Lead, EnrichmentResult
from ..scorer import LeadScorer

class BatchProcessor:
    @staticmethod
    def process_csv(file) -> pd.DataFrame:
        """
        Reads a CSV file-like object and processes rows in parallel.
        Expected columns: 'business_name', 'phone', 'zip_code', 'email'
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
            
            results = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Prepare futures
                future_to_row = {}
                for index, row in df.iterrows():
                    lead = Lead(
                        business_name=str(row['business_name']),
                        phone=str(row['phone']),
                        zip_code=str(row['zip_code']),
                        email=str(row['email']) if pd.notna(row['email']) else ""
                    )
                    future = executor.submit(LeadScorer.enrich_and_score, lead)
                    future_to_row[future] = index

                # Collect results
                processed_data = {} # Map index to result for verified order
                for future in concurrent.futures.as_completed(future_to_row):
                    index = future_to_row[future]
                    try:
                        res: EnrichmentResult = future.result()
                        processed_data[index] = {
                            "score": res.score,
                            "quality_tier": res.quality_tier,
                            "verified_name": res.verified_business_name,
                            "website": res.website,
                            "match_reasons": "; ".join(res.match_reasons),
                            "sources": ", ".join(res.sources)
                        }
                    except Exception as e:
                        processed_data[index] = {"score": 0, "quality_tier": "Error", "match_reasons": str(e)}

            # Append results to original DataFrame
            result_df = pd.DataFrame.from_dict(processed_data, orient='index')
            final_df = df.join(result_df)
            return final_df

        except Exception as e:
            raise e
