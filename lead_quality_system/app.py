import streamlit as st
import pandas as pd
from lead_quality_system.models import Lead
from lead_quality_system.scorer import LeadScorer
from lead_quality_system.services.csv_processor import BatchProcessor
from lead_quality_system.config import Config

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
        else:
            # Placeholder State
            st.info("Enter lead details and click Validate to see results here.")

def render_batch_mode():
    st.header("Batch CSV Processing")
    st.write("Upload a CSV with columns: `business_name`, `phone`, `zip_code`, `email`")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        if st.button("Process Batch"):
            with st.spinner("Processing leads in parallel..."):
                try:
                    result_df = BatchProcessor.process_csv(uploaded_file)
                    st.success("Processing Complete!")
                    
                    st.dataframe(result_df)
                    
                    # CSV Download
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Verified Results",
                        csv,
                        "verified_leads.csv",
                        "text/csv",
                        key='download-csv'
                    )
                    
                except Exception as e:
                    st.error(f"Error processing CSV: {e}")

if __name__ == "__main__":
    main()
