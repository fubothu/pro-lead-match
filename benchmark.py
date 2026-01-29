import pandas as pd
import sys
from lead_quality_system.scorer import LeadScorer
from lead_quality_system.models import Lead
from dotenv import load_dotenv

# Load env vars
load_dotenv(override=True)

def normalize_url(url):
    """Simple normalization to compare URLs ignoring protocol and www"""
    if not url: return ""
    return url.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")

def run_benchmark(csv_path="leads_golden_test.csv"):
    print(f"Loading benchmark file: {csv_path}...")
    try:
        df = pd.read_csv(csv_path, dtype=str)
    except FileNotFoundError:
        print(f"❌ Error: File '{csv_path}' not found.")
        return

    required_cols = {'business_name', 'phone', 'zip_code', 'expected_website'}
    if not required_cols.issubset(df.columns):
        print(f"❌ Error: Missing columns. Found: {list(df.columns)}")
        return

    print(f"🚀 Starting Benchmark on {len(df)} leads...\n")
    
    correct_count = 0
    results_data = []
    
    # Iterate through rows
    for idx, row in df.iterrows():
        lead = Lead(
            business_name=row['business_name'],
            phone=row['phone'],
            zip_code=row['zip_code'],
            email=row.get('email', "") if pd.notna(row.get('email')) else ""
        )
        
        expected_raw = row.get('expected_website', "") if pd.notna(row.get('expected_website')) else ""
        expected_norm = normalize_url(expected_raw)
        
        print(f"[{idx+1}/{len(df)}] Checking: {lead.business_name}...", end=" ", flush=True)
        
        try:
            result = LeadScorer.enrich_and_score(lead)
            found_raw = result.website
            found_norm = normalize_url(found_raw)
            
            # Match Logic
            match = False
            if not expected_norm and not found_norm:
                match = True
            elif expected_norm and found_norm:
                if expected_norm == found_norm:
                    match = True
                elif expected_norm in found_norm or found_norm in expected_norm:
                    match = True
            
            status = "MATCH" if match else "MISMATCH"
            reason = ""
            if match:
                print("✅ MATCH")
                correct_count += 1
            else:
                print("❌ MISMATCH")
                if not found_raw:
                    reason = "Not found by Maps/Yelp"
                else:
                    reason = "URL Mismatch"
            
            results_data.append({
                "Business Name": lead.business_name,
                "Expected URL": expected_raw,
                "Found URL": found_raw if found_raw else "Not Found",
                "Status": status,
                "Sources": ", ".join(result.sources),
                "Notes": reason
            })
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results_data.append({
                "Business Name": lead.business_name,
                "Expected URL": expected_raw,
                "Found URL": "ERROR",
                "Status": "ERROR",
                "Sources": "",
                "Notes": str(e)
            })

    # Save Report
    report_df = pd.DataFrame(results_data)
    report_df.to_csv("benchmark_results.csv", index=False)

    # Final Summary
    total_count = len(df)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print("\n" + "="*40)
    print(f"BENCHMARK COMPLETED")
    print("="*40)
    print(f"Total Leads: {total_count}")
    print(f"Correct:     {correct_count}")
    print(f"Accuracy:    {accuracy:.1f}%")
    print(f"Detailed Report saved to: benchmark_results.csv")
    print("="*40)

if __name__ == "__main__":
    run_benchmark()
