// Orders page: a customer's order history, newest first. Doubles as the
// order-confirmation screen -- right after checkout the Cart page sends
// us here with the new order id, which we highlight.

import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { getOrders } from "../api";
import { useCustomer } from "../context/CustomerContext";

function Orders() {
  const { customer } = useCustomer();
  const location = useLocation();
  const justPlaced = location.state?.justPlaced;

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOrders(customer.id)
      .then(setOrders)
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, [customer.id]);

  if (loading) return <p>Loading your orders...</p>;

  return (
    <div>
      <h1>My Orders</h1>

      {justPlaced && (
        <p className="confirmation">
          🎉 Order #{justPlaced} placed successfully! Thank you for your purchase.
        </p>
      )}

      {orders.length === 0 ? (
        <p>
          You haven't placed any orders yet. <Link to="/">Start shopping</Link>.
        </p>
      ) : (
        <div className="order-list">
          {orders.map((order) => (
            <div
              key={order.id}
              className={`order-card ${order.id === justPlaced ? "highlight" : ""}`}
            >
              <div className="order-head">
                <strong>Order #{order.id}</strong>
                <span>{new Date(order.order_date).toLocaleDateString()}</span>
                <span className={`order-status ${order.status}`}>{order.status}</span>
              </div>
              <ul className="order-items">
                {order.items.map((item, i) => (
                  <li key={i}>
                    {item.quantity} &times; {item.name} — ${item.line_total.toFixed(2)}
                  </li>
                ))}
              </ul>
              <div className="order-total">Total: ${order.total_amount.toFixed(2)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Orders;
