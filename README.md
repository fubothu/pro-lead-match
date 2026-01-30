# Pro Lead Match (Lead Quality System)

A robust tool to validate and verify professional leads (Contractors, Designers, etc.) using Google Maps, Yelp, and intelligent scoring logic.

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.

### 1. Prerequisites
*   **Python 3.9+** installed on your machine.
*   **Git** installed.

### 2. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/fubothu/pro-lead-match.git
cd pro-lead-match
```

### 3. Install Dependencies
It is best practice to use a virtual environment:
```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Mac/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install libraries
pip install -r requirements.txt
```

### 4. Setup API Keys (Crucial Step)
The system needs API keys to work (Google Maps & Yelp).

1.  **Rename the example config**:
    ```bash
    mv .env.example .env
    ```
2.  **Open `.env`** in a text editor.
3.  **Fill in your Keys**:
    *   See the detailed **[API Setup Guide](api_setup_guide.md)** included in this repo for step-by-step instructions on how to get free keys.
    *   *Note*: The system works best with at least `GOOGLE_PLACES_API_KEY` and `YELP_API_KEY`.

### 5. Run the App
Launch the Verified Lead Dashboard:
```bash
streamlit run lead_quality_system/app.py
```
*   The app should automatically open in your browser at `http://localhost:8501`.

### 6. Tools included
*   **Dashboard**: Upload CSVs for batch processing.
*   **Benchmark**: Run `python benchmark.py` to test system accuracy against a golden dataset.
