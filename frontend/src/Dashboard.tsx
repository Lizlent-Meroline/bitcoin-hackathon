/**
 * Page 1 — Producer Dashboard
 * Live sats counter, payment history table, earnings chart.
 * All driven by Socket.IO events from the backend.
 */
import { useEffect, useRef, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getStats, getPayments, type Payment, type Producer } from "./api";
import { getSocket, subscribeToMeter } from "./socket";
import PaymentModal, { type InvoiceEvent } from "./Payment";

interface ChartPoint {
  time: string;
  sats: number;
}

interface Props {
  producer: Producer;
  onLogout: () => void;
}

export default function Dashboard({ producer, onLogout }: Props) {
  const [totalSats, setTotalSats] = useState(0);
  const [totalKwh, setTotalKwh] = useState(0);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [liveEvent, setLiveEvent] = useState<InvoiceEvent | null>(null);
  const [paidReadingId, setPaidReadingId] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const latestSats = useRef(0);

  // ---------- Load initial data ----------
  useEffect(() => {
    const load = async () => {
      try {
        const [stats, pmts] = await Promise.all([
          getStats(producer.meter_id),
          getPayments(producer.meter_id),
        ]);
        setTotalSats(stats.total_sats);
        setTotalKwh(stats.total_kwh);
        latestSats.current = stats.total_sats;
        setPayments(pmts);
        setChartData(
          stats.history.map((h) => ({
            time: h.paid_at
              ? new Date(h.paid_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "—",
            sats: h.sats,
          }))
        );
      } catch (e) {
        console.error("Failed to load stats", e);
      }
    };
    load();
  }, [producer.meter_id]);

  // ---------- Socket.IO live updates ----------
  useEffect(() => {
    const socket = getSocket();

    socket.on("connect", () => {
      setConnected(true);
      subscribeToMeter(producer.meter_id);
    });

    socket.on("disconnect", () => setConnected(false));

    socket.on("new_invoice", (data: InvoiceEvent) => {
      if (data.meter_id === producer.meter_id) {
        setLiveEvent(data);
        setPaidReadingId(null);
      }
    });

    socket.on(
      "payment",
      (data: {
        reading_id: string;
        meter_id: string;
        sats: number;
        kwh: number;
        status: string;
        timestamp: string;
      }) => {
        if (data.meter_id !== producer.meter_id) return;
        if (data.status !== "settled") return;

        // Mark invoice as paid
        setPaidReadingId(data.reading_id);

        // Update counters
        const newSats = latestSats.current + data.sats;
        latestSats.current = newSats;
        setTotalSats(newSats);
        setTotalKwh((k) => k + data.kwh);

        // Add chart point
        const time = new Date(data.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
        setChartData((prev) => [...prev.slice(-19), { time, sats: data.sats }]);

        // Prepend to payment list
        setPayments((prev) => [
          {
            id: Date.now(),
            reading_id: data.reading_id,
            meter_id: data.meter_id,
            sats_amount: data.sats,
            kwh_amount: data.kwh,
            status: "settled",
            lightning_address: producer.lightning_address,
            invoice_request: null,
            paid_at: data.timestamp,
            created_at: data.timestamp,
          },
          ...prev.slice(0, 49),
        ]);
      }
    );

    if (socket.connected) {
      setConnected(true);
      subscribeToMeter(producer.meter_id);
    }

    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("new_invoice");
      socket.off("payment");
    };
  }, [producer.meter_id, producer.lightning_address]);

  const isPaid = liveEvent != null && paidReadingId === liveEvent.reading_id;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">☀️⚡</span>
          <div>
            <h1 className="font-bold text-yellow-400 text-lg leading-none">SolarSats</h1>
            <p className="text-gray-500 text-xs">{producer.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div
              className={`w-2 h-2 rounded-full ${connected ? "bg-green-500 animate-pulse" : "bg-red-500"}`}
            />
            <span className="text-xs text-gray-500">
              {connected ? "Live" : "Offline"}
            </span>
          </div>
          <button
            onClick={onLogout}
            className="text-gray-500 hover:text-gray-300 text-sm transition"
          >
            Switch Meter
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            label="Total Earned"
            value={`${totalSats.toLocaleString()} sats`}
            sub={`≈ ${(totalSats / 100_000_000).toFixed(8)} BTC`}
            accent="yellow"
          />
          <StatCard
            label="Energy Sold"
            value={`${totalKwh.toFixed(3)} kWh`}
            sub="from your solar panels"
            accent="green"
          />
          <StatCard
            label="Meter ID"
            value={producer.meter_id}
            sub={producer.lightning_address}
            accent="blue"
          />
        </div>

        {/* Earnings chart */}
        {chartData.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-gray-300 font-semibold mb-4">Sats per Reading</h2>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="satsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#eab308" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#eab308" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
                <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                  labelStyle={{ color: "#9ca3af" }}
                  itemStyle={{ color: "#eab308" }}
                  formatter={(v) => [`${v ?? 0} sats`, "Earned"] as [string, string]}
                />
                <Area
                  type="monotone"
                  dataKey="sats"
                  stroke="#eab308"
                  strokeWidth={2}
                  fill="url(#satsGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Payment history table */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-gray-300 font-semibold">Payment History</h2>
            <span className="text-gray-600 text-sm">{payments.length} payments</span>
          </div>
          {payments.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-600">
              <p className="text-4xl mb-3">⚡</p>
              <p>Waiting for your first meter reading…</p>
              <p className="text-sm mt-1">Start the meter simulator to see sats flow!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-xs border-b border-gray-800">
                    <th className="px-4 py-3 text-left">Time</th>
                    <th className="px-4 py-3 text-right">kWh</th>
                    <th className="px-4 py-3 text-right">Sats</th>
                    <th className="px-4 py-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((p) => (
                    <tr
                      key={p.id}
                      className="border-b border-gray-800/50 hover:bg-gray-800/30 transition"
                    >
                      <td className="px-4 py-3 text-gray-400">
                        {p.paid_at
                          ? new Date(p.paid_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-300">
                        {p.kwh_amount.toFixed(4)}
                      </td>
                      <td className="px-4 py-3 text-right text-yellow-400 font-mono font-semibold">
                        +{p.sats_amount}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            p.status === "settled"
                              ? "bg-green-900/50 text-green-400"
                              : p.status === "pending"
                              ? "bg-yellow-900/50 text-yellow-400"
                              : "bg-red-900/50 text-red-400"
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Invoice modal */}
      {liveEvent && (
        <PaymentModal
          event={liveEvent}
          isPaid={isPaid}
          onDismiss={() => setLiveEvent(null)}
        />
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub: string;
  accent: "yellow" | "green" | "blue";
}) {
  const colors = {
    yellow: "border-yellow-500/20 text-yellow-400",
    green: "border-green-500/20 text-green-400",
    blue: "border-blue-500/20 text-blue-400",
  };
  return (
    <div className={`bg-gray-900 border rounded-xl p-5 ${colors[accent]}`}>
      <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold font-mono ${colors[accent]}`}>{value}</p>
      <p className="text-gray-600 text-xs mt-1 truncate">{sub}</p>
    </div>
  );
}
