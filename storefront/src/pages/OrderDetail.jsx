// Order detail page: full breakdown of one order, with the tracking
// timeline and a link to download the invoice.

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getOrder, invoiceUrl } from "../api";
import TrackingTimeline from "../components/TrackingTimeline";

function OrderDetail() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getOrder(id)
      .then(setOrder)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p>Loading order...</p>;
  if (error) return <p style={{ color: "var(--danger)" }}>Error: {error}</p>;
  if (!order) return null;

  return (
    <div>
      <Link to="/orders" className="back-link">
        &larr; Back to my orders
      </Link>

      <div className="order-detail-head">
        <h1>Order #{order.id}</h1>
        <span className={`order-status ${order.status}`}>{order.status}</span>
      </div>
      <p className="verify-sub">
        Placed on {new Date(order.order_date).toLocaleDateString()}
      </p>

      <div className="detail-card">
        <h3>Delivery status</h3>
        <TrackingTimeline status={order.tracking_status} />
      </div>

      <div className="detail-card">
        <h3>Items</h3>
        <table className="cart-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Qty</th>
              <th>Unit price</th>
              <th>Line total</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((it, i) => (
              <tr key={i}>
                <td>{it.name}</td>
                <td>{it.quantity}</td>
                <td>${it.unit_price.toFixed(2)}</td>
                <td>${it.line_total.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="order-detail-footer">
          <span className="cart-total">Total: ${order.total_amount.toFixed(2)}</span>
          <a className="invoice-link" href={invoiceUrl(order.id)} target="_blank" rel="noreferrer">
            Download invoice
          </a>
        </div>
      </div>
    </div>
  );
}

export default OrderDetail;
