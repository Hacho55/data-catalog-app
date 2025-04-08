import streamlit as st
import pandas as pd
import os
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from datetime import datetime
from utils.utils import get_column_info, suggest_comment, build_comment_sql

# --- Load environment variables ---
load_dotenv(override=True)

# --- Logging utility ---
def log_event(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log.append(f"[{timestamp}] {msg}")

# --- UI Setup ---
st.set_page_config(page_title="Data Catalog Assistant", layout="wide")
st.title("🧠 AI - Table Column Data Catalog Assistant")

# --- Init session state ---
if "log" not in st.session_state:
    st.session_state.log = []
if "step" not in st.session_state:
    st.session_state.step = 0
if "df_edit" not in st.session_state:
    st.session_state.df_edit = None
if "read_only" not in st.session_state:
    st.session_state.read_only = False

# --- Sidebar Configuration ---
with st.sidebar:
    with st.expander("🪵 Debug Log", expanded=False):
        for entry in st.session_state.log[-50:]:
            st.text(entry)

    if st.button("🔄 Full reset"):
        st.session_state.clear()
        st.rerun()
        
    if st.button("🔁 Reset flow only"):
        for k in ["step", "df", "df_edit", "schema", "table", "table_loaded", "log", "table_description"]:
            st.session_state.pop(k, None)
        st.rerun()

    # st.checkbox("🔒 Read-only mode", key="read_only")
    
    st.header("Configuration")

    st.subheader("🔐 OpenAI Settings")
    if st.button("Load enviroment variables config from .env"):
        
    #     st.write("🔍 ENV CHECK", {
    #     "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    #     "DB_HOST": os.getenv("DB_HOST"),
    #     "DB_PORT": os.getenv("DB_PORT"),
    #     "DB_NAME": os.getenv("DB_NAME"),
    #     "DB_USER": os.getenv("DB_USER"),
    #     "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    # })
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        st.session_state.llm_model = "gpt-4o"
        st.session_state.db_host = os.getenv("DB_HOST", "localhost")
        st.session_state.db_port = os.getenv("DB_PORT", "5432")
        st.session_state.db_name = os.getenv("DB_NAME", "")
        st.session_state.db_user = os.getenv("DB_USER", "")
        st.session_state.db_password = os.getenv("DB_PASSWORD", "")
        st.success("✅ Config loaded from .env")
        log_event("Config loaded from .env")

    st.text_input("OpenAI API Key", key="openai_api_key", type="password")
    st.selectbox("Model", options=["gpt-4o", "gpt-4o-mini"], key="llm_model")

    st.subheader("🗄️ Database Settings")
    st.text_input("Host", key="db_host")
    st.text_input("Port", key="db_port")
    st.text_input("Database Name", key="db_name")
    st.text_input("Username", key="db_user")
    st.text_input("Password", key="db_password", type="password")

    if st.button("Test Connection"):
        try:
            engine = create_engine(
                f"postgresql+psycopg2://{st.session_state.db_user}:{st.session_state.db_password}@{st.session_state.db_host}:{st.session_state.db_port}/{st.session_state.db_name}"
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.success("✅ Database connection successful")
            st.session_state.db_valid = True
            st.session_state.db_engine = engine
            log_event("Database connection successful")
        except Exception as e:
            st.error(f"❌ Failed to connect to database: {e}")
            st.session_state.db_valid = False
            log_event(f"Database connection error: {e}")

    # if st.checkbox("Show debug log"):
    #     st.subheader("🪵 Debug Log")
    #     for entry in st.session_state.log:
    #         st.code(entry, language="text")

# --- Step 0: Validations ---
if not st.session_state.get("openai_api_key"):
    st.warning("⚠️ Please, load your OpenAI key in the side panel.")
    st.stop()

if not st.session_state.get("db_valid"):
    st.warning("⚠️ Please, load your db connection settings in the side panel.")
    st.stop()

llm = ChatOpenAI(
    temperature=0,
    model=st.session_state.llm_model,
    openai_api_key=st.session_state.openai_api_key
)

# --- Step 1: Select table ---
st.subheader("Step 1: Select schema/table")
schema = st.text_input("Schema", value=st.session_state.get("schema", "public"))
table = st.text_input("Table", value=st.session_state.get("table", ""))

if st.button("Load"):
    # Reset flow state if reloading a table
    for k in ["step", "df", "df_edit", "table_loaded", "table_description"]:
        st.session_state.pop(k, None)
        
    st.session_state.schema = schema
    st.session_state.table = table
    st.session_state.df = get_column_info(st.session_state.db_engine, schema, table)
    st.session_state.df_edit = st.session_state.df.copy()
    st.session_state.df_edit.rename(columns={'description': 'current_description'}, inplace=True)
    st.session_state.df_edit['llm_suggestion'] = None
    st.session_state.df_edit['final_comment'] = None
    st.session_state.table_loaded = True
    st.session_state.step = 1
    log_event(f"Table loaded: {schema}.{table}")
    st.rerun()

if st.session_state.get("df") is not None:
    st.subheader(f"Preview table: {st.session_state.schema}.{st.session_state.table}")
    st.dataframe(st.session_state.df)
    if st.session_state.step == 1 and st.button("Continue with suggestions"):
        st.session_state.step = 2
        st.rerun()
        
# --- Step 2: Generar sugerencias ---
if st.session_state.step >= 2:
    st.subheader("Step 2: Generate comments for columns without description, edit prompt if you like.")
    default_template = (
        "You are helping document a PostgreSQL table.\n"
        "Write a short and clear description (one sentence) for a column named '{column_name}' of type '{data_type}'.\n"
        "- Do NOT include the column name.\n"
        "- Do NOT include the table name.\n"
        "- Do NOT use quotation marks.\n"
        "Output only the sentence."
    )
    template = st.text_area("Prompt template", value=default_template, height=150)
    if st.button("Generate descriptions"):
        for i, row in st.session_state.df_edit.iterrows():
            if pd.isna(row['current_description']):
                log_event(f"Getting LLM comments for column: {row['column_name']}")
                suggestion = suggest_comment(row['column_name'], row['data_type'], template, llm)
                st.session_state.df_edit.at[i, 'llm_suggestion'] = suggestion
                log_event(f"LLM response: {suggestion}")
        st.success("✅ Descriptions generated")
    if st.button("Next"):
        st.session_state.step = 3
        log_event("Move to step 3: comments edition")
        st.rerun()

# --- Paso 3: Edición de comentarios ---
if st.session_state.step >= 3:
    st.subheader("Step 3: Edit and confirm comments")
    for i, row in st.session_state.df_edit.iterrows():
        st.markdown(f"**{row['column_name']}** ({row['data_type']})")
        current = row['current_description'] or ""
        suggestion = row['llm_suggestion'] or ""
        st.caption(f"Current: {current}")
        if suggestion:
            st.caption(f"Suggestion: {suggestion}")
        st.session_state.df_edit.at[i, 'final_comment'] = st.text_input(
            "Comment", value=current or suggestion, key=f"final_{i}"
        )
    if st.button("Continue with SQL sentence"):
        st.session_state.step = 4
        log_event("Move to step 4: SQL script")
        st.rerun()

# --- Paso 4: Confirmar y ejecutar SQL ---
if st.session_state.step >= 4:
    st.subheader("Step 4: Confirm and apply SQL")
    sql_statements = build_comment_sql(
        st.session_state.df_edit,
        st.session_state.schema,
        st.session_state.table,
        st.session_state.log
    )
    if not sql_statements:
        st.info("No new comments to apply.")
    else:
        st.code("\n".join(sql_statements), language="sql")
        if st.button("Execute on db"):
            try:
                with st.session_state.db_engine.begin() as conn:
                    for stmt in sql_statements:
                        conn.execute(text(stmt))
                st.success("✅ Comments successfully applied.")
                log_event("SQL executed")
            except SQLAlchemyError as e:
                st.error(f"❌ Execution error: {e}")
                log_event(f"SQL error: {e}")
        if st.button("Continue with file export"):
            st.session_state.step = 5
            log_event("Move to step 5: Markdown export")
            st.rerun()

# --- Paso 5: Exportar a Markdown ---
if st.session_state.step >= 5:
    st.subheader("Step 5: Generate Markdown document")

    if "table_description" not in st.session_state:
        prompt = (
            f"You are helping document a PostgreSQL table named '{st.session_state.table}'. "
            f"Here are the columns: {[col for col in st.session_state.df_edit['column_name']]}. "
            "Write a short description for this table. Do not include column names. No more than 3 sentences, only if needed."
        )
        st.session_state.table_description = llm.invoke(prompt).content.strip()
        log_event("Get description from LLM")

    description_input = st.text_area("Table description", value=st.session_state.table_description)

    md_lines = [
        f"## Table: `{st.session_state.table}`",
        "",
        f"**Description:** {description_input}",
        "",
        "| Column | Data Type | Description |",
        "|--------|-----------|-------------|",
    ]
    for _, row in st.session_state.df_edit.iterrows():
        name = row['column_name']
        dtype = row['data_type']
        comment = row['final_comment'] or ""
        md_lines.append(f"| `{name}` | `{dtype}` | {comment} |")

    markdown_result = "\n".join(md_lines)
    st.markdown("### Markdown Code Preview")
    st.code(markdown_result, language="markdown")

    st.markdown("### Final view")
    st.markdown(markdown_result, unsafe_allow_html=False)
    
    st.download_button("📥 Download Markdown Doc", markdown_result, file_name=f"{st.session_state.table}_catalog.md")
    log_event("Markdown downloaded")