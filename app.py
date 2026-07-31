import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
import pypdf
import docx
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Set up page configurations as the first Streamlit command
st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Document Parsers
# ---------------------------------------------------------

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        pdf_reader = pypdf.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error parsing PDF: {str(e)}")

def parse_docx(file_bytes: bytes) -> str:
    """Extract text from a Word DOCX file."""
    try:
        doc = docx.Document(BytesIO(file_bytes))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error parsing Word Document: {str(e)}")

def parse_txt(file_bytes: bytes) -> str:
    """Extract text from a plain TXT file with encoding fallback."""
    try:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1")
    except Exception as e:
        raise ValueError(f"Error parsing Text File: {str(e)}")

# ---------------------------------------------------------
# Custom Styling (Premium Glassmorphic Dark UI)
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    /* Custom font and base styling */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main container background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(20, 18, 38, 1) 0%, rgba(10, 8, 16, 1) 90%);
        color: #F1F5F9 !important;
    }
    
    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background-color: rgba(12, 10, 20, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Title gradient */
    h1 {
        background: linear-gradient(135deg, #A855F7 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    h2, h3 {
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }
    
    /* Glassmorphic card styling */
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(168, 85, 247, 0.3);
        box-shadow: 0 8px 32px 0 rgba(168, 85, 247, 0.1);
    }
    
    /* Buttons custom design */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6) !important;
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Text input custom hover and focus outline */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        transition: border-color 0.2s ease;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: #6366F1 !important;
    }
    
    /* Notification alerts */
    [data-testid="stNotification"] {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
    }
    
    /* Chat Q&A Styling */
    .chat-bubble {
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 16px;
        line-height: 1.6;
        font-size: 15px;
    }
    
    .user-bubble {
        background: rgba(99, 102, 241, 0.08) !important;
        border-left: 4px solid #6366F1;
        border-top-left-radius: 4px;
    }
    
    .assistant-bubble {
        background: rgba(168, 85, 247, 0.06) !important;
        border-left: 4px solid #A855F7;
        border-top-left-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Status Dots */
    .dot {
        height: 10px;
        width: 10px;
        background-color: #EF4444;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .dot-active {
        background-color: #10B981;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# State Management & Sidebar Settings
# ---------------------------------------------------------

# Retrieve the GOOGLE_API_KEY from environment variables
env_api_key = os.getenv("GOOGLE_API_KEY")

# Initialize Session State variables
if "api_key" not in st.session_state:
    st.session_state["api_key"] = env_api_key or ""

if "document_text" not in st.session_state:
    st.session_state["document_text"] = None
    st.session_state["file_name"] = ""
    st.session_state["file_size"] = 0

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Text input for manual API Key fallback entry
    user_key = st.text_input(
        "Gemini API Key",
        value=st.session_state["api_key"],
        type="password",
        help="Paste your Gemini API key here. It is kept secure inside the session memory."
    )
    if user_key != st.session_state["api_key"]:
        st.session_state["api_key"] = user_key
        st.rerun()
    
    # Help link to generate key
    st.markdown(
        """
        <p style="font-size: 13px; margin-top: -10px;">
            🔑 <a href="https://aistudio.google.com/" target="_blank" style="color: #6366F1; text-decoration: none; font-weight: 500;">
                Get a free key from Google AI Studio
            </a>
        </p>
        """,
        unsafe_allow_html=True
    )
    
    # Visual status badge
    if st.session_state["api_key"]:
        st.markdown(
            '<div style="font-size: 13px; color: #10B981; font-weight: 600; margin-bottom: 15px;">'
            '<span class="dot dot-active"></span>API Connection Ready'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="font-size: 13px; color: #EF4444; font-weight: 600; margin-bottom: 15px;">'
            '<span class="dot"></span>API Key Missing'
            '</div>',
            unsafe_allow_html=True
        )
    
    # Model Selection
    model_options = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.0-flash"
    ]
    
    selected_model = st.selectbox(
        "Generative Model",
        options=model_options,
        index=0,
        help="gemini-3.5-flash-lite is the recommended starting model."
    )
    
    st.markdown("---")
    st.markdown("### 📄 App Support")
    st.info(
        "Supported formats:\n"
        "- PDF Documents (.pdf)\n"
        "- Word Documents (.docx)\n"
        "- Text Files (.txt)"
    )

# ---------------------------------------------------------
# Main UI Layout
# ---------------------------------------------------------

st.title("📄 AI Document Assistant")
st.markdown(
    "<p style='font-size: 16px; opacity: 0.85; margin-top: -15px; margin-bottom: 30px;'>"
    "Upload business documents, contracts, or text logs and query them using state-of-the-art LLMs."
    "</p>",
    unsafe_allow_html=True
)

# 1. File Upload Section
uploaded_file = st.file_uploader(
    "Choose a file to parse", 
    type=["pdf", "docx", "txt"],
    help="Select a PDF, DOCX or TXT file to query."
)

if uploaded_file is not None:
    # Compute unique key to identify if we need to reload
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # Parse file if it is new
    if st.session_state.get("current_file_key") != file_key:
        with st.spinner("🔍 Parsing and indexing document..."):
            try:
                file_bytes = uploaded_file.read()
                file_extension = uploaded_file.name.split(".")[-1].lower()
                
                if file_extension == "pdf":
                    parsed_text = parse_pdf(file_bytes)
                elif file_extension == "docx":
                    parsed_text = parse_docx(file_bytes)
                else:
                    parsed_text = parse_txt(file_bytes)
                
                # Store parsed text in session state
                st.session_state["document_text"] = parsed_text
                st.session_state["current_file_key"] = file_key
                st.session_state["file_name"] = uploaded_file.name
                st.session_state["file_size"] = uploaded_file.size
                st.success("🎉 Document successfully parsed!")
            except Exception as e:
                st.error(f"Failed to read file: {e}")
                st.session_state["document_text"] = None
                st.session_state["current_file_key"] = None

# Show metadata card if file is parsed and loaded
if st.session_state["document_text"]:
    char_count = len(st.session_state["document_text"])
    word_count = len(st.session_state["document_text"].split())
    st.markdown(
        f"""
        <div class="glass-card">
            <h4 style="margin-top: 0; color: #A855F7;">📊 Document Statistics</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr>
                    <td style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); opacity: 0.8;"><b>Filename:</b></td>
                    <td style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right;">{st.session_state["file_name"]}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); opacity: 0.8;"><b>File Size:</b></td>
                    <td style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right;">{st.session_state["file_size"]/1024:.1f} KB</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); opacity: 0.8;"><b>Character Count:</b></td>
                    <td style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right;">{char_count:,}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; opacity: 0.8;"><b>Estimated Words:</b></td>
                    <td style="padding: 6px 0; text-align: right;">{word_count:,}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("💡 To start, upload a document or ask a general question below.")

# 2. Q&A Section
question = st.text_input("💬 Ask a question:")

col1, col2 = st.columns([1, 4])
with col1:
    generate_btn = st.button("✨ Generate Answer")

if generate_btn:
    if not st.session_state["api_key"]:
        st.error("🔑 Please set your Gemini API Key in the sidebar settings first.")
    elif not question:
        st.warning("⚠️ Please enter a question to generate an answer.")
    else:
        with st.spinner("🧠 Generative AI is thinking..."):
            try:
                # Initialize the Google GenAI SDK client
                client = genai.Client(api_key=st.session_state["api_key"])
                
                # Assemble system prompting and context if document is loaded
                contents = []
                system_instruction = (
                    "You are a professional, smart, and precise AI Document Assistant. "
                    "Analyze the provided document context carefully and give clear, correct, and structured answers. "
                    "If the user asks a question that is not covered or relevant to the document, "
                    "answer it using your general knowledge but mention that it is not in the document."
                )
                
                if st.session_state["document_text"]:
                    context_msg = (
                        f"Here is the context of the uploaded document:\n\n"
                        f"--- START DOCUMENT CONTENT ---\n"
                        f"{st.session_state['document_text']}\n"
                        f"--- END DOCUMENT CONTENT ---\n\n"
                        f"Answer this query based on the text: {question}"
                    )
                    contents.append(context_msg)
                else:
                    system_instruction = "You are a helpful general-purpose AI assistant."
                    contents.append(question)
                
                # Generate content using the modern SDK client
                response = client.models.generate_content(
                    model=selected_model,
                    contents=contents,
                    config={"system_instruction": system_instruction}
                )
                
                # Display Question and Answer bubbles
                st.markdown("### 📝 Results")
                
                st.markdown(
                    f"""
                    <div class="chat-bubble user-bubble">
                        <b>Question:</b><br>{question}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    f"""
                    <div class="chat-bubble assistant-bubble">
                        <b>Answer ({selected_model}):</b><br>
                        {response.text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            except APIError as api_err:
                st.error(f"🔒 API Error: {api_err.message}")
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
