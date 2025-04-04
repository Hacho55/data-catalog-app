import pandas as pd
from sqlalchemy import text


def get_column_info(engine, schema: str, table: str) -> pd.DataFrame:
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
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def suggest_comment(column_name: str, data_type: str, template: str, llm) -> str:
    prompt = template.format(column_name=column_name, data_type=data_type)
    response = llm.invoke(prompt).content.strip().strip("\"").strip("'")
    return response


def build_comment_sql(df: pd.DataFrame, schema: str, table: str, log: list) -> list:
    sql_statements = []
    for _, row in df.iterrows():
        comment = row['final_comment']
        if comment and isinstance(comment, str):
            escaped = comment.replace("'", "''")
            stmt = f"COMMENT ON COLUMN {schema}.{table}.{row['column_name']} IS '{escaped}';"
            sql_statements.append(stmt)
            log.append(f"Generated SQL: {stmt}")
    return sql_statements