
import { useState, useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";
const LINKS = [
  ["/", "Home"],
  ["/dashboard", "Dashboard"],
  ["/scan", "Messages"],
  ["/reports", "Reports"],
  ["/about", "About"],
];

export default function Layout() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      dark ? "dark" : "light"
    );
  }, [dark]);

  const closeDrawer = () => {
    document.getElementById("nav-drawer").checked = false;
  };

  return (
    <div className="drawer lg:drawer-open">
      <input
        id="nav-drawer"
        type="checkbox"
        className="drawer-toggle"
      />

      <div className="drawer-content min-h-screen bg-base-200">
        <div className="navbar border-b border-base-300 bg-base-100 lg:hidden">
          <label
            htmlFor="nav-drawer"
            className="btn btn-ghost btn-square"
            aria-label="Open menu"
          >
            ☰
          </label>

          <span className="font-heading text-lg font-bold text-white">
            FraudShield
          </span>
        </div>

        <Outlet />
      </div>

      <div className="drawer-side z-10">
        <label
          htmlFor="nav-drawer"
          className="drawer-overlay"
          aria-label="Close menu"
        />

        <aside className="flex min-h-full w-60 flex-col bg-primary p-4 text-primary-content">

          <div className="font-heading px-3 pb-5 font-bold text-white py-6 text-2xl">
            FraudShield
          </div>

          <nav className="grid gap-1">
            {LINKS.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                onClick={closeDrawer}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 font-medium transition text-white ${
                    isActive
                      ? "bg-primary-content/15" 
                      : "hover:bg-primary-content/10 hover:opacity-200 "
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>

          <button
            onClick={() => setDark((prev) => !prev)}
            className="btn btn-ghost mt-auto justify-start text-primary-content"
          >
            {dark ? "☀️ Light Mode" : "🌙 Dark Mode"}
          </button>

        </aside>
      </div>
    </div>
  );
}
