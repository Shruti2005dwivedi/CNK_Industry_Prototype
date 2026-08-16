"""
Generation & Citation Module
-------------------------------
Builds a context-grounded prompt from retrieved chunks and calls the
configured LLM (Groq or Gemini). The model is instructed to answer only
from the provided context and to cite (document, section, date) for
every claim; if retrieval came back empty/weak, we skip the LLM call
entirely and return the "not found" response -- cheaper and safer than
letting the model guess.

Swap in OpenAI by adding a third branch in `call_llm` -- everything
else in the pipeline is provider-agnostic.
"""
from app.config import settings

NOT_FOUND_MESSAGE = (
    "This isn't covered in the indexed sources I have access to. "
    "Try rephrasing, or ingest the relevant circular/notification first."
)

SYSTEM_PROMPT = """You are a tax & regulatory research assistant for internal auditors and tax consultants.
Rules:
1. Answer ONLY using the CONTEXT provided below. Do not use outside knowledge.
2. Every factual claim must end with an inline citation in the form [Source: <document>, <section>, <date>].
3. If the context does not contain enough information to answer, respond with exactly:
   "NOT_FOUND_IN_SOURCES"
4. Be precise and concise. Do not speculate.
"""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        m = c["metadata"]
        header = f'[Source: {m.get("source_document")}, {m.get("section_reference", "Unknown")}, {m.get("date_of_issue", "Unknown")}]'
        parts.append(f"{header}\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def call_llm(query: str, chunks: list[dict]) -> str:
    context = _build_context(chunks)
    user_prompt = f"CONTEXT:\n{context}\n\nQUESTION: {query}\n\nANSWER:"

    if settings.llm_provider == "groq":
        return _call_groq(user_prompt)
    elif settings.llm_provider == "gemini":
        return _call_gemini(user_prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


def _call_groq(user_prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=800,
    )
    return resp.choices[0].message.content.strip()


def _call_gemini(user_prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model, system_instruction=SYSTEM_PROMPT
    )
    resp = model.generate_content(user_prompt)
    return resp.text.strip()


def generate_answer(query: str, chunks: list[dict]) -> tuple[str, bool]:
    """Returns (answer_text, grounded: bool)."""
    if not chunks:
        return NOT_FOUND_MESSAGE, False

    raw = call_llm(query, chunks)
    if "NOT_FOUND_IN_SOURCES" in raw:
        return NOT_FOUND_MESSAGE, False
    return raw, True
