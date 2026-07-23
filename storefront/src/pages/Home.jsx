// Storefront home: category filter buttons and a product grid. Each card
// links to the product page and can add the item to the cart.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCategories, getProducts } from "../api";
import { categoryVisual } from "../categoryVisual";
import { useCart } from "../context/CartContext";
import { useCustomer } from "../context/CustomerContext";

function Home() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addItem } = useCart();
  const { customer } = useCustomer();

  // Categories load once.
  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
  }, []);

  // Products reload whenever the active category changes.
  useEffect(() => {
    setLoading(true);
    getProducts({ category: activeCategory })
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [activeCategory]);

  return (
    <div>
      <div className="hero">
        <h1>Welcome back, {customer.name.split(" ")[0]} 👋</h1>
        <p>Browse our collection and check out with a single click.</p>
      </div>

      <div className="category-bar">
        <button
          className={activeCategory === null ? "active" : ""}
          onClick={() => setActiveCategory(null)}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c}
            className={activeCategory === c ? "active" : ""}
            onClick={() => setActiveCategory(c)}
          >
            {c}
          </button>
        ))}
      </div>

      {loading ? (
        <p>Loading products...</p>
      ) : (
        <div className="product-grid">
          {products.map((p) => {
            const visual = categoryVisual(p.category);
            return (
              <div key={p.id} className="product-card">
                <Link
                  to={`/product/${p.id}`}
                  className="product-thumb"
                  style={{ background: `linear-gradient(135deg, ${visual.from}, ${visual.to})` }}
                >
                  {visual.emoji}
                </Link>
                <div className="product-body">
                  <p className="product-category">{p.category}</p>
                  <Link to={`/product/${p.id}`} className="product-name">
                    {p.name}
                  </Link>
                  <span className={`stock ${p.stock <= 0 ? "out" : p.low_stock ? "low" : "in"}`}>
                    {p.stock <= 0 ? "Out of stock" : p.low_stock ? `Only ${p.stock} left` : "In stock"}
                  </span>
                  <p className="product-price">${p.price.toFixed(2)}</p>
                  <button disabled={p.stock <= 0} onClick={() => addItem(p.id)}>
                    Add to cart
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Home;
