import streamlit as st
import requests
import os
from openai import OpenAI

# --- New RAG Imports ---
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

API_URL = os.getenv("API_URL", "http://localhost:5000")
client = OpenAI()

st.set_page_config(page_title="ECT Data & AI Portal", layout="wide")

# ==========================================
# SIDEBAR: RAG KNOWLEDGE BASE
# ==========================================
with st.sidebar:
    st.header("📚 Historical Knowledge Base")
    st.write("Connect to a storage location to query past reports and site models.")
    
    # Example placeholder targeting an Azure Data Lake mount or local folder
    storage_path = st.text_input("Storage Location Path", placeholder="/mnt/lakehouse/gold/reports")
    
    if st.button("Index Directory"):
        if os.path.exists(storage_path) and os.path.isdir(storage_path):
            with st.spinner("Loading and embedding documents..."):
                try:
                    # 1. Load Documents
                    loader = DirectoryLoader(storage_path, glob="**/*.*", use_multithreading=True)
                    #loader = DirectoryLoader(storage_path, glob="**/*.pdf") # Adjust glob for .txt, .csv, etc.
                    docs = loader.load()
                    
                    if not docs:
                        st.warning("No documents found in the specified directory.")
                    else:
                        # 2. Split Text into manageable chunks
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        splits = text_splitter.split_documents(docs)
                        
                        # 3. Create Embeddings and Store in FAISS Vector DB
                        embeddings = OpenAIEmbeddings()
                        vectorstore = FAISS.from_documents(splits, embeddings)
                        
                        # Store the retriever in session state for querying later
                        st.session_state['retriever'] = vectorstore.as_retriever()
                        st.success(f"Successfully indexed {len(docs)} documents!")
                except Exception as e:
                    st.error(f"Failed to index storage location: {str(e)}")
        else:
            st.error("Invalid path. Ensure the storage location is mounted and accessible.")

    st.divider()
    
    # RAG Chat Interface
    if 'retriever' in st.session_state:
        st.subheader("💬 Query Knowledge Base")
        rag_prompt = st.text_input("Ask about the historical data:")
        
        if st.button("Search Knowledge Base") and rag_prompt:
            with st.spinner("Searching..."):
                # Define how the LLM should use the retrieved context
                system_prompt = (
                    "You are an intelligent systems assistant specializing in environmental consulting. "
                    "Use the following pieces of retrieved context to answer the question. "
                    "If you don't know the answer, say that you don't know.\n\n"
                    "Context: {context}"
                )
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{input}"),
                ])
                
                llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
                question_answer_chain = create_stuff_documents_chain(llm, prompt)
                rag_chain = create_retrieval_chain(st.session_state['retriever'], question_answer_chain)
                
                response = rag_chain.invoke({"input": rag_prompt})
                st.info(response["answer"])
    else:
        st.info("Connect a storage location above to enable search.")


# ==========================================
# MAIN PAGE: DATA ANONYMIZATION PIPELINE
# ==========================================
st.title("🛡️ Data Sanitization Pipeline")
st.write("Upload a batch of datasets to automatically redact PII before analysis.")

if 'clean_data' not in st.session_state:
    st.session_state['clean_data'] = None

uploaded_files = st.file_uploader(
    "Choose files", 
    type=['csv', 'xlsx', 'xls', 'pdf', 'db', 'sqlite', 'txt'], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Anonymize Batch"):
        with st.spinner(f"Analyzing and redacting PII for {len(uploaded_files)} file(s)..."):
            try:
                files_payload = [
                    ('files', (file.name, file.getvalue(), file.type)) 
                    for file in uploaded_files
                ]
                
                response = requests.post(f"{API_URL}/api/anonymize", files=files_payload)
                response.raise_for_status()
                
                data = response.json()
                st.success(f"Anonymization Complete! Processed {data.get('processed_count', 0)} file(s).")
                st.session_state['clean_data'] = data.get("batch_results", [])
                
            except requests.exceptions.HTTPError as err:
                try:
                    error_message = response.json().get('error', str(err))
                except ValueError:
                    error_message = f"Server Error ({response.status_code})"
                st.error(f"API Error: {error_message}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

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
