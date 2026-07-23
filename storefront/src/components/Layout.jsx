// Shared page frame: the header on top, then the active page's content.
// Used as the element for all logged-in routes; <Outlet /> renders the
// matched child page.

import { Outlet } from "react-router-dom";
import Header from "./Header";

function Layout() {
  return (
    <div className="app-shell">
      <Header />
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
