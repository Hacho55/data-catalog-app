# utils/db.py

import os
import pandas as pd
from sqlalchemy import create_engine

def get_pg_engine():
    """
    Create a SQLAlchemy engine using environment variables.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", 5432)
    db_name = os.getenv("DB_NAME")

    url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(url)

def get_column_info(schema: str, table: str) -> pd.DataFrame:
    """
    Execute a system catalog query to retrieve column name, type and description.
    """
    query = f'''
    SELECT
        a.attname AS column_name,
        format_type(a.atttypid, a.atttypmod) AS data_type,
        col_description(a.attrelid, a.attnum) AS description
    FROM
        pg_attribute a
    JOIN
        pg_class c ON a.attrelid = c.oid
    JOIN
        pg_namespace n ON c.relnamespace = n.oid
    WHERE
        c.relname = '{table}'
        AND n.nspname = '{schema}'
        AND a.attnum > 0
        AND NOT a.attisdropped
    ORDER BY
        a.attnum;
    '''

    engine = get_pg_engine()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)