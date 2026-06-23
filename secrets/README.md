# 🔑 Google Service Account Credentials

Place your downloaded service account JSON file here as:

```
secrets/service_account.json
```

## How to get this file

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **IAM & Admin → Service Accounts**
4. Click your service account → **Keys** tab → **Add Key → Create new key → JSON**
5. Download the file and rename it to `service_account.json`
6. Place it in this `secrets/` folder

## ⚠️ IMPORTANT

- This file contains private credentials — **NEVER commit it to git**
- It is already listed in `.gitignore`
- For Streamlit Cloud deployment, paste the JSON contents into **Streamlit Secrets** as `[gcp_service_account]`

## Required API Permissions

Make sure the Google Sheets API and Google Drive API are enabled for your project,
and that the service account has **Editor** access to the Google Sheet.

To share the sheet with the service account:
1. Open the Google Sheet
2. Click **Share**
3. Paste the service account email (found in the JSON as `"client_email"`)
4. Grant **Editor** access
