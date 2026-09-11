import contextvars
from openai import OpenAI
from . import config

_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)

# per-task override so a ?mode=scripted stream stays fully deterministic even
# when USE_LLM=true globally
llm_off = contextvars.ContextVar("llm_off", default=False)


def chat(system: str, user: str, temperature: float = 0.3) -> str:
    """Returns the model's reply, or '' on failure / if LLM disabled (caller falls back)."""
    if not config.USE_LLM or llm_off.get():
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
