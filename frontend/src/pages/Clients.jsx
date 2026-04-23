import { useEffect, useState } from "react";
import {
  getClients,
  createClient,
  updateClient,
  deleteClient,
  fireTestRequest,
} from "../api/client";

const TIERS = ["free", "standard", "premium"];

function TierBadge({ tier }) {
  const cls =
    tier === "premium"
      ? "bg-indigo-900 text-indigo-300"
      : tier === "free"
        ? "bg-gray-800 text-gray-400"
        : "bg-blue-900 text-blue-300";
  return <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>{tier}</span>;
}

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [form, setForm] = useState({ name: "", tier: "standard" });
  const [error, setError] = useState("");
  const [testResults, setTestResults] = useState({});
  const [loading, setLoading] = useState(true);

  const reload = () => getClients().then(setClients).finally(() => setLoading(false));

  useEffect(() => {
    reload();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await createClient(form);
      setForm({ name: "", tier: "standard" });
      reload();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create client");
    }
  };

  const handleToggle = async (client) => {
    await updateClient(client.id, { is_active: !client.is_active });
    reload();
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this client? This removes all request logs too.")) return;
    await deleteClient(id);
    reload();
  };

  const handleTestFire = async (client) => {
    const result = await fireTestRequest(client.api_key);
    setTestResults((prev) => ({ ...prev, [client.id]: result }));
  };

  if (loading) return <p className="text-gray-500 text-sm">Loading...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-white mb-4">Clients</h1>

        <form
          onSubmit={handleCreate}
          className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-wrap gap-3 items-end"
        >
          <div>
            <label className="block text-xs text-gray-400 mb-1">Name</label>
            <input
              className="bg-gray-800 border border-gray-700 text-white rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="my-service"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tier</label>
            <select
              className="bg-gray-800 border border-gray-700 text-white rounded px-3 py-1.5 text-sm focus:outline-none"
              value={form.tier}
              onChange={(e) => setForm((f) => ({ ...f, tier: e.target.value }))}
            >
              {TIERS.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-1.5 rounded transition-colors"
          >
            Add Client
          </button>
          {error && <p className="text-red-400 text-sm w-full">{error}</p>}
        </form>
      </div>

      <div className="space-y-3">
        {clients.length === 0 && <p className="text-gray-500 text-sm">No clients yet. Create one above.</p>}
        {clients.map((c) => (
          <div
            key={c.id}
            className={`bg-gray-900 border rounded-xl p-5 ${c.is_active ? "border-gray-800" : "border-gray-800 opacity-50"}`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{c.name}</span>
                  <TierBadge tier={c.tier} />
                  {!c.is_active && <span className="text-xs text-gray-500 italic">inactive</span>}
                </div>
                <p className="text-xs text-gray-500 font-mono">
                  Key: <span className="text-gray-400">{c.api_key}</span>
                </p>
                {c.rate_config && (
                  <p className="text-xs text-gray-500">
                    Limit: <span className="text-gray-300">{c.rate_config.requests_per_window} req / {c.rate_config.window_seconds}s</span>
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleTestFire(c)}
                  disabled={!c.is_active}
                  className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded transition-colors disabled:opacity-40"
                >
                  Fire request
                </button>
                <button
                  onClick={() => handleToggle(c)}
                  className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded transition-colors"
                >
                  {c.is_active ? "Deactivate" : "Activate"}
                </button>
                <button
                  onClick={() => handleDelete(c.id)}
                  className="text-xs bg-gray-800 hover:bg-red-900 text-gray-400 hover:text-red-300 px-3 py-1.5 rounded transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>

            {testResults[c.id] && (
              <div
                className={`mt-3 text-xs rounded px-3 py-2 font-mono ${
                  testResults[c.id].status === 429 ? "bg-red-950 text-red-300" : "bg-green-950 text-green-300"
                }`}
              >
                Status: {testResults[c.id].status} | Remaining: {testResults[c.id].headers?.["x-ratelimit-remaining"] ?? "-"}
                {testResults[c.id].status === 429 && ` | Retry-After: ${testResults[c.id].headers?.["retry-after"]}s`}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
