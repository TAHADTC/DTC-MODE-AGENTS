import streamlit as st
from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import io
import pandas as pd
import requests
from docx import Document
from PyPDF2 import PdfReader

# -----------------------------
# App Configuration & CSS
# -----------------------------
st.set_page_config(
    page_title="DTCMODE BOT-ASSISTANT",
    page_icon="🤖",
    layout="wide"
)
st.markdown("""
<style>
    .main { background: #f8f9fa; padding: 1rem; }
    .stButton>button { width:100%; margin:0.5rem 0; padding:0.75rem;
        font-size:1rem; background:#2563eb; color:#fff; border-radius:8px; border:none; }
    .sidebar-header { text-align:center; color:#fff; font-size:1.25rem; padding:1rem 0; background:#2c2c2e; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Session State Initialization
# -----------------------------
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Agent 2'
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
for key, default in {
    'messages': [],
    'document_texts': [],
    'brand_summary': '',
    'approved': False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -----------------------------
# Webhook URLs
# -----------------------------
N8N_WEBHOOK_URL   = os.getenv('N8N_WEBHOOK_URL')
ICP_URL          = os.getenv('ICP_WEBHOOK_URL')
AGENT2_INIT_URL  = os.getenv('AGENT2_WEBHOOK_URL')
AGENT2_CHAT_URL  = os.getenv('AGENT2_CHATBOT_URL')
CONTENT_FUNNEL_WEBHOOK_URL = os.getenv('CONTENT_FUNNEL_WEBHOOK_URL')
CONVERSION_PATHWAY_WEBHOOK_URL = os.getenv('CONVERSION_PATHWAY_WEBHOOK_URL')
RETENTION_AFFINITY_WEBHOOK_URL = os.getenv('RETENTION_AFFINITY_WEBHOOK_URL')
STRATEGY_WEBHOOK_URL = os.getenv('STRATEGY_WEBHOOK_URL')
MASTER_WEBHOOK_URL = os.getenv('MASTER_WEBHOOK_URL')

# -----------------------------
# Sidebar Navigation
# -----------------------------
st.sidebar.markdown('<div class="sidebar-header">🤖 DTCMODE BOT-ASSISTANT</div>', unsafe_allow_html=True)
for tab in ['Miro Sticky Notes', "ICP's", 'Agent 2', 'Content Funnel Section', 'Conversion Pathway Strategy Framework', 'Retention + Affinity Generator', 'Strategy', 'Master']:
    if st.sidebar.button(tab):
        st.session_state.active_tab = tab

# -----------------------------
# Miro Sticky Notes Automation
# -----------------------------
def miro_mode():
    st.header("Miro Sticky Notes Automation")

    # 1) Input for Miro Board ID
    board_id = st.text_input(
        "Enter your Miro Board ID",
        placeholder="e.g. uXjVI56ioZA",
        help="The ID part after /boards/ in your Miro board URL"
    )
    if not board_id:
        st.info("🔗 Please enter your Miro Board ID above to enable file upload.")
        st.stop()

    # 2) File Uploader for Excel
    uploaded_file = st.file_uploader(
        "Upload an Excel (.xlsx) file", type=["xlsx"],
        help="This file will be sent to n8n for processing"
    )
    if not uploaded_file:
        st.stop()

    # 3) Preview the Uploaded Sheet
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ File read successfully!")
        st.write("### Preview of uploaded data:")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

    # 4) Build the n8n Webhook URL and Miro Bulk-Create URL
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
    if not N8N_WEBHOOK_URL:
        st.error("❌ Missing N8N_WEBHOOK_URL in the environment variables.")
        st.stop()

    st.write(f"▶️ Posting file + board_id to n8n webhook: `{N8N_WEBHOOK_URL}`")

    # Encode board_id for URL safety
    from urllib.parse import quote
    encoded_board_id = quote(board_id, safe='')
    miro_url = f"https://api.miro.com/v2/boards/{encoded_board_id}/items/bulk"
    st.write(f"▶️ Miro Bulk-Create API URL: `{miro_url}`")

    # 5) Send the File + board_id + miro_url to n8n
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

# -----------------------------
# ICP's Automation
# -----------------------------
def icp_mode():
    st.header("Ideal Customer Profiles")

    # Email input field
    email = st.text_input('Enter your email address', placeholder='e.g., user@example.com')

    # File uploader for multiple PDFs and TXT files
    uploads = st.file_uploader(
        'Upload files (Multiple PDFs and up to 3 TXT files allowed)', 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )

    if uploads:
        # Validate file types and count
        pdf_files = [f for f in uploads if f.type == 'application/pdf']
        txt_files = [f for f in uploads if f.type == 'text/plain']

        # Display validation messages
        st.write(f"📄 PDF files uploaded: {len(pdf_files)}")
        st.write(f"📝 TXT files uploaded: {len(txt_files)}")

        if len(txt_files) > 3:
            st.warning('⚠️ Please upload no more than 3 TXT files.')
            return

        # Check total size limit (10 MB)
        total_size = sum(f.size for f in uploads)
        if total_size > 10 * 1024 * 1024:
            st.error("The total size of uploaded files exceeds the 10 MB limit.")
            return

        # Button to send files to webhook
        if st.button('Process Files'):
            if not email.strip():
                st.warning('Please enter your email address.')
                return

            with st.spinner("Processing files..."):
                try:
                    # Prepare the file payload
                    files_payload = []
                    for f in uploads:
                        data = f.read()
                        file_type = 'application/pdf' if f.type == 'application/pdf' else 'text/plain'
                        files_payload.append(('files', (f.name, data, file_type)))

                    # Prepare additional data
                    data = {
                        'email': email
                    }

                    # Send the files to the webhook
                    resp = requests.post(ICP_URL, files=files_payload, data=data, timeout=30)

                    # Handle the response
                    if resp.ok:
                        st.success("🎉 Files processed successfully!")
                    else:
                        st.error(f"❌ Error: {resp.status_code} - {resp.text}")
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

# -----------------------------
# Agent 2: File Upload & Chat Assistant
# -----------------------------
def agent2_mode():
    st.header('Agent 2 – File Upload & Chat Assistant')

    # Store email in session state if not already present
    if 'agent2_email' not in st.session_state:
        st.session_state.agent2_email = ''

    # Email input field - persist the value in session state
    email = st.text_input('Email', value=st.session_state.agent2_email)
    if email != st.session_state.agent2_email:
        st.session_state.agent2_email = email

    # --- File Upload & Initial Summary ---
    if not st.session_state.brand_summary:
        with st.form('upload_form', clear_on_submit=True):
            uploads = st.file_uploader(
                'Upload files(BRAND DOCUMENT AS PDF AND MEETING NOTES AS TXT)', 
                type=['pdf','txt'],
                accept_multiple_files=True
            )
            submitted = st.form_submit_button('Get Initial Summary')

        if submitted:
            if not uploads or not st.session_state.agent2_email.strip():
                st.warning('Please upload files and enter email')
            else:
                docs, files_payload = [], []
                for f in uploads:
                    data = f.read()
                    if f.type == 'application/pdf':
                        txt = '\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(data)).pages)
                    elif 'wordprocessingml.document' in f.type:
                        doc = Document(io.BytesIO(data))
                        txt = '\n'.join(p.text for p in doc.paragraphs)
                    elif 'spreadsheetml.sheet' in f.type:
                        df = pd.read_excel(io.BytesIO(data))
                        txt = df.to_csv(index=False)
                    else:
                        txt = data.decode(errors='ignore')
                    docs.append(txt)
                    files_payload.append(('files', (f.name, data, f.type)))

                st.session_state.document_texts = docs

                # Call initial-summary webhook with email
                resp = requests.post(
                    AGENT2_INIT_URL,
                    files=files_payload,
                    data={'email': st.session_state.agent2_email},
                    timeout=60
                )
                resp.raise_for_status()
                result_json = resp.json()
                payload = result_json[0] if isinstance(result_json, list) else result_json
                summary = payload.get('summary') or payload.get('assistant') or payload.get('textContent','')
                summary = summary.strip()

                # Store and display
                st.session_state.brand_summary = summary
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': summary,
                    'email': st.session_state.agent2_email  # Include email in message
                })
                st.success('Initial summary generated!')

    # --- Display Initial Summary ---
    if st.session_state.brand_summary:
        st.subheader('Initial Generated Summary')
        st.write(st.session_state.brand_summary)

    # --- Chat Interface ---
    st.markdown('---')
    st.subheader('Chat')
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # --- Chat Input & Response ---
    if st.session_state.brand_summary and not st.session_state.approved:
        user_input = st.chat_input('Your instruction...')
        if user_input:
            # 1) Show user message
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input,
                'email': st.session_state.agent2_email  # Include email in message
            })
            with st.chat_message('user'):
                st.markdown(user_input)

            # 2) Send to chatbot, including the latest summary and email
            payload = {
                'session_id': st.session_state.session_id,
                'documents': st.session_state.document_texts,
                'generated_summary': st.session_state.brand_summary,
                'instruction': user_input,
                'email': st.session_state.agent2_email
            }
            
            try:
                with st.spinner("Waiting for response from the assistant..."):
                    # Increased timeout to 180 seconds
                    resp = requests.post(AGENT2_CHAT_URL, json=payload, timeout=180)
                    
                    if not resp.ok:
                        st.error(f"Server returned error {resp.status_code}: {resp.text}")
                        return
                    
                    # Check content type of response
                    content_type = resp.headers.get('content-type', '')
                    
                    if 'application/pdf' in content_type:
                        # Handle PDF response
                        st.success("✅ Document generated successfully!")
                        
                        # Create download button for PDF
                        st.download_button(
                            label="Download PDF",
                            data=resp.content,
                            file_name=f"generated_document_{st.session_state.session_id}.pdf",
                            mime="application/pdf"
                        )
                        
                        # Set approved state
                        st.session_state.approved = True
                        return
                        
                    # Handle JSON/text responses as before
                    try:
                        data = resp.json()
                        data = data[0] if isinstance(data, list) else data
                        # Ensure email is preserved in the response data
                        if 'email' not in data:
                            data['email'] = st.session_state.agent2_email
                    except requests.exceptions.JSONDecodeError:
                        # If response is not JSON, create a data dict with the text response
                        data = {
                            'assistant': resp.text,
                            'generated_summary': resp.text,
                            'approved': True,
                            'email': st.session_state.agent2_email
                        }
                    
            except requests.exceptions.ReadTimeout:
                st.error("""
                Request timed out after 180 seconds. This could be because:
                1. The server is taking too long to process
                2. There might be an issue with the webhook response configuration
                
                Please check your n8n workflow configuration:
                - Ensure both webhook response nodes are properly configured
                - Make sure each path (true/false) properly ends the request
                - Consider optimizing any heavy processing
                """)
                return
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the server: {str(e)}")
                return

            # Only process text/JSON responses
            if not st.session_state.approved:
                # Extract and render assistant reply
                reply = data.get('assistant') or data.get('generated_summary') or data.get('textContent','')
                reply = reply.strip()
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': reply,
                    'email': data.get('email', st.session_state.agent2_email)
                })
                with st.chat_message('assistant'):
                    st.markdown(reply)

                # Update brand_summary for the next turn
                st.session_state.brand_summary = data.get('generated_summary', reply)

                # Check for approval flag
                if data.get('approved'):
                    st.session_state.approved = True

    # --- Final Summary on approval ---
    elif st.session_state.approved:
        st.success('✅ Conversation approved!')
        st.markdown(f"""### Final Summary
{st.session_state.brand_summary}""")

# -----------------------------
# Content Funnel Section
# -----------------------------
def content_funnel_mode():
    st.header("Content Funnel Section")

    # Email input field
    email = st.text_input('Enter your email address', placeholder='e.g., user@example.com')

    # File uploader for PDF and TXT documents
    uploads = st.file_uploader(
        'Upload files (PDF and TXT only)', 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )

    # Button to send the files to the n8n webhook
    if st.button('Send to n8n Webhook'):
        if not uploads or not email.strip():
            st.warning('Please upload files and enter a valid email address.')
            return

        # Check total size limit (e.g., 10 MB)
        total_size = sum(f.size for f in uploads)
        if total_size > 10 * 1024 * 1024:  # Example: 10 MB limit
            st.error("The total size of uploaded files exceeds the 10 MB limit.")
            return

        with st.spinner("Sending files to n8n webhook..."):
            try:
                # Prepare the file payload
                files_payload = []
                for f in uploads:
                    data = f.read()
                    file_type = 'application/pdf' if f.name.endswith('.pdf') else 'text/plain'
                    files_payload.append(('files', (f.name, data, file_type)))

                # Prepare additional data
                data = {
                    'email': email  # Include the email in the payload
                }

                # Send the files to the n8n webhook
                resp = requests.post(CONTENT_FUNNEL_WEBHOOK_URL, files=files_payload, data=data, timeout=30)

                # Handle the response
                if resp.ok:
                    st.success("🎉 Files sent to n8n webhook successfully!")
                else:
                    st.error(f"❌ n8n webhook returned {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error sending files to n8n webhook: {e}")

# -----------------------------
# Conversion Pathway Strategy Framework
# -----------------------------
def conversion_pathway_mode():
    st.header("Conversion Pathway Strategy Framework")

    # Email input field
    email = st.text_input('Enter your email address', placeholder='e.g., user@example.com')

    # File uploader for PDF and TXT documents
    uploads = st.file_uploader(
        'Upload files (PDF and TXT only)', 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )

    # Button to send the files to the n8n webhook
    if st.button('Send to n8n Webhook'):
        if not uploads or not email.strip():
            st.warning('Please upload files and enter a valid email address.')
            return

        # Check total size limit (e.g., 10 MB)
        total_size = sum(f.size for f in uploads)
        if total_size > 10 * 1024 * 1024:  # Example: 10 MB limit
            st.error("The total size of uploaded files exceeds the 10 MB limit.")
            return

        with st.spinner("Sending files to n8n webhook..."):
            try:
                # Prepare the file payload
                files_payload = []
                for f in uploads:
                    data = f.read()
                    file_type = 'application/pdf' if f.name.endswith('.pdf') else 'text/plain'
                    files_payload.append(('files', (f.name, data, file_type)))

                # Prepare additional data
                data = {
                    'email': email  # Include the email in the payload
                }

                # Send the files to the n8n webhook
                resp = requests.post(CONVERSION_PATHWAY_WEBHOOK_URL, files=files_payload, data=data, timeout=30)

                # Handle the response
                if resp.ok:
                    st.success("🎉 Files sent to n8n webhook successfully!")
                else:
                    st.error(f"❌ n8n webhook returned {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error sending files to n8n webhook: {e}")

# -----------------------------
# Retention + Affinity Generator
# -----------------------------
def retention_affinity_mode():
    st.header("Retention + Affinity Generator")

    # Email input field
    email = st.text_input('Enter your email address', placeholder='e.g., user@example.com')

    # File uploader for PDF and TXT documents
    uploads = st.file_uploader(
        'Upload files (PDF and TXT only)', 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )

    # Button to send the files to the n8n webhook
    if st.button('Send to n8n Webhook'):
        if not uploads or not email.strip():
            st.warning('Please upload files and enter a valid email address.')
            return

        # Check total size limit (e.g., 10 MB)
        total_size = sum(f.size for f in uploads)
        if total_size > 10 * 1024 * 1024:  # Example: 10 MB limit
            st.error("The total size of uploaded files exceeds the 10 MB limit.")
            return

        with st.spinner("Sending files to n8n webhook..."):
            try:
                # Prepare the file payload
                files_payload = []
                for f in uploads:
                    data = f.read()
                    file_type = 'application/pdf' if f.name.endswith('.pdf') else 'text/plain'
                    files_payload.append(('files', (f.name, data, file_type)))

                # Prepare additional data
                data = {
                    'email': email  # Include the email in the payload
                }

                # Send the files to the n8n webhook
                resp = requests.post(RETENTION_AFFINITY_WEBHOOK_URL, files=files_payload, data=data, timeout=30)

                # Handle the response
                if resp.ok:
                    st.success("🎉 Files sent to n8n webhook successfully!")
                else:
                    st.error(f"❌ n8n webhook returned {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error sending files to n8n webhook: {e}")

# -----------------------------
# Strategy Page
# -----------------------------
def strategy_mode():
    st.header("Strategy")

    # Email input field
    email = st.text_input('Enter your email address', placeholder='e.g., user@example.com')

    # File uploader for PDF and TXT documents
    uploads = st.file_uploader(
        'Upload files (PDF and TXT only)', 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )

    # Button to send the files to the n8n webhook
    if st.button('Send to n8n Webhook'):
        if not uploads or not email.strip():
            st.warning('Please upload files and enter a valid email address.')
            return

        # Check total size limit (e.g., 10 MB)
        total_size = sum(f.size for f in uploads)
        if total_size > 10 * 1024 * 1024:  # Example: 10 MB limit
            st.error("The total size of uploaded files exceeds the 10 MB limit.")
            return

        with st.spinner("Sending files to n8n webhook..."):
            try:
                # Prepare the file payload
                files_payload = []
                for f in uploads:
                    data = f.read()
                    file_type = 'application/pdf' if f.name.endswith('.pdf') else 'text/plain'
                    files_payload.append(('files', (f.name, data, file_type)))

                # Prepare additional data
                data = {
                    'email': email  # Include the email in the payload
                }

                # Send the files to the n8n webhook
                resp = requests.post(STRATEGY_WEBHOOK_URL, files=files_payload, data=data, timeout=30)

                # Handle the response
                if resp.ok:
                    st.success("🎉 Files sent to n8n webhook successfully!")
                else:
                    st.error(f"❌ n8n webhook returned {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error sending files to n8n webhook: {e}")

# -----------------------------
# Master Page
# -----------------------------
def master_mode():
    st.header("Master File Upload")

    # Email input field
    email = st.text_input('Enter your email address', placeholder='e.g., user@example.com')

    # File uploader for PDF and TXT documents
    uploads = st.file_uploader(
        'Upload files (PDF and TXT only)', 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )

    # Button to send the files to the n8n webhook
    if st.button('Send to n8n Webhook'):
        if not uploads or not email.strip():
            st.warning('Please upload files and enter a valid email address.')
            return

        with st.spinner("Sending files to n8n webhook..."):
            try:
                # Prepare the file payload
                files_payload = []
                for f in uploads:
                    data = f.read()
                    file_type = 'application/pdf' if f.name.endswith('.pdf') else 'text/plain'
                    files_payload.append(('files', (f.name, data, file_type)))

                # Prepare additional data
                data = {
                    'email': email  # Include the email in the payload
                }

                # Send the files to the n8n webhook
                resp = requests.post(MASTER_WEBHOOK_URL, files=files_payload, data=data, timeout=30)

                # Handle the response
                if resp.ok:
                    st.success("🎉 Files sent to n8n webhook successfully!")
                else:
                    st.error(f"❌ n8n webhook returned {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error sending files to n8n webhook: {e}")

# -----------------------------
# Main Dispatcher
# -----------------------------
if st.session_state.active_tab == 'Miro Sticky Notes':
    miro_mode()
elif st.session_state.active_tab == "ICP's":
    icp_mode()
elif st.session_state.active_tab == "Content Funnel Section":
    content_funnel_mode()
elif st.session_state.active_tab == "Conversion Pathway Strategy Framework":
    conversion_pathway_mode()
elif st.session_state.active_tab == "Retention + Affinity Generator":
    retention_affinity_mode()
elif st.session_state.active_tab == "Strategy":
    strategy_mode()
elif st.session_state.active_tab == "Master":
    master_mode()
else:
    agent2_mode()
