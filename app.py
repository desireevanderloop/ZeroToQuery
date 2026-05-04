import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

st.set_page_config(
    page_title="ZeroToQuery",
    page_icon="🔍",
    layout="centered"
)

st.markdown("""
    <style>
    .stButton button {
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        font-size: 15px !important;
    }
    h3 {
        font-size: 1.4rem !important;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### About ZeroToQuery")
    st.write("ZeroToQuery helps business analysts and non-technical users generate SQL queries from plain language descriptions.")
    st.markdown("### How to Use")
    st.write("1. Describe What Data You Need (English)")
    st.write("2. Click Generate SQL Query")
    st.write("3. Copy and Run Your Query")
    st.markdown("### Example Prompts")
    st.write("- Show Me Total Revenue by Region for Q1 2024")
    st.write("- List All Customers Who Have Not Placed an Order in 90 Days")
    st.write("- Find the Top 5 Products by Units Sold Last Month")
    st.image("ZTQ Bot.png", use_container_width=True)

st.image("ZeroToQuery (Light).png", width=480)
st.markdown("#### From Question to Query in Seconds.")
st.markdown("---")

st.markdown("**Describe What Data You Need (English):**")

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

user_input = st.text_area(
    label="",
    placeholder="Example: Show Me the Top 10 Customers by Total Sales in 2024",
    height=150,
    value=st.session_state.user_input
)

col1, col2 = st.columns([1, 1])

with col1:
    generate = st.button("Generate SQL Query", use_container_width=True)

with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.user_input = ""
        st.rerun()

if generate:
    if user_input.strip() == "":
        st.warning("Please describe what data you need first.")
    else:
        with st.spinner("Generating your SQL query..."):
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are a SQL expert assistant. A business user has described what data they need in plain English.
Your job is to:
1. Write a clean, ready-to-run SQL query that retrieves what they need
2. Provide a plain English explanation of what the query does

User request: {user_input}

Respond in exactly this format:
SQL QUERY:
```sql
[your SQL query here]
```

EXPLANATION:
[your plain English explanation here]"""
                    }
                ]
            )

        response = message.content[0].text

        if "SQL QUERY:" in response and "EXPLANATION:" in response:
            parts = response.split("EXPLANATION:")
            sql_part = parts[0].replace("SQL QUERY:", "").strip().replace("```sql", "").replace("```", "").strip()
            explanation_part = parts[1].strip()

            st.subheader("Your SQL Query")
            st.code(sql_part, language="sql")

            st.button("📋 Copy Query", on_click=lambda: st.write(""), help="Copy the query above to your clipboard")

            st.subheader("What This Query Does")
            st.write(explanation_part)
        else:
            st.write(response)