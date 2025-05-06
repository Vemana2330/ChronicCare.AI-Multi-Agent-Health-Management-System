# FILE: frontend/utils/knowledge_base.py

import streamlit as st
import requests
import json

API_AGENT_ENDPOINT = "http://fastapi_service:8000/agent"

CHRONIC_CONDITIONS = [
    "Cholesterol", "CKD", "Gluten", "Hypertension", "Polycystic", "Type2", "Obesity"
]

def show_knowledge_base():
    if "condition" not in st.session_state:
        st.session_state.condition = CHRONIC_CONDITIONS[0]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "last_summary" not in st.session_state:
        st.session_state.last_summary = None

    st.title("💬 Knowledgebase Assistant")
    st.markdown("Ask questions about chronic conditions, or generate a medical summary report.")

    st.markdown("### 🩺 Select a Chronic Condition")
    st.session_state.condition = st.selectbox("Choose a condition:", CHRONIC_CONDITIONS)

    user_input = st.text_input("Enter your question")

    st.divider()
    st.subheader("📜 Conversation")
    for msg in st.session_state.chat_history:
        if msg["type"] == "human":
            st.markdown(f"**🧑 You:** {msg['content']}")
        elif msg["type"] == "ai":
            if "generate report" in msg["content"].lower():
                st.markdown(
                    f"<div style='color:#0a9396'><b>📄 Summary Report:</b><br><pre style='white-space: pre-wrap'>{msg['content']}</pre></div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"""
<details>
<summary><strong>🤖 AI Response</strong></summary>

{msg['content']}

</details>
""", unsafe_allow_html=True)

    if st.button("Ask"):
        if user_input.strip():
            st.session_state.chat_history.append({"type": "human", "content": user_input})
            payload = {
                "input": user_input,
                "condition": st.session_state.condition,
                "chat_history": st.session_state.chat_history
            }

            with st.spinner("🤖 Thinking..."):
                try:
                    response = requests.post(API_AGENT_ENDPOINT, json=payload)
                    if response.status_code == 200:
                        result = response.json()["response"]
                        st.session_state.chat_history.append({"type": "ai", "content": result})
                    else:
                        st.error("❌ Something went wrong.")
                except Exception as e:
                    st.error("❌ Backend not responding.")
            st.rerun()

    if st.button("📄 Generate Summary Report"):
        st.session_state.chat_history.append({"type": "human", "content": "generate report"})
        payload = {
            "input": "generate report",
            "condition": st.session_state.condition,
            "chat_history": st.session_state.chat_history
        }

        with st.spinner("📄 Summarizing..."):
            try:
                response = requests.post(API_AGENT_ENDPOINT, json=payload)
                if response.status_code == 200:
                    result = response.json()["response"]
                    st.session_state.chat_history.append({"type": "ai", "content": result})
                    st.session_state.last_summary = result
                    st.rerun()
                else:
                    st.error("❌ Failed to generate summary.")
            except Exception as e:
                st.error("❌ Backend not responding.")
