// Fake login page. The email/password fields are visuals only -- no
// authentication happens. "Sign in" just records which existing customer
// we're shopping as (chosen from the dropdown) and enters the store.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCustomers } from "../api";
import { useCustomer } from "../context/CustomerContext";

function Login() {
  const [customers, setCustomers] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState(null);
  const { login } = useCustomer();
  const navigate = useNavigate();

  useEffect(() => {
    getCustomers()
      .then((data) => {
        setCustomers(data);
        if (data.length > 0) setSelectedId(String(data[0].id));
      })
      .catch((err) => setError(err.message));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const chosen = customers.find((c) => String(c.id) === String(selectedId));
    if (!chosen) return;
    login(chosen);
    navigate("/");
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>🛍️ AI Store</h1>
        <p className="login-sub">Sign in to start shopping</p>
        {error && <p style={{ color: "var(--danger)" }}>Couldn't load customers: {error}</p>}

        <form onSubmit={handleSubmit}>
          {/* Decorative only -- not checked by anything. */}
          <div className="field">
            <label>Email</label>
            <input type="email" placeholder="you@example.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" placeholder="••••••••" />
          </div>

          {/* The real control: which existing customer we shop as. */}
          <div className="field">
            <label>Shop as</label>
            <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  #{c.id} — {c.name}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" disabled={!selectedId}>
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
