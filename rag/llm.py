"""LLM client. Works with Groq (cloud) or Ollama (offline) - both speak the
OpenAI chat-completions format, so one function handles both."""
import time
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_URL, LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_URL


class LLMError(Exception):
    pass


def provider_info() -> dict:
    if LLM_PROVIDER == "ollama":
        return {"provider": "ollama", "model": OLLAMA_MODEL, "configured": True}
    return {"provider": "groq", "model": GROQ_MODEL, "configured": bool(GROQ_API_KEY)}


def ask_llm(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    if LLM_PROVIDER == "ollama":
        url, model, headers = OLLAMA_URL, OLLAMA_MODEL, {}
    else:
        if not GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY is not set. Add it to Streamlit Secrets or .env.")
        url, model, headers = GROQ_URL, GROQ_MODEL, {"Authorization": f"Bearer {GROQ_API_KEY}"}

    import httpx

    last_err = None
    for attempt in range(4):
        try:
            resp = httpx.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": 3000,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=180,
            )
        except httpx.HTTPError as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
            continue

        if resp.status_code == 200:
            return (resp.json()["choices"][0]["message"].get("content") or "").strip()

        if resp.status_code in (429, 502, 503):
            retry_after = resp.headers.get("retry-after")
            wait = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else (4 * (attempt + 1))
            last_err = f"{LLM_PROVIDER.title()} error {resp.status_code}: {resp.text[:300]}"
            time.sleep(min(wait, 20))
            continue

        raise LLMError(f"{LLM_PROVIDER.title()} error {resp.status_code}: {resp.text[:300]}")

    where = "Ollama (is `ollama serve` running?)" if LLM_PROVIDER == "ollama" else "Groq"
    raise LLMError(f"Could not reach {where} after retries: {last_err}")
