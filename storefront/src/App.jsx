// Top-level router. The /login route stands alone; every other route is
// wrapped in RequireLogin + the shared Layout (header + page frame).
// Pages are added under the layout as they're built.

import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
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
        element={
          <RequireLogin>
            <Layout />
          </RequireLogin>
        }
      >
        <Route path="/" element={<Home />} />
      </Route>

      {/* Unknown routes fall back to home (which itself guards login). */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
