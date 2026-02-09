import os
from io import BytesIO
from datetime import datetime

import streamlit as st
import pandas as pd
from lead_quality_system.models import Lead
from lead_quality_system.scorer import LeadScorer
from lead_quality_system.services.csv_processor import BatchProcessor
from lead_quality_system.config import Config

# Shard size for batch processing; results are written to file after each shard
BATCH_SHARD_SIZE = 1000
BATCH_OUTPUT_DIR = "batch_output"

st.set_page_config(page_title="Lead Validation System", layout="wide")

def main():
    st.title("Lead Validation System")

    # Sidebar Configuration
    st.sidebar.header("Configuration")
    if not Config.GOOGLE_PLACES_API_KEY:
        st.sidebar.warning("⚠️ Google Maps API Key Missing")
    if not Config.YELP_API_KEY:
        st.sidebar.warning("⚠️ Yelp API Key Missing")

    mode = st.sidebar.radio("Select Mode", ["Single Lead Validation", "Batch CSV Processing"])

    if mode == "Single Lead Validation":
        render_single_mode()
    else:
        render_batch_mode()

def render_single_mode():
    st.header("Validate Single Lead")

    # Initialize Session State for result persistence
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None

    col_input, col_result = st.columns([1, 1], gap="large")

    # --- Left Column: Input Form ---
    with col_input:
        st.subheader("Lead Information")
        with st.form("lead_form"):
            business_name = st.text_input("Business Name")
            phone = st.text_input("Phone Number")
            zip_code = st.text_input("Zip Code")
            email = st.text_input("Email")

            submitted = st.form_submit_button("Validate Lead", use_container_width=True)

            if submitted:
                if not business_name or not phone:
                    st.error("Business Name and Phone are required.")
                else:
                    lead = Lead(business_name, phone, zip_code, email)
                    with st.spinner("Validating lead against Google & Yelp..."):
                        # Save result to session state
                        st.session_state.validation_result = LeadScorer.enrich_and_score(lead)

    # --- Right Column: Result Card ---
    with col_result:
        result = st.session_state.validation_result
        if result:
            st.subheader("Validation Result")

            # Card-like container
            with st.container(border=True):
                # Score and Tier
                col_metric, col_tier = st.columns([1, 2])
                with col_metric:
                    st.metric("Score", f"{result.score}/100")
                with col_tier:
                    if result.quality_tier == "High":
                        st.success("High Quality Lead")
                    elif result.quality_tier == "Medium":
                        st.warning("Medium Quality Lead")
                    else:
                        st.error("Low Quality Lead")

                st.divider()

                # Verified Details
                if result.verified_business_name:
                    st.write(f"✅ **Verified Identity:** {result.verified_business_name}")
                else:
                    st.write("❌ **Identity Not Verified**")

                if result.website:
                    st.write(f"🔗 **Website Found:** [{result.website}]({result.website})")

                st.divider()

                # Match Reasons
                st.write("**Match Reasons:**")
                for reason in result.match_reasons:
                    st.caption(f"• {reason}")

                # Sources
                st.write("**Data Sources:**")
                st.caption(", ".join(result.sources))

                # Raw API responses (expandable)
                with st.expander("Raw validation responses (Google / Yelp)"):
                    if result.raw_google:
                        st.write("**Google Places**")
                        st.json(result.raw_google)
                    else:
                        st.caption("Google: No match returned.")
                    st.divider()
                    if result.raw_yelp:
                        st.write("**Yelp**")
                        st.json(result.raw_yelp)
                    else:
                        st.caption("Yelp: No match returned.")
        else:
            # Placeholder State
            st.info("Enter lead details and click Validate to see results here.")

def render_batch_mode():
    st.header("Batch CSV Processing")
    st.write("Upload a CSV with columns: `business_name`, `phone`, `zip_code`, `email`. "
             "Large files are split into shards of **1,000 rows**; results are saved after each shard so you can stop anytime and keep partial results.")

    uploaded_file = st.file_uploader("Choose a CSV file to process", type="csv")
    required_cols = {"business_name", "phone", "zip_code", "email"}

    with st.expander("Load previous batch output to view results"):
        loaded_file = st.file_uploader("Upload a batch output CSV", type="csv", key="load_batch_output")
        if loaded_file is not None:
            try:
                loaded_df = pd.read_csv(loaded_file)
                st.session_state.batch_result_df = loaded_df
                st.session_state.batch_output_path = None
                st.session_state.batch_failed_log_path = None
                st.success(f"Loaded {len(loaded_df)} rows. Results shown below.")
            except Exception as e:
                st.error(f"Could not load file: {e}")

        # List recent batch output files from disk (recover past batches)
        if os.path.isdir(BATCH_OUTPUT_DIR):
            batch_files = [
                f for f in os.listdir(BATCH_OUTPUT_DIR)
                if f.endswith(".csv") and not f.startswith("failed_rows_")
            ]
            if batch_files:
                batch_files_with_mtime = [
                    (f, os.path.getmtime(os.path.join(BATCH_OUTPUT_DIR, f)))
                    for f in batch_files
                ]
                batch_files_with_mtime.sort(key=lambda x: x[1], reverse=True)
                recent = batch_files_with_mtime[:10]
                path_to_label = {}
                for fname, _ in recent:
                    path = os.path.join(BATCH_OUTPUT_DIR, fname)
                    try:
                        n = sum(1 for _ in open(path, encoding="utf-8")) - 1
                    except Exception:
                        n = "?"
                    path_to_label[path] = f"{fname} ({n} rows)"
                if path_to_label:
                    st.caption("Or load a recent batch from disk:")
                    paths = list(path_to_label.keys())
                    selected = st.selectbox(
                        "Recent batch files",
                        options=paths,
                        format_func=lambda p: path_to_label.get(p, p),
                        key="recent_batch_select",
                    )
                    if st.button("Load selected file", key="load_recent_batch"):
                        try:
                            df_loaded = pd.read_csv(selected)
                            st.session_state.batch_result_df = df_loaded
                            st.session_state.batch_output_path = selected
                            # Derive failed rows path: output_TS_name.csv -> failed_rows_TS_name.csv
                            sel_basename = os.path.basename(selected)
                            if sel_basename.startswith("output_"):
                                failed_basename = "failed_rows_" + sel_basename[7:]
                            else:
                                failed_basename = sel_basename.replace(".csv", "") + "_failed_rows.csv"
                            failed_path_derived = os.path.join(os.path.dirname(selected), failed_basename)
                            st.session_state.batch_failed_log_path = failed_path_derived if os.path.isfile(failed_path_derived) else None
                            st.success(f"Loaded {len(df_loaded)} rows from {os.path.basename(selected)}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not load file: {e}")

    if uploaded_file is not None:
        start_index = st.number_input(
            "Start from row index (0-based)",
            min_value=0,
            value=0,
            step=BATCH_SHARD_SIZE,
            help="Process from this row onward. E.g. 1000 = skip first 1000 rows (start at batch 2). Use 0 to process from the beginning.",
            key="batch_start_index",
        )

        if st.button("Process Batch"):
            progress_bar = st.progress(0)
            progress_status = st.empty()
            result_placeholder = st.empty()
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, dtype=str)
                df.columns = df.columns.str.lower().str.strip()
                if not required_cols.issubset(df.columns):
                    missing = required_cols - set(df.columns)
                    st.error(f"Missing required columns: {missing}")
                    st.stop()
                total_rows = len(df)
                start_index_val = min(max(0, start_index), total_rows)
                rows_to_process = total_rows - start_index_val
                if rows_to_process <= 0:
                    st.error("No rows to process (start index >= total rows).")
                    st.stop()
                shard_starts = list(range(start_index_val, total_rows, BATCH_SHARD_SIZE))
                num_shards = len(shard_starts)
                os.makedirs(BATCH_OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                input_basename = os.path.basename(uploaded_file.name or "batch.csv")
                output_path = os.path.join(BATCH_OUTPUT_DIR, f"output_{timestamp}_{input_basename}")
                failed_log_path = os.path.join(BATCH_OUTPUT_DIR, f"failed_rows_{timestamp}_{input_basename}")
                all_results = []
                with open(failed_log_path, "w", encoding="utf-8") as failed_log_file:
                    failed_log_file.write("row_index,api_errors\n")
                    for shard_i, shard_start in enumerate(shard_starts):
                        shard_end = min(shard_start + BATCH_SHARD_SIZE, total_rows)
                        shard_df = df.iloc[shard_start:shard_end]
                        buf = BytesIO(shard_df.to_csv(index=False).encode("utf-8"))

                        def make_progress_cb(base, shard_index, n_shards, total_to_process):
                            def cb(done: int, total: int) -> None:
                                global_done = base + done
                                if total_to_process > 0:
                                    progress_bar.progress((global_done - start_index_val) / total_to_process)
                                progress_status.caption(
                                    f"Shard **{shard_index + 1} / {n_shards}** — **{global_done - start_index_val} / {total_to_process}** rows (from row {start_index_val})"
                                )
                            return cb

                        def make_failed_cb(flog):
                            def cb(row_index_0based: int, errors: list) -> None:
                                row_1based = row_index_0based + 1
                                flog.write(f"{row_1based},\"{','.join(errors)}\"\n")
                                flog.flush()
                            return cb

                        with st.spinner(f"Processing shard {shard_i + 1}/{num_shards}..."):
                            result_df = BatchProcessor.process_csv(
                                buf,
                                progress_callback=make_progress_cb(shard_start, shard_i, num_shards, rows_to_process),
                                failed_rows_callback=make_failed_cb(failed_log_file),
                            )
                        all_results.append(result_df)
                        if shard_i == 0 and start_index_val > 0:
                            # Prepend skipped rows so output has same row count and order as input
                            skipped_df = df.iloc[0:start_index_val].copy()
                            for col in result_df.columns:
                                if col not in skipped_df.columns:
                                    skipped_df[col] = ""
                            skipped_df = skipped_df[result_df.columns]
                            full_df = pd.concat([skipped_df, result_df], ignore_index=True)
                            full_df.to_csv(output_path, mode="w", header=True, index=False)
                        elif shard_i == 0:
                            result_df.to_csv(output_path, mode="w", header=True, index=False)
                        else:
                            result_df.to_csv(output_path, mode="a", header=False, index=False)
                        if start_index_val > 0 and shard_i == 0:
                            st.session_state.batch_result_df = pd.concat([skipped_df, result_df], ignore_index=True)
                        elif start_index_val > 0:
                            st.session_state.batch_result_df = pd.concat([
                                st.session_state.batch_result_df,
                                result_df,
                            ], ignore_index=True)
                        else:
                            st.session_state.batch_result_df = pd.concat(all_results, ignore_index=True)
                        st.session_state.batch_output_path = output_path
                        st.session_state.batch_failed_log_path = failed_log_path
                        with result_placeholder.container():
                            st.dataframe(st.session_state.batch_result_df)
                            st.caption(f"Results saved to `{output_path}` (partial results persist if you stop)")
                            st.caption("⚠️ **Note:** Clicking Download will rerun the app and *stop* the batch. Partial results are already in the file above.")
                            csv_bytes = st.session_state.batch_result_df.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                "Download current results",
                                csv_bytes,
                                f"output_{timestamp}_{input_basename}",
                                "text/csv",
                                key=f"download-batch-partial-{shard_i}",
                            )

                progress_bar.progress(1.0)
                progress_status.caption(f"Done: **{rows_to_process}** rows processed (from row {start_index_val} to {total_rows - 1}).")
                result_placeholder.empty()
                st.success(f"Processing complete! Results saved to `{output_path}`. Failed rows (e.g. 400/429) logged to `{failed_log_path}`.")
            except Exception as e:
                st.error(f"Error processing CSV: {e}")

        # Show last batch results (persists after run or after stop)
        if st.session_state.get("batch_result_df") is not None:
            st.divider()
            st.subheader("Batch results")
            st.dataframe(st.session_state["batch_result_df"])
            path = st.session_state.get("batch_output_path")
            failed_path = st.session_state.get("batch_failed_log_path")
            if path:
                st.caption(f"Output file: `{path}`")
            if failed_path and os.path.isfile(failed_path):
                st.caption(f"Failed rows log (400/429/errors): `{failed_path}`")
            csv_bytes = st.session_state["batch_result_df"].to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Verified Results",
                csv_bytes,
                "verified_leads.csv",
                "text/csv",
                key="download-csv",
            )

if __name__ == "__main__":
    main()
