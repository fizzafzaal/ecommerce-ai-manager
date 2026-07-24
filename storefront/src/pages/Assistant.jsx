// AI Assistant page: the same multi-agent chat the Streamlit app uses,
// rebuilt as a store page. Sends messages to POST /chat with the logged-in
// customer, and shows a "Thinking..." state (replies run a local model on
// CPU, so they take ~10-40 seconds).

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendChat } from "../api";
import { useCustomer } from "../context/CustomerContext";

const SUGGESTIONS = [
  "What is your return policy?",
  "Do you have any warm winter jackets?",
  "I'm looking for wireless headphones",
];

function Assistant() {
  const { customer } = useCustomer();
  const [messages, setMessages] = useState([]); // { role, content }
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  // Keep the latest message in view.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const send = async (text) => {
    const message = text.trim();
    if (!message || busy) return;

    setMessages((m) => [...m, { role: "user", content: message }]);
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(message, customer.id);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Sorry, something went wrong (${e.message}).` },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="assistant">
      <h1>AI Assistant</h1>
      <p className="assistant-sub">
        Ask about refunds, products, or our policies. Replies run a local AI model on
        CPU, so they take about 10-40 seconds.
      </p>

      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Try asking:</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            {m.role === "assistant" ? (
              <div className="markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
              </div>
            ) : (
              m.content
            )}
          </div>
        ))}

        {busy && <div className="chat-msg assistant thinking">Thinking…</div>}
        <div ref={endRef} />
      </div>

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default Assistant;
