# API Setup & Cost Protection Guide

Follow these steps to generate your API keys and configure cost caps so you can run the Lead Validation System for **$0**.

---

## Part 1: Google Cloud Platform (GCP)

### Step 1: Create a Project
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Click the project dropdown (top left) > **New Project**.
3.  Name it `Lead-Validator` and create it.
4.  **Billing**: You will be asked to link a Billing Account. This is required by Google, but we will set caps below to ensure you aren't charged.

### Step 2: Enable "Places API (New)"
1.  In the search bar at the top, type **"Places API (New)"**.
2.  Select it and click **Enable**.
3.  Once enabled, go to **Credentials** (left sidebar).
4.  Click **Create Credentials** > **API Key**.
5.  **Copy this key**. This is your `GOOGLE_PLACES_API_KEY`.
6.  *(Recommended)* Click on the key name to restrict it. Under "API restrictions", select **"Places API (New)"** so it can't be used for anything else.

### Step 3: Enable "Custom Search API"
1.  In the search bar, type **"Custom Search API"**.
2.  Select it and click **Enable**.
3.  Go to **Credentials**.
4.  Click **Create Credentials** > **API Key**.
5.  **Copy this NEW key**. This is your `GOOGLE_SEARCH_API_KEY`.
6.  Click on the key name to restrict it. Under "API restrictions", select **"Custom Search API"** (and nothing else).
7.  Click **Save**.

### Step 4: Create Search Engine ID (CX)
1.  Go to [Programmable Search Engine Control Panel](https://programmablesearchengine.google.com/controlpanel/all).
2.  Click **Add**.
3.  **Name**: `Global Search`.
4.  **What to search**: Select **"Search specific sites or pages"**.
5.  **Enter**: `www.google.com` (as a placeholder).
6.  Complete the captcha and click **Create**.
7.  **Crucial Workaround (New Interface)**:
    *   Click **Modify your search engine**.
    *   Under **"Search features"** (or sometimes bottom of "Overview"), look for **"Search the entire web"**.
    *   *If allowed*: Turn it **ON**.
    *   *If blocked*: We will use a fallback. Copy the **Search engine ID** anyway.
        *   *Note*: If stuck with site-specific search, we might need to rely more heavily on Google Maps or Yelp for website discovery, as Google has tightened this free feature recently.
8.  **Copy the ID**. This is your `GOOGLE_SEARCH_CX`.

### Step 5: Set Cost Caps (Crucial!)
To ensure you stay within the Free Tier:

**A. Cap Custom Search ($0 Hard Limit)**
1.  Go to [APIs & Services > Dashboard](https://console.cloud.google.com/apis/dashboard).
2.  Click **"Custom Search API"**.
3.  Click the **Quotas** tab.
4.  Find **"Queries per day"**.
5.  Click the **Edit (Pencil)** icon.
6.  Set the limit to **100**.
    *   *Result*: The API stops working after 100 searches/day. You will never pay.

**B. Cap Places API (Budget Control)**
1.  Go to [Google Maps Platform > Quotas](https://console.cloud.google.com/google/maps-apis/quotas).
2.  In the dropdown "All APIs", select **"Places API (New)"**.
3.  You need to cap two specific quotas (look for them in the list):
    *   **`SearchTextRequest per day`** (Used for Name+Zip searches).
    *   **`SearchNearbyRequest per day`** (Used for Phone searches).
4.  Check the box next to both, click **Edit Quotas**, and set them to **500**.
    *   *Result*: 500 * 30 days = 15,000 requests. Since the first ~11,000 are free ($200 credit), this keeps you very close to $0.

---

## Part 2: Yelp Fusion API

### Step 1: Create App
1.  Go to [Yelp for Developers](https://www.yelp.com/developers/v3/manage_app).
2.  Log in (you don't need a Business account, a regular User account works).
3.  Click **Create App**.
    *   **App Name**: `Lead Validator`.
    *   **Industry**: `Technology`.
    *   **Contact Email**: Your email.
4.  Create the app.

### Step 2: Get Key
1.  Once created, you will see an **API Key** at the top of the "Manage App" page.
2.  **Copy this key**. This is your `YELP_API_KEY`.
3.  **Cost**: Authentication is free. The daily limit is usually 5,000 calls, which is plenty. No credit card is required for the free tier.

---

## Part 3: Activate Production Mode

1.  Open your project folder.
2.  Rename `.env.example` to `.env`.
3.  Paste your keys:
    ```ini
    GOOGLE_PLACES_API_KEY=AIzaSyD...
    GOOGLE_SEARCH_API_KEY=AIzaSyD...  (Can be same as above)
    GOOGLE_SEARCH_CX=a1b2c3...
    YELP_API_KEY=abcdef12345...
    MOCK_MODE=false
    ```
4.  Restart your server. You are now validating real leads!
