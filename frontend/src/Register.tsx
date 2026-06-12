/**
 * Page 3 — Onboarding
 * Producer pastes their Lightning address and meter ID, clicks Register.
 */
import { useState } from "react";
import { registerProducer, type Producer } from "./api";

interface Props {
  onRegistered: (producer: Producer) => void;
}

export default function Register({ onRegistered }: Props) {
  const [form, setForm] = useState({
    name: "",
    meter_id: "",
    lightning_address: "",
    node_pubkey: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const producer = await registerProducer({
        name: form.name,
        meter_id: form.meter_id,
        lightning_address: form.lightning_address,
        node_pubkey: form.node_pubkey || undefined,
      });
      onRegistered(producer);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-yellow-500/20 rounded-2xl p-8 w-full max-w-md shadow-2xl">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-2">☀️⚡</div>
          <h1 className="text-3xl font-bold text-yellow-400">SolarSats</h1>
          <p className="text-gray-400 mt-1 text-sm">
            Sell your solar power. Get paid in sats. Instantly.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">
              Your Name
            </label>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              placeholder="Alice Odhiambo"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">
              Meter ID
            </label>
            <input
              name="meter_id"
              value={form.meter_id}
              onChange={handleChange}
              required
              placeholder="METER001"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">
              Lightning Address
            </label>
            <input
              name="lightning_address"
              value={form.lightning_address}
              onChange={handleChange}
              required
              placeholder="alice@getalby.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition"
            />
            <p className="text-xs text-gray-500 mt-1">
              Your Alby, Wallet of Satoshi, or any Lightning address
            </p>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">
              LND Node Pubkey{" "}
              <span className="text-gray-500 font-normal">(optional)</span>
            </label>
            <input
              name="node_pubkey"
              value={form.node_pubkey}
              onChange={handleChange}
              placeholder="02abc123..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500 transition"
            />
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-500/30 text-red-400 rounded-lg p-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-yellow-500 hover:bg-yellow-400 disabled:opacity-50 text-gray-950 font-bold py-3 rounded-lg transition text-lg"
          >
            {loading ? "Registering…" : "Register as Producer ⚡"}
          </button>
        </form>

        <p className="text-center text-gray-600 text-xs mt-6">
          50 sats per kWh · No middleman · Instant settlement
        </p>
      </div>
    </div>
  );
}
