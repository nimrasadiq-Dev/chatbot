import uuid
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="FlashAI Assistant", page_icon="⚡", layout="centered")

# 2. Dark Theme CSS & Login Card Styling
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; }
    .main-title { text-align: center; color: #ffffff; font-size: 2.5rem; margin-bottom: 0px; }
    .sub-title { text-align: center; color: #8b949e; font-size: 1.1rem; margin-bottom: 25px; }
    div[data-testid="stChatInput"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    div[data-testid="stChatMessage"] { background-color: #161b22; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
    
    /* Login Box Styling */
    div[data-testid="stForm"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 15px;
        padding: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Session State for Authentication
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================= LOGIN SCREEN =================
if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>⚡ Welcome to FlashAI Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Sign in to access your AI workspace</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔑 Login Dashboard")
            email = st.text_input("Email Address", placeholder="name@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Sign In 🚀", use_container_width=True)

            if submit_btn:
                # Basic email & password verification
                if "@" in email and len(password) >= 4:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Please enter a valid email and password (min 4 characters).")
    st.stop()

# ================= MAIN CHAT APP (LOGGED IN) =================

# Header
st.markdown("<h1 class='main-title'>⚡ FlashAI Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Python Coding & AI Solutions</p>", unsafe_allow_html=True)

# Chat Sessions Management
if "chats" not in st.session_state:
    st.session_state.chats = {"default": {"title": "New Chat", "messages": []}}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = "default"

# Sidebar Setup
st.sidebar.markdown(f"👤 *User:* {st.session_state.get('user_email', 'User')}")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Settings")
# Pehle Streamlit Secrets check karein, agar na mile toh user input lein
secret_key = st.secrets.get("GEMINI_API_KEY", "")
if secret_key:
    api_key = secret_key
else:
    raw_api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")
    api_key = raw_api_key.strip() if raw_api_key else ""

selected_model = st.sidebar.selectbox("Model:", ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-1.5-flash"])

st.sidebar.markdown("---")
st.sidebar.title("💬 Chat History")

# New Chat Button
if st.sidebar.button("➕ New Chat", use_container_width=True):
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.active_chat_id = new_id
    st.rerun()

# List Chats with Delete Option
for chat_id, chat_data in list(st.session_state.chats.items()):
    col1, col2 = st.sidebar.columns([0.8, 0.2])
    with col1:
        label = f"▶️ {chat_data['title']}" if chat_id == st.session_state.active_chat_id else chat_data['title']
        if st.button(label, key=f"select_{chat_id}"):
            st.session_state.active_chat_id = chat_id
            st.rerun()
            
    with col2:
        if st.button("🗑️", key=f"del_{chat_id}"):
            del st.session_state.chats[chat_id]
            if not st.session_state.chats:
                st.session_state.chats = {"default": {"title": "New Chat", "messages": []}}
            st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
            st.rerun()

if not api_key:
    st.info("👈 Please enter API Key in sidebar to start.")
    st.stop()

genai.configure(api_key=api_key)
active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

# Display Chat Messages
for idx, msg in enumerate(messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            c1, c2, _ = st.columns([0.1, 0.1, 0.8])
            with c1: st.button("👍", key=f"like_{idx}")
            with c2: st.button("👎", key=f"dislike_{idx}")

# Media Input Section
col_plus, col_chat = st.columns([0.1, 0.9])
with col_plus:
    with st.popover("➕"):
        file = st.file_uploader("📁 Upload", type=["png", "jpg", "mp3", "py", "txt"])
        use_cam = st.checkbox("📸 Use Camera")
        cam_photo = st.camera_input("Capture") if use_cam else None
        audio = st.audio_input("🎙️ Voice Note")

with col_chat:
    prompt = st.chat_input("Ask Gemini...")

# Execution Logic
if prompt or file or cam_photo or audio:
    payload = []
    if file: 
        payload.append(Image.open(file) if file.type.startswith("image") else file.read().decode('utf-8'))
    if cam_photo: 
        payload.append(Image.open(cam_photo))
    if audio: 
        payload.append(types.Part.from_bytes(data=audio.read(), mime_type="audio/wav"))
    
    text = prompt if prompt else "Analyze this attachment."
    payload.append(text)
    
    # User ka message add karein
    messages.append({"role": "user", "content": text})
    
    try:
        # Client ki bajaye Standard Model Call
        model = genai.GenerativeModel(selected_model)
        response = model.generate_content(payload)
        
        # AI ka response save karein
        messages.append({"role": "assistant", "content": response.text})
        st.rerun()
    except Exception as e:
        st.error(f"API Error: {e}")
