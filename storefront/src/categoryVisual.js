// Products have no photos, so each category gets a simple visual identity
// -- an emoji on a soft tinted gradient -- used as the "product image" on
// cards and the detail page. Keeps the store looking like a store without
// needing real image assets.

const VISUALS = {
  Clothing: { emoji: "🧥", from: "#dbeafe", to: "#eff6ff" },
  Electronics: { emoji: "🎧", from: "#ede9fe", to: "#f5f3ff" },
  "Home & Kitchen": { emoji: "🍳", from: "#fef3c7", to: "#fffbeb" },
  "Sports & Outdoors": { emoji: "🏕️", from: "#dcfce7", to: "#f0fdf4" },
  "Beauty & Personal Care": { emoji: "💄", from: "#fce7f3", to: "#fdf2f8" },
};

const FALLBACK = { emoji: "🛍️", from: "#e2e8f0", to: "#f8fafc" };

export function categoryVisual(category) {
  return VISUALS[category] || FALLBACK;
}
