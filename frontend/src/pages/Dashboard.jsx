import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { getSummary, getTimeline, getThrottledClients } from "../api/client";

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-3xl font-bold ${accent || "text-white"}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [throttled, setThrottled] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [s, t, th] = await Promise.all([
        getSummary(),
        getTimeline(30),
        getThrottledClients(),
      ]);
      setSummary(s);
      setTimeline(t);
      setThrottled(th);
      setError("");
    } catch (err) {
      setError(err.response?.data?.error || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, []);

  if (loading) {
    return <p className="text-gray-500 text-sm">Loading dashboard...</p>;
  }

  if (error) {
    return <p className="text-red-400 text-sm">{error}</p>;
  }

  const { last_60_min, active_clients } = summary;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-white mb-4">
          Overview <span className="text-xs text-gray-500 font-normal ml-1">last 60 min | auto-refreshes</span>
        </h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Requests" value={last_60_min.total_requests} />
          <StatCard label="Throttled" value={last_60_min.throttled_requests} accent="text-red-400" />
          <StatCard
            label="Throttle Rate"
            value={`${last_60_min.throttle_rate_pct}%`}
            accent={last_60_min.throttle_rate_pct > 10 ? "text-yellow-400" : "text-green-400"}
          />
          <StatCard label="Active Clients" value={active_clients} accent="text-indigo-400" />
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-4">Requests / minute (last 30 min)</h2>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }} />
            <Legend />
            <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} dot={false} name="Total" />
            <Line
              type="monotone"
              dataKey="throttled"
              stroke="#f87171"
              strokeWidth={2}
              dot={false}
              name="Throttled"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {throttled.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-gray-400 mb-4">Most Throttled Clients</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-800">
                <th className="pb-2">Client</th>
                <th className="pb-2">Tier</th>
                <th className="pb-2 text-right">Throttled (1h)</th>
              </tr>
            </thead>
            <tbody>
              {throttled.map((c) => (
                <tr key={c.id} className="border-b border-gray-800/50">
                  <td className="py-2 text-white">{c.name}</td>
                  <td className="py-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        c.tier === "premium"
                          ? "bg-indigo-900 text-indigo-300"
                          : c.tier === "free"
                            ? "bg-gray-800 text-gray-400"
                            : "bg-blue-900 text-blue-300"
                      }`}
                    >
                      {c.tier}
                    </span>
                  </td>
                  <td className="py-2 text-right text-red-400 font-mono">{c.throttled_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
