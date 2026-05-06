import streamlit as st
import anthropic
import os
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

st.set_page_config(
    page_title="ZeroToQuery | Blue Jay Credit Union",
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
    .schema-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.85rem;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCHEMA DEFINITION
# ─────────────────────────────────────────────
SCHEMA = """
DATABASE: BJCU_DW
SCHEMA: CORE

TABLE: BRANCHES
  BRANCH_ID         INTEGER       Primary Key
  BRANCH_NAME       VARCHAR       Branch name (e.g. 'Downtown Baltimore')
  ADDRESS           VARCHAR       Street address
  CITY              VARCHAR       City
  STATE             VARCHAR       State (e.g. 'MD')
  ZIP_CODE          VARCHAR       ZIP code
  PHONE             VARCHAR       Phone number
  MANAGER_NAME      VARCHAR       Branch manager full name
  DATE_OPENED       DATE          Date branch opened
  STATUS            VARCHAR       'Active' or 'Closed'

TABLE: EMPLOYEES
  EMPLOYEE_ID       INTEGER       Primary Key
  FIRST_NAME        VARCHAR       First name
  LAST_NAME         VARCHAR       Last name
  BRANCH_ID         INTEGER       Foreign Key -> BRANCHES.BRANCH_ID
  DEPARTMENT        VARCHAR       Department (e.g. 'Lending', 'Operations', 'Member Services')
  JOB_TITLE         VARCHAR       Job title
  HIRE_DATE         DATE          Date hired
  SALARY            DECIMAL(10,2) Annual salary
  STATUS            VARCHAR       'Active' or 'Terminated'

TABLE: MEMBERS
  MEMBER_ID         INTEGER       Primary Key
  FIRST_NAME        VARCHAR       First name
  LAST_NAME         VARCHAR       Last name
  EMAIL             VARCHAR       Email address
  PHONE             VARCHAR       Phone number
  DATE_OF_BIRTH     DATE          Date of birth
  DATE_JOINED       DATE          Date member joined BJCU
  MEMBERSHIP_STATUS VARCHAR       'Active', 'Inactive', or 'Suspended'
  MEMBERSHIP_TYPE   VARCHAR       'Individual', 'Joint', or 'Business'
  BRANCH_ID         INTEGER       Foreign Key -> BRANCHES.BRANCH_ID
  CREDIT_SCORE      INTEGER       Credit score (580-820)
  EMPLOYER          VARCHAR       Employer name
  ANNUAL_INCOME     DECIMAL(10,2) Annual income

TABLE: ACCOUNTS
  ACCOUNT_ID        INTEGER       Primary Key
  MEMBER_ID         INTEGER       Foreign Key -> MEMBERS.MEMBER_ID
  ACCOUNT_TYPE      VARCHAR       'Checking', 'Savings', 'Money Market', or 'CD'
  BALANCE           DECIMAL(10,2) Current balance
  AVAILABLE_BALANCE DECIMAL(10,2) Available balance
  DATE_OPENED       DATE          Date account opened
  DATE_CLOSED       DATE          Date account closed (NULL if active)
  STATUS            VARCHAR       'Active', 'Closed', or 'Frozen'
  INTEREST_RATE     DECIMAL(5,4)  Interest rate
  BRANCH_ID         INTEGER       Foreign Key -> BRANCHES.BRANCH_ID

TABLE: TRANSACTIONS
  TRANSACTION_ID    INTEGER       Primary Key
  ACCOUNT_ID        INTEGER       Foreign Key -> ACCOUNTS.ACCOUNT_ID
  MEMBER_ID         INTEGER       Foreign Key -> MEMBERS.MEMBER_ID
  TRANSACTION_DATE  DATE          Date of transaction
  TRANSACTION_TYPE  VARCHAR       'Deposit', 'Withdrawal', 'Transfer', 'Fee', or 'Interest'
  AMOUNT            DECIMAL(10,2) Transaction amount
  RUNNING_BALANCE   DECIMAL(10,2) Running account balance after transaction
  DESCRIPTION       VARCHAR       Transaction description
  CHANNEL           VARCHAR       'Branch', 'ATM', 'Online', or 'Mobile'
  BRANCH_ID         INTEGER       Foreign Key -> BRANCHES.BRANCH_ID

TABLE: LOANS
  LOAN_ID           INTEGER       Primary Key
  MEMBER_ID         INTEGER       Foreign Key -> MEMBERS.MEMBER_ID
  LOAN_TYPE         VARCHAR       'Auto', 'Mortgage', 'Personal', 'Student', or 'Business'
  LOAN_AMOUNT       DECIMAL(10,2) Original loan amount
  OUTSTANDING_BALANCE DECIMAL(10,2) Remaining balance
  INTEREST_RATE     DECIMAL(5,2)  Annual interest rate (%)
  MONTHLY_PAYMENT   DECIMAL(10,2) Monthly payment amount
  ORIGINATION_DATE  DATE          Loan origination date
  MATURITY_DATE     DATE          Loan maturity date
  LOAN_STATUS       VARCHAR       'Current', 'Delinquent', 'Default', or 'Paid Off'
  DAYS_PAST_DUE     INTEGER       Number of days past due (0 if current)
  BRANCH_ID         INTEGER       Foreign Key -> BRANCHES.BRANCH_ID

TABLE: LOAN_PAYMENTS
  PAYMENT_ID        INTEGER       Primary Key
  LOAN_ID           INTEGER       Foreign Key -> LOANS.LOAN_ID
  MEMBER_ID         INTEGER       Foreign Key -> MEMBERS.MEMBER_ID
  PAYMENT_DATE      DATE          Date payment was made
  AMOUNT_PAID       DECIMAL(10,2) Total amount paid
  PRINCIPAL_PAID    DECIMAL(10,2) Principal portion of payment
  INTEREST_PAID     DECIMAL(10,2) Interest portion of payment
  REMAINING_BALANCE DECIMAL(10,2) Remaining loan balance after payment
  PAYMENT_STATUS    VARCHAR       'On Time', 'Late', or 'Missed'
"""

# ─────────────────────────────────────────────
# LOAD DATA INTO DUCKDB
# ─────────────────────────────────────────────
@st.cache_resource
def load_data():
    conn = duckdb.connect(database=":memory:")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    tables = ["BRANCHES", "EMPLOYEES", "MEMBERS", "ACCOUNTS",
              "TRANSACTIONS", "LOANS", "LOAN_PAYMENTS"]
    for table in tables:
        path = os.path.join(data_dir, f"{table}.csv")
        conn.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{path}')")
    return conn

conn = load_data()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("BJCU.png", use_container_width=True)
    st.markdown("### About ZeroToQuery")
    st.write("ZeroToQuery is a schema-aware SQL assistant built exclusively for Blue Jay Credit Union branch operations analysts. Unlike general-purpose AI tools, ZeroToQuery knows BJCU's exact Snowflake database structure, including every table, every column, and every relationship. Analysts describe what KPI data they need in plain English and receive a production-ready Snowflake SQL query using BJCU's real schema, plus live results from the BJCU data warehouse. No SQL knowledge required. No schema lookup required. No manual editing required.")
    st.markdown("### How to Use")
    st.write("1. Describe the KPI or member data you need")
    st.write("2. Click Generate SQL Query")
    st.write("3. Review the Snowflake-ready query and live BJCU results")
    st.write("4. Copy and run directly in Snowflake")
    st.markdown("### Example Prompts")
    st.write("- Show me delinquent loan totals by branch this quarter")
    st.write("- Which members have a credit score below 620 and an active loan?")
    st.write("- What is the total deposit volume by channel this month?")
    st.write("- List all mortgage loans originated in 2024 with outstanding balance over $200,000")
    st.write("- How many new members joined each branch this year?")
    st.image("ZTQ Bot.png", use_container_width=True)

# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
st.image("ZeroToQuery (Light).png", width=480)
st.markdown("#### Snowflake SQL for Blue Jay Credit Union — Built for Branch Operations Analysts")
st.markdown("---")

with st.expander("View BJCU Database Schema", expanded=False):
    st.markdown('<div class="schema-box"><pre>' + SCHEMA + '</pre></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("**Describe What Data You Need:**")

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

user_input = st.text_area(
    label="",
    placeholder="Example: Show me all delinquent loans by branch",
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
                        "content": f"""You are a SQL expert assistant for Blue Jay Credit Union (BJCU), a Maryland-based credit union.
You help branch operations analysts generate production-ready SQL queries for weekly KPI reporting.

You have access to the following Snowflake database schema:
{SCHEMA}

CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. ONLY use column names that are explicitly listed in the schema above. Do NOT invent or assume column names.
2. Before writing any column name, verify it exists in the schema. For example:
   - LOANS has: LOAN_ID, MEMBER_ID, LOAN_TYPE, LOAN_AMOUNT, OUTSTANDING_BALANCE, INTEREST_RATE, MONTHLY_PAYMENT, ORIGINATION_DATE, MATURITY_DATE, LOAN_STATUS, DAYS_PAST_DUE, BRANCH_ID
   - MEMBERS has: MEMBER_ID, FIRST_NAME, LAST_NAME, EMAIL, PHONE, DATE_OF_BIRTH, DATE_JOINED, MEMBERSHIP_STATUS, MEMBERSHIP_TYPE, BRANCH_ID, CREDIT_SCORE, EMPLOYER, ANNUAL_INCOME
   - There is NO borrower_name, NO last_payment_date, NO account_number, NO member_name column
3. To get a member's name, JOIN LOANS to MEMBERS on MEMBER_ID and use MEMBERS.FIRST_NAME and MEMBERS.LAST_NAME
4. Write Snowflake-compatible SQL syntax
5. Always use fully qualified table names in the format: BJCU_DW.CORE.TABLE_NAME
6. Write clean, well-formatted SQL with proper indentation
7. If the request cannot be answered with the available schema, explain why

User request: {user_input}

Respond in exactly this format:
SQL QUERY:
```sql
[your SQL query here]
```

EXPLANATION:
[plain English explanation of what the query does and what KPI it supports]"""
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

            # Run query against BJCU sample data
            st.subheader("Live BJCU Results")
            try:
                local_sql = sql_part
                for table in ["BRANCHES", "EMPLOYEES", "MEMBERS", "ACCOUNTS",
                               "TRANSACTIONS", "LOANS", "LOAN_PAYMENTS"]:
                    local_sql = local_sql.replace(f"BJCU_DW.CORE.{table}", table)

                result_df = conn.execute(local_sql).fetchdf()
                if len(result_df) == 0:
                    st.info("Query returned no results.")
                else:
                    st.success(f"Query returned {len(result_df)} row(s) from the BJCU sample dataset.")
                    st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not run query against sample data: {str(e)}")
                st.info("Copy the query above and run it directly in your Snowflake environment.")
        else:
            st.write(response)