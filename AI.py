import os
import uuid
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Page Configuration
st.set_page_config(
    page_title="FlashAI - Coding Assistant",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ FlashAI Assistant")
st.caption("Python Coding & General AI Assistant")

# 2. Secrets / Environment / Sidebar se API Key handle karna
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

with st.sidebar:
    st.header("⚙️ Settings")
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key:", type="password")
    
    selected_model = st.selectbox(
        "Model",
        ["gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )

# 3. Validation Check
if not api_key:
    st.info("👈 Please enter your Gemini API Key in the sidebar or set it in Streamlit Secrets to start.")
    st.stop()

# API Configure karein
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# 4. Session State Management
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"name": "New Chat", "messages": []}
    st.session_state.active_chat_id = new_id

# Sidebar Chat Management
with st.sidebar:
    st.divider()
    if st.button("+ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"name": "New Chat", "messages": []}
        st.session_state.active_chat_id = new_id
        st.rerun()

    st.subheader("Chat History")
    for cid, cdata in list(st.session_state.chats.items()):
        col1, col2 = st.columns([0.8, 0.2])
        if col1.button(cdata["name"], key=f"btn_{cid}", use_container_width=True):
            st.session_state.active_chat_id = cid
            st.rerun()
        if col2.button("🗑️", key=f"del_{cid}"):
            del st.session_state.chats[cid]
            if st.session_state.active_chat_id == cid:
                remaining_ids = list(st.session_state.chats.keys())
                if remaining_ids:
                    st.session_state.active_chat_id = remaining_ids[0]
                else:
                    new_id = str(uuid.uuid4())
                    st.session_state.chats[new_id] = {"name": "New Chat", "messages": []}
                    st.session_state.active_chat_id = new_id
            st.rerun()

# Current Active Chat
active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

# Display Chat History
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. User Input and Model Response
user_prompt = st.chat_input("Type your message here...")

if user_prompt:
    # Set chat title if first message
    if len(messages) == 0:
        active_chat["name"] = user_prompt[:20] + ("..." if len(user_prompt) > 20 else "")

    # Display user message
    messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Load Model
                model = genai.GenerativeModel(selected_model)
                
                # Format history for Gemini API
                formatted_history = []
                for m in messages[:-1]:
                    role = "user" if m["role"] == "user" else "model"
                    formatted_history.append({"role": role, "parts": [m["content"]]})
                
                # Start chat session
                chat_session = model.start_chat(history=formatted_history)
                response = chat_session.send_message(user_prompt)
                
                # Render Response
                st.markdown(response.text)
                messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
