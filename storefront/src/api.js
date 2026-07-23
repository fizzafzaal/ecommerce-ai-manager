// Single place that knows where the backend lives and how to call it.
// Every page imports these helpers instead of calling fetch() directly,
// so the API base URL and error handling live in exactly one spot.

const API_BASE = "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    // Try to surface the backend's error detail if there is one.
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body; keep the status text
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  // 204 No Content etc. won't have a body.
  if (response.status === 204) return null;
  return response.json();
}

// --- Customers (fake login) ---
export function getCustomers() {
  return request("/customers");
}

// --- Products ---
export function getProducts({ category, search } = {}) {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (search) params.set("search", search);
  const query = params.toString();
  return request(`/products${query ? `?${query}` : ""}`);
}

export function getProduct(id) {
  return request(`/products/${id}`);
}

export function getCategories() {
  return request("/categories");
}

// --- Cart ---
export function getCart(customerId) {
  return request(`/cart?customer_id=${customerId}`);
}

export function addToCart(customerId, productId, quantity = 1) {
  return request("/cart", {
    method: "POST",
    body: JSON.stringify({ customer_id: customerId, product_id: productId, quantity }),
  });
}

export function removeFromCart(itemId) {
  return request(`/cart/${itemId}`, { method: "DELETE" });
}

// --- Orders ---
export function placeOrder(customerId) {
  // No items -> the backend checks out the customer's cart.
  return request("/orders", {
    method: "POST",
    body: JSON.stringify({ customer_id: customerId }),
  });
}

export function getOrders(customerId) {
  return request(`/orders?customer_id=${customerId}`);
}

// --- AI assistant ---
export function sendChat(message, customerId) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message, customer_id: customerId }),
  });
}
