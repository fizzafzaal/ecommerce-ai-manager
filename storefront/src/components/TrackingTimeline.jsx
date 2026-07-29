// A simple order tracking timeline: Placed -> Processing -> Shipped ->
// Delivered, with completed/current stages highlighted. For refunded or
// cancelled orders it shows that terminal state instead.

const STAGES = ["Placed", "Processing", "Shipped", "Delivered"];

function TrackingTimeline({ status }) {
  // Terminal states that aren't part of the normal delivery flow.
  if (status === "Refunded" || status === "Cancelled") {
    return <div className={`tracking-terminal ${status.toLowerCase()}`}>{status}</div>;
  }

  const currentIndex = STAGES.indexOf(status);

  return (
    <div className="tracking">
      {STAGES.map((stage, i) => (
        <div
          key={stage}
          className={`tracking-step ${i <= currentIndex ? "done" : ""} ${
            i === currentIndex ? "current" : ""
          }`}
        >
          <span className="tracking-dot" />
          <span className="tracking-label">{stage}</span>
        </div>
      ))}
    </div>
  );
}

export default TrackingTimeline;
