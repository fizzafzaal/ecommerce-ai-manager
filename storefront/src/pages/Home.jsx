// Placeholder home page for now -- confirms the login flow lands here
// with the right customer. The real product grid comes in the next step.

import { useCustomer } from "../context/CustomerContext";

function Home() {
  const { customer, logout } = useCustomer();

  return (
    <div>
      <h1>Welcome, {customer.name}</h1>
      <p>You are shopping as customer #{customer.id}.</p>
      <p>(The storefront product grid will appear here next.)</p>
      <button onClick={logout}>Sign out</button>
    </div>
  );
}

export default Home;
