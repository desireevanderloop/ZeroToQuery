import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with st.sidebar:
    st.markdown("### About ZeroToQuery")
    st.write("ZeroToQuery helps business analysts and non-technical users generate SQL queries from plain language descriptions.")
    st.markdown("### How to Use")
    st.write("1. Describe what data you need in plain English")
    st.write("2. Click Generate SQL Query")
    st.write("3. Copy and run your query")
    st.markdown("### Example Prompts")
    st.write("- Show me total revenue by region for Q1 2024")
    st.write("- List all customers who have not placed an order in 90 days")
    st.write("- Find the top 5 products by units sold last month")
st.image("ZeroToQuery (Light).png", width=800)
st.markdown("#### From Question to Query in Seconds.")
st.markdown("---")

user_input = st.text_area(
    "Describe what data you need in plain English:",
    placeholder="Example: Show me the top 10 customers by total sales in 2024",
    height=150
)

if st.button("Generate SQL Query"):
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

            st.subheader("What This Query Does")
            st.write(explanation_part)
        else:
            st.write(response)