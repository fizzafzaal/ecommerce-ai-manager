// Storefront home: category filter buttons and a product grid. Each card
// links to the product page and can add the item to the cart.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCategories, getProducts } from "../api";
import { useCart } from "../context/CartContext";

function Home() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addItem } = useCart();

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
      <h1>Products</h1>

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
          {products.map((p) => (
            <div key={p.id} className="product-card">
              <Link to={`/product/${p.id}`} className="product-name">
                {p.name}
              </Link>
              <p className="product-category">{p.category}</p>
              <p className="product-price">${p.price.toFixed(2)}</p>
              <p className={`stock ${p.stock <= 0 ? "out" : p.low_stock ? "low" : "in"}`}>
                {p.stock <= 0 ? "Out of stock" : p.low_stock ? `Only ${p.stock} left` : "In stock"}
              </p>
              <button disabled={p.stock <= 0} onClick={() => addItem(p.id)}>
                Add to cart
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Home;
