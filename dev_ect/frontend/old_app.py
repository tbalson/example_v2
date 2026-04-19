import streamlit as st
import requests
import os

# Fetch the API URL from the Docker environment, or default to localhost if testing outside Docker
API_URL = os.getenv("API_URL", "http://localhost:5000")

st.set_page_config(page_title="Streamlit + Flask", layout="centered")
st.title("🚀 Two-Container App")

st.write("Click the button to ping the Flask REST API.")

if st.button("Ping API"):
    with st.spinner("Connecting to Flask..."):
        try:
            # Send a GET request to the Flask container
            response = requests.get(f"{API_URL}/api/hello")
            response.raise_for_status()
            
            data = response.json()
            st.success(f"Success! The API responded with: **{data['message']}**")
            
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to the API: {e}")
