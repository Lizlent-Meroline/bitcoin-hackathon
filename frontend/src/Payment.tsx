/**
 * Page 2 — Invoice / QR Screen
 * Shown when a new kWh event fires. Displays QR + countdown.
 * Turns green when the WebSocket confirms settlement.
 */
import { useEffect, useState } from "react";
import { QRCodeSVG as QRCode } from "qrcode.react";

export interface InvoiceEvent {
  reading_id: string;
  meter_id: string;
  sats: number;
  kwh: number;
  invoice: string;
  producer_name: string;
  timestamp: string;
}

interface Props {
  event: InvoiceEvent;
  isPaid: boolean;
  onDismiss: () => void;
}

const EXPIRY_SECONDS = 60;

export default function Payment({ event, isPaid, onDismiss }: Props) {
  const [secondsLeft, setSecondsLeft] = useState(EXPIRY_SECONDS);

  useEffect(() => {
    if (isPaid) return;
    const interval = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(interval);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isPaid]);

  const expired = secondsLeft === 0 && !isPaid;

  return (
    <div className="fixed inset-0 bg-gray-950/90 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div
        className={`bg-gray-900 border rounded-2xl p-8 w-full max-w-sm shadow-2xl text-center transition-all ${
          isPaid
            ? "border-green-500 shadow-green-500/20"
            : expired
            ? "border-red-500/50"
            : "border-yellow-500/30"
        }`}
      >
        {isPaid ? (
          /* ---- PAID STATE ---- */
          <>
            <div className="text-6xl mb-4 animate-bounce">✅</div>
            <h2 className="text-2xl font-bold text-green-400 mb-1">Paid!</h2>
            <p className="text-gray-300 mb-4">
              <span className="text-yellow-400 font-bold text-xl">{event.sats} sats</span>
              {" "}settled to{" "}
              <span className="text-white font-medium">{event.producer_name}</span>
            </p>
            <p className="text-gray-500 text-sm mb-6">
              {event.kwh.toFixed(4)} kWh delivered and confirmed ⚡
            </p>
            <button
              onClick={onDismiss}
              className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-2.5 rounded-lg transition"
            >
              Done
            </button>
          </>
        ) : expired ? (
          /* ---- EXPIRED STATE ---- */
          <>
            <div className="text-5xl mb-4">⏱️</div>
            <h2 className="text-xl font-bold text-red-400 mb-2">Invoice Expired</h2>
            <p className="text-gray-400 text-sm mb-6">
              The HODL invoice timed out. A new one will be generated on the next meter reading.
            </p>
            <button
              onClick={onDismiss}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-bold py-2.5 rounded-lg transition"
            >
              Dismiss
            </button>
          </>
        ) : (
          /* ---- PENDING STATE ---- */
          <>
            <h2 className="text-lg font-bold text-yellow-400 mb-1">
              ⚡ Energy Invoice
            </h2>
            <p className="text-gray-400 text-sm mb-4">
              {event.kwh.toFixed(4)} kWh ·{" "}
              <span className="text-white font-semibold">{event.sats} sats</span>
            </p>

            {/* QR Code */}
            <div className="flex justify-center mb-4">
              <div className="bg-white p-3 rounded-xl">
                <QRCode
                  value={event.invoice || `lightning:${event.invoice}`}
                  size={200}
                  level="M"
                  includeMargin={false}
                />
              </div>
            </div>

            {/* Invoice string */}
            <div className="bg-gray-800 rounded-lg p-2 mb-4 overflow-hidden">
              <p className="text-xs text-gray-500 font-mono truncate">
                {event.invoice.slice(0, 60)}…
              </p>
            </div>

            {/* Countdown */}
            <div className="flex items-center justify-center gap-2 mb-4">
              <div
                className={`text-2xl font-mono font-bold ${
                  secondsLeft < 15 ? "text-red-400" : "text-yellow-400"
                }`}
              >
                {String(Math.floor(secondsLeft / 60)).padStart(2, "0")}:
                {String(secondsLeft % 60).padStart(2, "0")}
              </div>
              <span className="text-gray-500 text-sm">remaining</span>
            </div>

            {/* HODL explanation */}
            <div className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-3 mb-4">
              <p className="text-blue-300 text-xs">
                🔒 <strong>HODL invoice</strong> — funds are only released when the smart
                meter confirms energy delivery. Trustless settlement.
              </p>
            </div>

            <p className="text-gray-500 text-xs">
              Meter: <span className="text-gray-300">{event.meter_id}</span>
            </p>

            <button
              onClick={onDismiss}
              className="mt-4 text-gray-600 hover:text-gray-400 text-sm transition"
            >
              Dismiss
            </button>
          </>
        )}
      </div>
    </div>
  );
}
