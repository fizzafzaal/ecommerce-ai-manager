// Storefront home: category filter buttons and a product grid. Each card
// links to the product page and can add the item to the cart.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCategories, getProducts } from "../api";
import ProductImage from "../components/ProductImage";
import { useCart } from "../context/CartContext";
import { useCustomer } from "../context/CustomerContext";

function Home() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addItem } = useCart();
  const { customer } = useCustomer();
  const navigate = useNavigate();

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
          {products.map((p) => (
            <div
              key={p.id}
              className="product-card"
              onClick={() => navigate(`/product/${p.id}`)}
            >
              <ProductImage product={p} className="product-thumb" />
              <div className="product-body">
                <p className="product-category">{p.category}</p>
                <p className="product-name">{p.name}</p>
                <span className={`stock ${p.stock <= 0 ? "out" : p.low_stock ? "low" : "in"}`}>
                  {p.stock <= 0 ? "Out of stock" : p.low_stock ? `Only ${p.stock} left` : "In stock"}
                </span>
                <p className="product-price">${p.price.toFixed(2)}</p>
                <button
                  disabled={p.stock <= 0}
                  onClick={(e) => {
                    e.stopPropagation(); // don't open the product page when adding
                    addItem(p.id);
                  }}
                >
                  Add to cart
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Home;
