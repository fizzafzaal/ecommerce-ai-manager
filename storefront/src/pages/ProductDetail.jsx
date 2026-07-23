// Product detail page: full info for one product, with an add-to-cart
// control. Reached from the product cards on the home page.

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProduct } from "../api";
import ProductImage from "../components/ProductImage";
import { useCart } from "../context/CartContext";

function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);
  const { addItem } = useCart();

  useEffect(() => {
    setLoading(true);
    getProduct(id)
      .then(setProduct)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleAdd = async () => {
    await addItem(product.id);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p style={{ color: "red" }}>Error: {error}</p>;
  if (!product) return null;

  const outOfStock = product.stock <= 0;

  return (
    <div>
      <Link to="/" className="back-link">
        &larr; Back to store
      </Link>

      <div className="product-detail">
        <ProductImage product={product} className="detail-thumb" />

        <div className="detail-info">
          <p className="product-category">{product.category}</p>
          <h1>{product.name}</h1>
          <span className={`stock ${outOfStock ? "out" : product.low_stock ? "low" : "in"}`}>
            {outOfStock
              ? "Out of stock"
              : product.low_stock
                ? `Only ${product.stock} left in stock`
                : "In stock"}
          </span>
          <p className="product-price product-price-lg">${product.price.toFixed(2)}</p>
          <p className="product-description">{product.description}</p>

          <button disabled={outOfStock} onClick={handleAdd}>
            {added ? "Added ✓" : "Add to cart"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProductDetail;
