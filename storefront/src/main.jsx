import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { CustomerProvider } from './context/CustomerContext'
import { CartProvider } from './context/CartContext'
import { ChatProvider } from './context/ChatContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* BrowserRouter enables page navigation; CustomerProvider makes the
        logged-in customer available to every page; CartProvider and
        ChatProvider (inside it, since both belong to a customer) keep the
        cart and the AI conversation alive across page navigation. */}
    <BrowserRouter>
      <CustomerProvider>
        <CartProvider>
          <ChatProvider>
            <App />
          </ChatProvider>
        </CartProvider>
      </CustomerProvider>
    </BrowserRouter>
  </StrictMode>,
)
