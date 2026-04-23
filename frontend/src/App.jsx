import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Clients from "./pages/Clients";
import "./index.css";

const NAV = [
  { id: "dashboard", label: "Dashboard" },
  { id: "clients", label: "Clients" },
];

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans">
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center gap-8">
        <span className="text-lg font-semibold tracking-tight text-white">
          RateLimiter
        </span>
        <nav className="flex gap-1">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setPage(n.id)}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                page === n.id
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {n.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {page === "dashboard" && <Dashboard />}
        {page === "clients" && <Clients />}
      </main>
    </div>
  );
}
