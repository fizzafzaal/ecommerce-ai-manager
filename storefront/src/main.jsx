import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { CustomerProvider } from './context/CustomerContext'
import { CartProvider } from './context/CartContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* BrowserRouter enables page navigation; CustomerProvider makes the
        logged-in customer available to every page; CartProvider (inside it,
        since the cart belongs to a customer) tracks the cart. */}
    <BrowserRouter>
      <CustomerProvider>
        <CartProvider>
          <App />
        </CartProvider>
      </CustomerProvider>
    </BrowserRouter>
  </StrictMode>,
)
