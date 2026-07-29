// Single place that knows where the backend lives and how to call it.
// Every page imports these helpers instead of calling fetch() directly,
// so the API base URL and error handling live in exactly one spot.

// Where the backend lives:
//  - In development, the Vite dev server (port 5173) and the API (port 8000)
//    are separate, so we point at localhost:8000.
//  - In the production build, the FastAPI backend serves this frontend from
//    the SAME origin, so we use relative URLs ("") -- no CORS, one domain.
//  - VITE_API_URL can override both if you ever split them onto two hosts.
const API_BASE =
  import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://localhost:8000" : "");

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

// --- Auth (fake: signup creates a real customer, login matches by email) ---
export function signup(name, email, password) {
  return request("/signup", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}

export function login(email, password) {
  return request("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

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

export function generateMarketing(productId, style) {
  const query = style ? `?style=${encodeURIComponent(style)}` : "";
  return request(`/products/${productId}/marketing${query}`, { method: "POST" });
}

// Direct URL to an order's downloadable invoice image.
export function invoiceUrl(orderId) {
  return `${API_BASE}/orders/${orderId}/invoice`;
}

// Upload an invoice image for verification (multipart form-data, so we
// don't use the JSON `request` helper here).
export async function verifyInvoice(file) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/verify-invoice`, { method: "POST", body: form });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // no JSON body
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json();
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

export function getOrder(orderId) {
  return request(`/orders/${orderId}`);
}

// --- AI assistant ---
export function sendChat(message, customerId, history = []) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message, customer_id: customerId, history }),
  });
}
