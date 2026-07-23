import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { CustomerProvider } from './context/CustomerContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* BrowserRouter enables page navigation; CustomerProvider makes the
        logged-in customer available to every page. */}
    <BrowserRouter>
      <CustomerProvider>
        <App />
      </CustomerProvider>
    </BrowserRouter>
  </StrictMode>,
)
