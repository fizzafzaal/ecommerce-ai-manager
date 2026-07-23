// Top-level router. Pages are added here as they're built. Any route
// other than /login requires a "logged in" customer; if there isn't one,
// we redirect to the login page.

import { Navigate, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import { useCustomer } from "./context/CustomerContext";

// Wraps pages that require a logged-in customer.
function RequireLogin({ children }) {
  const { customer } = useCustomer();
  return customer ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireLogin>
            <Home />
          </RequireLogin>
        }
      />
      {/* Unknown routes fall back to home (which itself guards login). */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
