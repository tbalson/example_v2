import streamlit as st
import requests
import os
from openai import OpenAI

API_URL = os.getenv("API_URL", "http://localhost:5000")
# Make sure to pass this into your docker-compose.yml environment variables later!
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI()

st.set_page_config(page_title="ECT Anonymization & AI Portal", layout="centered")
st.title("🛡️ Secure Data Pipeline & AI")

st.write("Upload a dataset to automatically redact PII. Once clean, you can query the data using AI.")

# Initialize session state to hold our clean data
if 'clean_data' not in st.session_state:
    st.session_state['clean_data'] = None

uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls', 'pdf', 'db', 'sqlite', 'txt'])

if uploaded_file is not None:
    if st.button("Anonymize Data"):
        with st.spinner("Analyzing and redacting PII..."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                response = requests.post(f"{API_URL}/api/anonymize", files=files)
                response.raise_for_status()
                
                data = response.json()
                st.success("Anonymization Complete!")
                
                # Store the clean results in session state so the LLM can use it
                st.session_state['clean_data'] = data["results"]
                st.session_state['data_type'] = data["data_type"]
                
                if st.session_state['data_type'] == "dataframe":
                    st.dataframe(st.session_state['clean_data'])
                else:
                    st.text_area("Anonymized Output", st.session_state['clean_data'], height=300)
                
            except requests.exceptions.HTTPError as err:
                try:
                    error_message = response.json().get('error', str(err))
                except ValueError:
                    error_message = f"Server Error ({response.status_code})"
                st.error(f"API Error: {error_message}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- NEW: LLM CHAT INTERFACE ---
# Only show this if we have clean data sitting in memory
if st.session_state['clean_data'] is not None:
    st.divider()
    st.subheader("💬 Query Anonymized Data")
    
    user_prompt = st.text_input("Ask a question about this data:")
    
    if st.button("Ask LLM") and user_prompt:
        with st.spinner("Generating insights..."):
            try:
                # Convert the clean data into a string format the LLM can read
                context_string = str(st.session_state['clean_data'])
                
                # Build the prompt
                system_message = "You are an environmental data analyst. Use the provided anonymized data context to answer the user's question. Do not make up facts outside the provided data."
                
                # Call OpenAI
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo", # or gpt-4
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Context Data: {context_string}\n\nQuestion: {user_prompt}"}
                    ]
                )
                
                # Display the answer
                st.info(completion.choices[0].message.content)
                
            except Exception as e:
                st.error(f"LLM Error: {str(e)}")
