// Stage B skeleton: prove the React app can reach the FastAPI backend.
// Intentionally plain -- it just fetches products and lists them. Styling
// and real pages come in later stages.

import { useEffect, useState } from "react";
import { getProducts } from "./api";

function App() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch the product list once when the page loads.
  useEffect(() => {
    getProducts()
      .then((data) => setProducts(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading products...</p>;
  if (error) return <p style={{ color: "red" }}>Error: {error}</p>;

  return (
    <div>
      <h1>Storefront (skeleton)</h1>
      <p>{products.length} products loaded from the backend:</p>
      <ul>
        {products.map((p) => (
          <li key={p.id}>
            {p.name} — ${p.price} — stock {p.stock}
            {p.low_stock ? " (low)" : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
