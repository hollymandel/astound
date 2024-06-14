import json
import logging
from types import MappingProxyType

with open("data/prompts.json", "r", encoding="UTF-8") as f:
    PROMPTS = MappingProxyType(json.load(f))

MESSAGE_KWARGS = MappingProxyType(
    {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "temperature": 0.0,
        "system": PROMPTS["field_system_prompt"],
        # "api_key": YOUR_API_KEY
    }
)


def type_header(t):
    return (
        f"Which subfields of a python ast node of type {t} contain child nodes? "
        "Return only immediate subfields, i.e. 'subfield' is ok but 'subfield.subsubfield' is not."
    )


def parser_type_query(t: str, anthropic_client, sqlite_conn):
    try:
        cursor = sqlite_conn.cursor()

        cursor.execute("SELECT value FROM subfield_store WHERE key = ?", (t,))
        result = cursor.fetchone()

        if result:
            response = result[0]
        else:
            if anthropic_client is None:
                raise KeyError("unknown type and no anthropic client")
            prompt = type_header(t)

            response = (
                anthropic_client.messages.create(
                    **MESSAGE_KWARGS, messages=[{"role": "user", "content": prompt}]
                )
                .content[0]
                .text
            ).replace(" ", "")

            logging.info("Generated link for type %s:\n%s", t, response)

            cursor.execute(
                """INSERT INTO subfield_store (key, value) VALUES (?, ?)""",
                (t, response),
            )
    finally:
        cursor.close()

    return response