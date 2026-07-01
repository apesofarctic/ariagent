from openai import OpenAI
from . import config

_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


def chat(system: str, user: str, temperature: float = 0.3) -> str:
    """Returns the model's reply, or '' on failure / if LLM disabled (caller falls back)."""
    if not config.USE_LLM:
        return ""
    try:
        resp = _client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temperature,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"[llm] falling back to deterministic text (error: {e})")
        return ""
