import os
import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote

# ——————————————————————————————————————————
# Streamlit App: Miro Integration with n8n Trigger
# ——————————————————————————————————————————
st.set_page_config(page_title="Miro Integration", layout="centered")
st.title("Miro Integration")

# ——————————————————————————————————————————
# 1) Input: Miro Board ID
# ——————————————————————————————————————————
board_id = st.text_input(
    "Enter your Miro Board ID",
    placeholder="e.g. uXjVI56ioZA=",
    help="The ID part after /boards/ in your Miro board URL"
)
if not board_id:
    st.info("🔗 Please enter your Miro Board ID above to enable file upload.")
    st.stop()

# ——————————————————————————————————————————
# 2) File Uploader for Excel
# ——————————————————————————————————————————
uploaded_file = st.file_uploader(
    "Upload an Excel (.xlsx) file", type=["xlsx"],
    help="This file will be sent to n8n for processing"
)
if not uploaded_file:
    st.stop()

# ——————————————————————————————————————————
# 3) Preview the Uploaded Sheet
# ——————————————————————————————————————————
try:
    df = pd.read_excel(uploaded_file)
    st.success("✅ File read successfully!")
    st.write("### Preview of uploaded data:")
    st.dataframe(df)
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

# ——————————————————————————————————————————
# 4) Build the n8n Webhook URL and Miro Bulk-Create URL
# ——————————————————————————————————————————
# n8n webhook endpoint (set via environment or hard-code for testing)
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://dtcmode.app.n8n.cloud/webhook-test/79fd5d26-8db1-49e3-a838-52376ae35931"
)
st.write(f"▶️ Posting file + board_id to n8n webhook: `{N8N_WEBHOOK_URL}`")

# Encode board_id for URL safety
encoded_board_id = quote(board_id, safe='')
miro_url = f"https://api.miro.com/v2/boards/{encoded_board_id}/items/bulk"
st.write(f"▶️ Miro Bulk-Create API URL: `{miro_url}`")

# ——————————————————————————————————————————
# 5) Send the File + board_id + miro_url to n8n
# ——————————————————————————————————————————
with st.spinner("Triggering workflow in n8n..."):
    files = {
        'data': (
            uploaded_file.name,
            uploaded_file.getvalue(),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    }
    data = {
        'board_id': board_id,
        'miro_url': miro_url
    }
    try:
        resp = requests.post(N8N_WEBHOOK_URL, files=files, data=data, timeout=30)
        if resp.ok:
            st.success("🎉 Workflow triggered successfully!")
        else:
            st.error(f"❌ n8n webhook returned {resp.status_code}: {resp.text}")
    except Exception as err:
        st.error(f"❌ Error sending to n8n: {err}")
