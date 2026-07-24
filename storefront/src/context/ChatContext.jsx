// Holds the AI Assistant conversation for the whole app so it survives
// navigating between pages (and a refresh, via sessionStorage). The chat
// resets when the logged-in customer changes.

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useCustomer } from "./CustomerContext";

const ChatContext = createContext(null);
const STORAGE_KEY = "storefront_chat";

export function ChatProvider({ children }) {
  const { customer } = useCustomer();
  const [messages, setMessages] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  });

  // Persist on every change so navigating away and back keeps the chat.
  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  // Clear the conversation if the customer changes (login as someone else,
  // or logout). Doesn't fire on first mount, so a restored chat is kept.
  const prevCustomerId = useRef(customer?.id);
  useEffect(() => {
    if (prevCustomerId.current !== customer?.id) {
      setMessages([]);
      prevCustomerId.current = customer?.id;
    }
  }, [customer?.id]);

  const addMessage = (msg) => setMessages((m) => [...m, msg]);
  const clearChat = () => setMessages([]);

  return (
    <ChatContext.Provider value={{ messages, addMessage, clearChat }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (ctx === null) {
    throw new Error("useChat must be used inside a ChatProvider");
  }
  return ctx;
}
