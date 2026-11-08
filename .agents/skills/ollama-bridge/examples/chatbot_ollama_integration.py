"""Integration Pattern Example for src/acdp/3_chatbot_mvp.py with Ollama.

Demonstrates:
1. Local embedding with BatchedRetryEmbeddings.
2. Dual-mode LLM client:
   - Google Gemini API (default).
   - Ollama Cloud (via OpenAI client or native Ollama).
   - Ollama Local (via OpenAI client pointing to localhost:11434/v1).
"""

import os
from openai import OpenAI
from langchain_ollama import OllamaEmbeddings


def create_llm_client() -> tuple[str, any]:
    """Returns (provider_type, client_instance).

    Supports:
    - 'gemini': Google GenAI client
    - 'ollama_local': OpenAI SDK pointing to http://localhost:11434/v1
    - 'ollama_cloud': OpenAI SDK pointing to https://ollama.com/v1 with OLLAMA_API_KEY
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama_cloud":
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            raise ValueError(
                "OLLAMA_API_KEY is required for Ollama Cloud. "
                "Run 'ollama signin' or generate a key at https://ollama.com/settings/keys"
            )
        client = OpenAI(
            base_url="https://ollama.com/v1",
            api_key=api_key,
        )
        model = os.getenv("CHAT_MODEL", "gemma4:31b")
        return "ollama_openai", (client, model)

    elif provider == "ollama_local":
        client = OpenAI(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",  # Local Ollama ignores API key
        )
        model = os.getenv("CHAT_MODEL", "qwen2.5:3b")
        return "ollama_openai", (client, model)

    else:
        # Default Gemini setup
        from google import genai
        client = genai.Client()
        model = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
        return "gemini", (client, model)


def call_chat_completion(client_tuple: tuple[str, any], system_prompt: str, messages: list[dict]) -> str:
    """Unified wrapper calling either Gemini or OpenAI-compatible Ollama."""
    provider_type, (client, model) = client_tuple

    if provider_type == "ollama_openai":
        formatted_msgs = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=model,
            messages=formatted_msgs,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    else:
        # Gemini logic
        from google.genai import types as genai_types
        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=m["content"])]))
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=genai_types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2),
        )
        return (response.text or "").strip()

