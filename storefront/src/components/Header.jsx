// Site header shown on every store page: brand, navigation, a live cart
// count, the current customer, and sign out.

import { Link } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useCustomer } from "../context/CustomerContext";

function Header() {
  const { customer, logout } = useCustomer();
  const { count } = useCart();

  return (
    <header className="site-header">
      <Link to="/" className="brand">
        🛍️ ShopSphere
      </Link>

      <nav className="site-nav">
        <Link to="/">Home</Link>
        <Link to="/orders">My Orders</Link>
        <Link to="/verify">Verify Invoice</Link>
        <Link to="/assistant">AI Assistant</Link>
        <Link to="/cart" className="cart-link">
          Cart ({count})
        </Link>
      </nav>

      <div className="header-user">
        <span>{customer?.name}</span>
        <button onClick={logout}>Sign out</button>
      </div>
    </header>
  );
}

export default Header;
