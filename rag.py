"""RAG pipeline: embed guide -> retrieve top-k -> build context -> generate."""
import json
import os
import re

import numpy as np
import ollama
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = "embeddinggemma"
CHAT_MODEL = "qwen3:4b"
KB_PATH = "knowledge_base.json"
TOP_K = 3
THRESHOLD = 0.40  # tune after running test_rag.py 
IDK = "I don't know. The travel guide does not contain this information."

SYSTEM_PROMPT = """You are Lumen Travel's assistant for {city}.
Rules:
1. Answer ONLY with facts written in the guide entries that the user gives you.
2. Cite the ID of every entry you use in square brackets, for example [G03].
3. If the entries do not contain the answer, reply exactly: {idk}
4. Never use outside knowledge and never guess prices, hours or phone numbers.
5. Keep the answer short: 1 to 4 sentences."""


def get_client() -> ollama.Client:
    url = os.getenv("OLLAMA_URL", "").strip()
    if not url:
        raise RuntimeError("OLLAMA_URL is missing in the .env file.")
    return ollama.Client(host=url, timeout=120)


def load_kb(path: str = KB_PATH) -> list:
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    for e in entries:
        for field in ("id", "title", "text", "source"):
            if not e.get(field):
                raise ValueError(f"Entry {e.get('id', '?')} is missing '{field}'.")
    return entries


def _normalize(matrix: np.ndarray) -> np.ndarray:
    return matrix / np.linalg.norm(matrix, axis=-1, keepdims=True)


def embed(client: ollama.Client, texts: list) -> np.ndarray:
    response = client.embed(model=EMBED_MODEL, input=texts)
    return np.array(response["embeddings"], dtype=np.float32)


def build_index(client: ollama.Client, entries: list) -> np.ndarray:
    """Embed the whole guide ONCE. embeddinggemma uses a separate prompt format for documents."""
    docs = [f"title: {e['title']} | text: {e['text']}" for e in entries]
    return _normalize(embed(client, docs))


def retrieve(client, question: str, entries: list, vectors: np.ndarray, k: int = TOP_K) -> list:
    """Return the k entries with the highest cosine similarity, with their scores."""
    q = _normalize(embed(client, [f"task: search result | query: {question}"]))[0]
    scores = vectors @ q  # vectors are normalized -> dot product = cosine similarity
    top = np.argsort(-scores)[:k]
    return [{"entry": entries[i], "score": float(scores[i])} for i in top]


def build_context(hits: list) -> str:
    return "\n\n".join(
        f"[{h['entry']['id']}] {h['entry']['title']}: {h['entry']['text']}" for h in hits
    )


def generate(client, question: str, hits: list, city: str) -> str:
    relevant = [h for h in hits if h["score"] >= THRESHOLD]
    if not relevant:  # Rule 1: no entry is relevant enough -> do not call the LLM
        return IDK

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(city=city, idk=IDK)},
        {"role": "user", "content": f"Guide entries:\n{build_context(relevant)}\n\nQuestion: {question} /no_think"},
    ]
    response = client.chat(
        model=CHAT_MODEL,
        messages=messages,
        think=False,  # turn off qwen3's "thinking" mode
        options={"temperature": 0},
    )
    text = response["message"]["content"]
    # Remove the reasoning block. Some servers drop the opening <think> tag,
    # so also keep only what comes after the last </think>.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = text.split("</think>")[-1].strip()
    return text or IDK


def ask(client, question: str, entries: list, vectors: np.ndarray, city: str):
    """Full pipeline for one question. Returns (answer, list of hits)."""
    hits = retrieve(client, question, entries, vectors)
    return generate(client, question, hits, city), hits