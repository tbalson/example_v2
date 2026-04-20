import streamlit as st
import requests
import os
from openai import OpenAI

API_URL = os.getenv("API_URL", "http://localhost:5000")
# Initializes using the OPENAI_API_KEY from your .env file
client = OpenAI()

st.set_page_config(page_title="ECT Anonymization & AI Portal", layout="centered")
st.title("🛡️ Secure Data Pipeline & AI")

st.write("Upload a batch of datasets to automatically redact PII. Once clean, you can query the data using AI.")

# Initialize session state to hold our clean batch data
if 'clean_data' not in st.session_state:
    st.session_state['clean_data'] = None

# 1. Enable multiple file uploads
uploaded_files = st.file_uploader(
    "Choose files", 
    type=['csv', 'xlsx', 'xls', 'pdf', 'db', 'sqlite', 'txt'], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Anonymize Batch"):
        with st.spinner(f"Analyzing and redacting PII for {len(uploaded_files)} file(s)..."):
            try:
                # 2. Prepare the multipart/form-data payload for multiple files
                # We map every file to the 'files' key so Connexion receives an array
                files_payload = [
                    ('files', (file.name, file.getvalue(), file.type)) 
                    for file in uploaded_files
                ]
                
                response = requests.post(f"{API_URL}/api/anonymize", files=files_payload)
                response.raise_for_status()
                
                data = response.json()
                st.success(f"Anonymization Complete! Processed {data.get('processed_count', 0)} file(s).")
                
                # Store the array of results in session state
                st.session_state['clean_data'] = data.get("batch_results", [])
                
            except requests.exceptions.HTTPError as err:
                try:
                    error_message = response.json().get('error', str(err))
                except ValueError:
                    error_message = f"Server Error ({response.status_code})"
                st.error(f"API Error: {error_message}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# 3. Display the processed files iteratively
if st.session_state['clean_data']:
    st.divider()
    st.subheader("Anonymized Data Preview")
    
    for item in st.session_state['clean_data']:
        st.markdown(f"**Filename:** `{item['filename']}`")
        if item['data_type'] == "dataframe":
            st.dataframe(item['results'])
        else:
            st.text_area(f"Output for {item['filename']}", item['results'], height=150)
        st.write("---")

# --- LLM CHAT INTERFACE ---
# Only show this if we have clean data sitting in memory
if st.session_state['clean_data'] is not None:
    st.subheader("💬 Query Anonymized Data Batch")
    
    user_prompt = st.text_input("Ask a question about this data batch:")
    
    if st.button("Ask LLM") and user_prompt:
        with st.spinner("Generating insights..."):
            try:
                # Convert the entire batch array into a string format the LLM can read
                context_string = str(st.session_state['clean_data'])
                
                # Build the prompt
                system_message = "You are an environmental data analyst. Use the provided anonymized data context to answer the user's question. Do not make up facts outside the provided data."
                
                # Call OpenAI
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo", 
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Context Data Batch: {context_string}\n\nQuestion: {user_prompt}"}
                    ]
                )
                
                # Display the answer
                st.info(completion.choices[0].message.content)
                
            except Exception as e:
                st.error(f"LLM Error: {str(e)}")
