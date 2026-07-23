// Cart page: lists the current cart, lets you remove lines, and places
// the order (which checks stock and decrements inventory on the backend).

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";

function Cart() {
  const { cart, removeItem, checkout } = useCart();
  const navigate = useNavigate();
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState(null);

  const handleCheckout = async () => {
    setPlacing(true);
    setError(null);
    try {
      const order = await checkout();
      // Land on the orders page, flagging the one we just placed.
      navigate("/orders", { state: { justPlaced: order.id } });
    } catch (e) {
      setError(e.message);
    } finally {
      setPlacing(false);
    }
  };

  if (cart.items.length === 0) {
    return (
      <div>
        <h1>Your cart</h1>
        <p>Your cart is empty.</p>
        <Link to="/">Browse products</Link>
      </div>
    );
  }

  return (
    <div>
      <h1>Your cart</h1>

      <table className="cart-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Qty</th>
            <th>Line total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {cart.items.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>${item.price.toFixed(2)}</td>
              <td>{item.quantity}</td>
              <td>${item.line_total.toFixed(2)}</td>
              <td>
                <button className="link-btn" onClick={() => removeItem(item.id)}>
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="cart-summary">
        <span className="cart-total">Total: ${cart.total.toFixed(2)}</span>
        <button onClick={handleCheckout} disabled={placing}>
          {placing ? "Placing order..." : "Place order"}
        </button>
      </div>

      {error && <p style={{ color: "var(--danger)" }}>Could not place order: {error}</p>}
    </div>
  );
}

export default Cart;
