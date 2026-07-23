// Holds the current customer's cart for the whole app, so the header can
// show a live item count and any page can add/remove/checkout. The cart
// itself lives server-side; this context mirrors it and refreshes from
// the backend after each change.

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  addToCart,
  getCart,
  placeOrder as apiPlaceOrder,
  removeFromCart,
} from "../api";
import { useCustomer } from "./CustomerContext";

const CartContext = createContext(null);

const EMPTY_CART = { items: [], total: 0 };

export function CartProvider({ children }) {
  const { customer } = useCustomer();
  const [cart, setCart] = useState(EMPTY_CART);

  const refreshCart = useCallback(async () => {
    if (!customer) {
      setCart(EMPTY_CART);
      return;
    }
    try {
      setCart(await getCart(customer.id));
    } catch {
      setCart(EMPTY_CART);
    }
  }, [customer]);

  // Load (or clear) the cart whenever the logged-in customer changes.
  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addItem = async (productId, quantity = 1) => {
    const updated = await addToCart(customer.id, productId, quantity);
    setCart(updated);
    return updated;
  };

  const removeItem = async (itemId) => {
    const updated = await removeFromCart(itemId);
    setCart(updated);
    return updated;
  };

  const checkout = async () => {
    const order = await apiPlaceOrder(customer.id);
    await refreshCart(); // the backend clears the cart on checkout
    return order;
  };

  const count = cart.items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <CartContext.Provider value={{ cart, count, refreshCart, addItem, removeItem, checkout }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (ctx === null) {
    throw new Error("useCart must be used inside a CartProvider");
  }
  return ctx;
}
