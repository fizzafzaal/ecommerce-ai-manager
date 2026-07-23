// Holds the "logged in" customer for the whole app. Login here is fake
// (visuals only) -- it just remembers which existing customer we're
// shopping as. Stored in localStorage so a page refresh keeps you in.

import { createContext, useContext, useEffect, useState } from "react";

const CustomerContext = createContext(null);

const STORAGE_KEY = "storefront_customer";

export function CustomerProvider({ children }) {
  const [customer, setCustomer] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  });

  // Keep localStorage in sync whenever the logged-in customer changes.
  useEffect(() => {
    if (customer) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(customer));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [customer]);

  const login = (selectedCustomer) => setCustomer(selectedCustomer);
  const logout = () => setCustomer(null);

  return (
    <CustomerContext.Provider value={{ customer, login, logout }}>
      {children}
    </CustomerContext.Provider>
  );
}

// Convenience hook so pages can do: const { customer, login, logout } = useCustomer();
export function useCustomer() {
  const ctx = useContext(CustomerContext);
  if (ctx === null) {
    throw new Error("useCustomer must be used inside a CustomerProvider");
  }
  return ctx;
}
