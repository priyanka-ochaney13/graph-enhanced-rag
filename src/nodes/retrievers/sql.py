import sqlite3
from pathlib import Path

from src.llm import chat_reasoning

DB_PATH = Path("data/company.db")


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS acquisitions (
            id INTEGER PRIMARY KEY,
            acquirer TEXT, target TEXT, year INTEGER, amount_musd REAL, acl TEXT
        )"""
    )
    conn.execute("DELETE FROM acquisitions")
    conn.executemany(
        "INSERT INTO acquisitions (acquirer, target, year, amount_musd, acl) VALUES (?,?,?,?,?)",
        [
            ("Apple", "Siri", 2010, 200.0, "public"),
            ("Apple", "Beats", 2014, 3000.0, "public"),
            ("Microsoft", "LinkedIn", 2016, 26200.0, "public"),
            ("Google", "DeepMind", 2014, 500.0, "public"),
        ],
    )
    conn.commit()
    return conn


SQL_PROMPT = """Given this question, write a single SQLite SELECT query.
Table: acquisitions(id, acquirer, target, year, amount_musd, acl)
User roles: {roles}
Only return rows where acl IN ({roles}) OR acl = 'public'.
Return ONLY SQL, no markdown.
Question: {question}"""


def retrieve_sql(query: str, user_roles: list[str]) -> list[dict]:
    conn = _ensure_db()
    roles_sql = ",".join(f"'{r}'" for r in user_roles) or "'public'"
    sql = chat_reasoning([
        {"role": "system", "content": "You output only SQLite SELECT statements. No explanations."},
        {"role": "user", "content": SQL_PROMPT.format(roles=roles_sql, question=query)},
    ]).strip().strip("`").removeprefix("sql").strip()

    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    except Exception as e:
        conn.close()
        return [{"text": f"SQL error: {e}", "source": "sql", "doc_id": "sql:error", "score": 0.0, "trust": "trusted_structured"}]

    conn.close()
    text = " | ".join(cols) + "\n" + "\n".join(" | ".join(str(v) for v in row) for row in rows[:20])
    return [{"text": text, "source": "sql", "doc_id": "sql:result", "score": 0.8, "trust": "trusted_structured"}]