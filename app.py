# app.py

import os
import streamlit as st
import plotly.express as px

# ==== Import Modules ====
from modules.expense_analyzer import load_transactions, categorize_expenses, get_summary
from modules.trend_forecaster import forecast_expense
from modules.chatbot import ask_finance_bot
from modules.pdf_qa_bot import ask_pdf_question
from dotenv import load_dotenv
load_dotenv()


# ==== Page Setup ====
st.set_page_config(page_title="FinGenAI", page_icon="📊", layout="wide")

# ==== Custom CSS ====
# ==== Modern Styling ====
st.markdown("""
    <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

        /* Change background color */
        .stApp {
            background-color: #0F1716;
            font-family: 'Poppins', sans-serif;
        }

        /* Headings */
        h1, h2, h3, h4 {
            font-family: 'inter', sans-serif;
            font-weight: 700;
            color: #222;
        }

        /* Input fields and text areas */
        .stTextInput input, .stTextArea textarea {
            border-radius: 10px;
            padding: 0.75rem;
            border: 1px solid #ccc;
        }

        /* Buttons */
        .stButton > button {
            background-color: #3b82f6;
            color: white;
            font-size: 25px;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
            margin-top: 10px;
        }

        .stButton > button:hover {
            background-color: #2563eb;
            transition: all 0.3s ease;
        }

        /* Tabs spacing */
        .stTabs [role="tablist"] {
            gap: 30px;
            
        }

        /* Boxed subheaders */
        .block-title {
            background: linear-gradient(to right, #3b82f6, #60a5fa);
            color: white;
            padding: 0.75rem 1rem;
            margin-top: 1.5rem;
            border-radius: 8px;
            font-size: 40px;
            font-weight: 600;
        }

        /* Add more padding inside app */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Font for markdowns */
        .markdown-text-container {
            font-size: 1.05rem;
            line-height: 1.6;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        /* Fade-in animation */
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(15px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        /* Apply fade-in to widgets */
        .stMarkdown, .stDataFrame, .stButton, .stTextInput, .stPlotlyChart, .stTextArea {
            animation: fadeIn 0.7s ease-out;
        }

        /* Animate PDF upload sections */
        .stFileUploader {
            animation: fadeIn 0.8s ease-in-out;
        }

        /* Answer box animation */
        .stAlert-success {
            animation: fadeIn 1s ease-in;
        }

        /* Title fade-in */
        .css-10trblm {
            animation: fadeIn 1s ease-in;
        }
    </style>
""", unsafe_allow_html=True)


# ==== App Title ====
st.title(" FinGenAI")
st.markdown("##### A Multi-Tool Financial Assistant")
st.markdown("---")


# ==== TABS ====
tabs = st.tabs(["📁 PDF Q&A" ,"📊 Expense Analyzer and Forecaster", "🤖 Chatbot"])

# ========== 📁 TAB 1: PDF Q&A ==========
with tabs[0]:
    st.header("📁 Financial PDF Q&A (Pinecone-powered)")

 
# pdf q/a bot
from modules.pdf_processor import process_pdf, get_file_hash  # or use compute_file_hash
from modules.pinecone_handler import vectors_exist_in_pinecone, upload_embeddings_to_pinecone


uploaded_files = st.file_uploader("📤 Upload Financial PDFs", type=["pdf"], accept_multiple_files=True)

# Initialize session state
if "file_hash" not in st.session_state:
    st.session_state.file_hash = None

if "file_hashes" not in st.session_state:
    st.session_state.file_hashes = []

if "file_paths" not in st.session_state:
    st.session_state.file_paths = {}

if "all_chunks" not in st.session_state:
    st.session_state.all_chunks = []

if uploaded_files:
    os.makedirs("temp", exist_ok=True)

    for file in uploaded_files:
        # Save uploaded file locally
        file_path = os.path.join("temp", file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

        file_hash = get_file_hash(file_path)

        # Check if this file hash was already processed in this session
        if file_hash in st.session_state.file_hashes:
            st.info(f"🔁 {file.name} already processed in this session.")
            continue

        with st.spinner(f"📄 Processing {file.name}..."):
            # Process the PDF
            chunks = process_pdf(file_path)
            chunks = [c for c in chunks if c.get("text") or c.get("table_text")]

            if not chunks:
                st.warning(f"⚠️ No content found in {file.name}. Skipping.")
                continue

            # Check Pinecone only if embeddings not already uploaded
            if not vectors_exist_in_pinecone(file_hash):
                upload_embeddings_to_pinecone(file_hash, chunks)
                st.success(f"📥 Uploaded {len(chunks)} chunks from {file.name}.")
            else:
                st.info(f"✅ Embeddings already exist for {file.name}.")

            # Save session state
            st.session_state.file_hashes.append(file_hash)
            st.session_state.file_paths[file_hash] = file_path
            st.session_state.all_chunks.extend(chunks)

        

    st.success("✅ All PDFs processed and indexed.")

# UI for asking questions
if st.session_state.all_chunks:
    st.subheader("💬 Ask a Question")
    query = st.text_input("Type your financial question here...")

    if st.button("Get Answer") and query.strip():
        with st.spinner("🔍 Fetching answer..."):
            # Assume last uploaded PDF is used for now
            last_file_hash = st.session_state.file_hashes[-1]
            answer = ask_pdf_question(query, last_file_hash)
            st.markdown("### 📌 Answer")
            st.success(answer)



# ========== 📊 TAB 2: Expense Analyzer ==========
with tabs[1]:
    st.header("📊 Expense Analyzer (CSV Upload)")

    uploaded_csv = st.file_uploader("📤 Upload your transaction CSV", type=["csv"])

    if uploaded_csv is not None:
        df = load_transactions(uploaded_csv)
        df = categorize_expenses(df)

        st.subheader("📋 Transaction Table")
        st.dataframe(df)

        st.subheader("📈 Summary by Category")
        summary = get_summary(df)
        st.dataframe(summary)

        fig = px.bar(summary, x=summary.index, y='Amount', title="Spending by Category")
        st.plotly_chart(fig)

        pie_fig = px.pie(summary.reset_index(), names='Category', values='Amount', title="Spending Distribution")
        st.plotly_chart(pie_fig)

        st.subheader("🔮 Expense Forecast")
        if st.checkbox("Show Forecast for Next 3 Months"):
            forecast_df, error = forecast_expense(df)
            if error:
                st.warning(error)
            else:
                st.dataframe(forecast_df)
                fig2 = px.line(forecast_df, x='Month', y='Predicted_Expense', title='Forecasted Expenses')
                st.plotly_chart(fig2)


# ========== 🤖 TAB 3: Chatbot ==========

with tabs[2]:
    st.header("🤖 Ask FinGenAI (Chatbot)")

    user_input = st.text_input("Ask anything about finance (general knowledge):")

    if user_input.strip():
        with st.spinner("Thinking..."):
            response = ask_finance_bot(user_input)
            st.markdown("### 🧠 Answer")
            st.success(response)




