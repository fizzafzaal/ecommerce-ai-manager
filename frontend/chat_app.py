"""Streamlit chat UI for the E-Commerce AI Manager.

Talks to the FastAPI backend over HTTP only -- it never imports the
app package, so the UI stays decoupled from the database and models.

Run (with the API already running) from the project root:
    streamlit run frontend/chat_app.py
"""

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120  # phi on CPU can take 10-40s, especially on a cold load

st.set_page_config(page_title="E-Commerce AI Manager", page_icon="🛍️")


@st.cache_data(show_spinner=False)
def fetch_customers() -> list[dict]:
    """Load the customer list from the API once and cache it."""
    response = requests.get(f"{API_URL}/customers", timeout=10)
    response.raise_for_status()
    return response.json()


def send_message(message: str, customer_id: int) -> dict:
    """POST a message to the backend and return the parsed reply."""
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": message, "customer_id": customer_id},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


st.title("🛍️ E-Commerce AI Manager")
st.caption("A multi-agent assistant for refunds, product search, and FAQs.")

# --- Sidebar: customer picker and API status ---
with st.sidebar:
    st.header("Who are you?")
    try:
        customers = fetch_customers()
    except requests.exceptions.RequestException:
        st.error(
            "Can't reach the backend. Start it first:\n\n"
            "`uvicorn app.main:app`"
        )
        st.stop()

    customer_labels = {f"#{c['id']} — {c['name']}": c["id"] for c in customers}
    selected_label = st.selectbox("Select a customer", list(customer_labels.keys()))
    selected_customer_id = customer_labels[selected_label]

    st.info("Responses run a local model on CPU, so replies take ~10-40 seconds.")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# --- Chat history (kept per session) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat input + response ---
if prompt := st.chat_input("Ask about a refund, a product, or our policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = send_message(prompt, selected_customer_id)
                reply = result["reply"]
            except requests.exceptions.RequestException as e:
                reply = f"Sorry, something went wrong talking to the backend ({e})."
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
