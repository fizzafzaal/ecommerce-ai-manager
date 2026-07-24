// Auth page with two modes: Log in (match an existing customer by email)
// and Sign up (create a new customer in the database). Login is fake --
// passwords are never checked -- but signup really does add the customer,
// so each person shops as their own account.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login as apiLogin, signup as apiSignup } from "../api";
import { useCustomer } from "../context/CustomerContext";

function Login() {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const { login } = useCustomer();
  const navigate = useNavigate();

  const isSignup = mode === "signup";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const customer = isSignup
        ? await apiSignup(name, email, password)
        : await apiLogin(email, password);
      login(customer);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const switchMode = () => {
    setMode(isSignup ? "login" : "signup");
    setError(null);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>🛍️ ShopSphere</h1>
        <p className="login-sub">
          {isSignup ? "Create your account to start shopping" : "Sign in to your account"}
        </p>

        {error && <p className="form-error">{error}</p>}

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <div className="field">
              <label>Full name</label>
              <input
                type="text"
                placeholder="Jane Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="field">
            <label>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" disabled={busy}>
            {busy ? "Please wait..." : isSignup ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="login-switch">
          {isSignup ? "Already have an account?" : "New here?"}{" "}
          <button type="button" className="link-btn" onClick={switchMode}>
            {isSignup ? "Log in" : "Create one"}
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;
