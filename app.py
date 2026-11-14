"""Lumen Travel - Sign-in Travel Assistant with RAG Chat."""
import os

import streamlit as st

import rag
from firebase_client import AuthError, sign_in, sign_up

CITY = "Long Xuyen"

st.set_page_config(page_title="Lumen Travel", page_icon="🧭")

# ---------- Session memory (survives Streamlit reruns) ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------- Embed the guide ONCE and reuse it for every question ----------
@st.cache_resource(show_spinner="Embedding the travel guide (only once)...")
def load_index(kb_mtime: float):
    # kb_mtime: when you edit knowledge_base.json this value changes -> re-embed automatically
    client = rag.get_client()
    entries = rag.load_kb()
    vectors = rag.build_index(client, entries)
    return client, entries, vectors


def show_sources(hits: list):
    with st.expander(f"📚 Sources: {len(hits)} retrieved guide entries"):
        for h in hits:
            e, score = h["entry"], h["score"]
            status = "✅ used" if score >= rag.THRESHOLD else "⛔ below threshold, not used"
            st.markdown(f"**[{e['id']}] {e['title']}** · score `{score:.3f}` · {status}")
            st.caption(e["text"])
            st.caption(f"Source: {e['source']}")


# ---------- Sign-in / sign-up page ----------
def handle_auth(action, email: str, password: str):
    if not email.strip() or not password:
        st.error("Please enter both email and password.")
        return
    try:
        st.session_state.user = action(email.strip(), password)
    except AuthError as err:
        st.error(str(err))
        return
    st.session_state.messages = []
    st.rerun()


def auth_page():
    st.title("🧭 Lumen Travel")
    st.write(f"Sign in to chat with the **{CITY}** travel assistant.")
    tab_in, tab_up = st.tabs(["Sign in", "Sign up"])

    with tab_in:
        with st.form("signin_form"):
            email = st.text_input("Email", key="signin_email")
            password = st.text_input("Password", type="password", key="signin_pw")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            handle_auth(sign_in, email, password)

    with tab_up:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (at least 6 characters)", type="password", key="signup_pw")
            confirm = st.text_input("Confirm password", type="password", key="signup_pw2")
            submitted = st.form_submit_button("Create account")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                handle_auth(sign_up, email, password)


# ---------- Chat page (shown only after sign-in) ----------
def chat_page():
    with st.sidebar:
        st.markdown(f"Signed in as **{st.session_state.user['email']}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state.clear()  # clears the user and the whole chat history
            st.rerun()
        st.divider()
        st.caption(f"Chat model: {rag.CHAT_MODEL}")
        st.caption(f"Embedding model: {rag.EMBED_MODEL}")
        st.caption(f"top-k = {rag.TOP_K} · threshold = {rag.THRESHOLD}")

    st.title(f"🧭 {CITY} Travel Assistant")
    st.caption("Answers come only from our travel guide. Sources are shown under each answer.")

    try:
        client, entries, vectors = load_index(os.path.getmtime(rag.KB_PATH))
    except Exception as err:
        st.error("Cannot reach the Ollama server. Check OLLAMA_URL in .env and make sure Pinggy is running.")
        st.caption(f"Details: {err}")
        st.stop()

    # Show the chat history of this session again
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("hits"):
                show_sources(msg["hits"])

    question = st.chat_input("Ask about the city, e.g. When is the floating market busiest?")
    if question is None:
        return
    if not question.strip():
        st.warning("Please type a question first.")
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching the travel guide..."):
                answer, hits = rag.ask(client, question, entries, vectors, CITY)
        except Exception as err:
            st.error("Cannot reach the Ollama server right now. Check Pinggy / OLLAMA_URL and try again.")
            st.caption(f"Details: {err}")
            return
        st.markdown(answer)
        show_sources(hits)

    st.session_state.messages.append({"role": "assistant", "content": answer, "hits": hits})


# ---------- Routing: no chat before sign-in ----------
if st.session_state.user:
    chat_page()
else:
    auth_page()