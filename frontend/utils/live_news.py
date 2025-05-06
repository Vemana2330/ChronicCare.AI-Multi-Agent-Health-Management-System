# utils/live_news.py

import requests
import streamlit as st

API_URL = "http://fastapi_service:8000/news"  # Update to deployed URL if needed

def render_live_news_page():
    """
    Renders the live news page with condition dropdown and clickable news previews + GPT summary
    """
    st.title("📰 Live News on Chronic Conditions")
    st.markdown("Stay up to date with the latest research, treatments, and medical innovations.")

    # --- Dropdown for condition selection ---
    condition = st.selectbox(
        "🔽 Select a condition to fetch the latest medical news:",
        ["Cholesterol", "CKD", "Gluten", "Hypertension", "Polycystic", "Type2", "Obesity"]
    )

    # --- Button to trigger API ---
    if st.button("🔍 Fetch News"):
        with st.spinner("📡 Gathering live updates..."):
            try:
                response = requests.post(API_URL, json={"condition": condition})
                response.raise_for_status()
                result = response.json()

                news = result.get("news", {})
                articles = news.get("articles", [])

                if not articles:
                    st.warning("⚠️ No recent news found. Try another condition or check back later.")
                    return

                st.success(f"✅ Top {len(articles)} News Articles on **{condition}**")

                # === Display Articles with Individual Summaries ===
                for i, item in enumerate(articles, 1):
                    st.markdown("----")
                    st.markdown(f"### {i}. {item['title']}")
                    st.markdown(f"**🗞 Source:** {item['source']} &nbsp;&nbsp; | &nbsp;&nbsp; **📅 Date:** {item['published']}")
                    st.markdown(f"{item['preview']}")
                    st.markdown(f"[🔗 Read Full Article]({item['url']})", unsafe_allow_html=True)

                    # Show GPT summary if available
                    if "summary" in item:
                        st.markdown("**🧠 GPT Summary:**")
                        st.markdown(f"> {item['summary']}")
                    else:
                        st.markdown("⚠️ GPT Summary not available.")

            except Exception as e:
                st.error(f"❌ Failed to fetch news: {str(e)}")
