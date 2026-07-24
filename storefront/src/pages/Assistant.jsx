// AI Assistant page: the multi-agent chat, rebuilt as a store page. Sends
// messages (with recent history for context) to POST /chat. The conversation
// lives in ChatContext, so it survives navigating between pages.

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendChat } from "../api";
import { useChat } from "../context/ChatContext";
import { useCustomer } from "../context/CustomerContext";

const SUGGESTIONS = [
  "What is your return policy?",
  "Do you have any warm winter jackets?",
  "I'm looking for wireless headphones",
];

function Assistant() {
  const { customer } = useCustomer();
  const { messages, addMessage, clearChat } = useChat();
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

    // Send the conversation so far as context, then add the new turn.
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    addMessage({ role: "user", content: message });
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(message, customer.id, history);
      addMessage({ role: "assistant", content: res.reply });
    } catch (e) {
      addMessage({ role: "assistant", content: `Sorry, something went wrong (${e.message}).` });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="assistant">
      <div className="assistant-head">
        <div>
          <h1>AI Assistant</h1>
          <p className="assistant-sub">
            Ask about products, your orders, refunds, or our policies.
          </p>
        </div>
        {messages.length > 0 && (
          <button className="clear-chat" onClick={clearChat} disabled={busy}>
            Clear chat
          </button>
        )}
      </div>

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
