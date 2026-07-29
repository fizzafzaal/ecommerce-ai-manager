// Verify Invoice page: upload an invoice image; the backend uses Gemini
// (vision) to read it and checks it against the database. Shows one of
// three outcomes -- verified, not verified, or not recognized.

import { useRef, useState } from "react";
import { verifyInvoice } from "../api";

function VerifyInvoice() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setPreview(URL.createObjectURL(f));
  };

  const onVerify = async () => {
    if (!file) return;
    setBusy(true);
    setResult(null);
    try {
      const res = await verifyInvoice(file);
      setResult(res);
    } catch (e) {
      setResult({ status: "error", message: `Something went wrong (${e.message}).` });
    } finally {
      setBusy(false);
    }
  };

  // Map status -> banner style class.
  const statusClass = {
    verified: "ok",
    not_verified: "bad",
    not_recognized: "warn",
    error: "bad",
  };

  return (
    <div className="verify-page">
      <h1>Verify an invoice</h1>
      <p className="verify-sub">
        Upload a ShopSphere invoice image and we'll check it against our records.
      </p>

      <div className="verify-card">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={onPick}
          style={{ display: "none" }}
        />
        <button className="upload-btn" onClick={() => inputRef.current?.click()}>
          {file ? "Choose a different image" : "Choose invoice image"}
        </button>

        {preview && <img src={preview} alt="invoice preview" className="verify-preview" />}

        {file && (
          <button className="verify-btn" onClick={onVerify} disabled={busy}>
            {busy ? "Verifying…" : "Verify invoice"}
          </button>
        )}
      </div>

      {result && (
        <div className={`verify-result ${statusClass[result.status] || "warn"}`}>
          <strong>{result.message}</strong>
          {result.order && (
            <div className="verify-details">
              <div>
                <span>Order</span> #{result.order.order_id}
              </div>
              <div>
                <span>Placed</span> {result.order.date}
              </div>
              <div>
                <span>Customer</span> {result.order.customer}
              </div>
              <div>
                <span>Items</span> {result.order.items.join(", ")}
              </div>
              <div>
                <span>Total</span> ${result.order.total.toFixed(2)}
              </div>
              <div>
                <span>Status</span> {result.order.order_status}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default VerifyInvoice;
