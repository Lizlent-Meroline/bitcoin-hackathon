import { useState, useEffect } from "react";
import { type Producer } from "./api";
import Register from "./Register";
import Dashboard from "./Dashboard";

const STORAGE_KEY = "solarsats_producer";

function App() {
  const [producer, setProducer] = useState<Producer | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Try to restore session from localStorage
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setProducer(JSON.parse(stored));
        setLoading(false);
        return;
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  const handleRegistered = (p: Producer) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
    setProducer(p);
  };

  const handleLogout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setProducer(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-yellow-400 text-2xl animate-pulse">☀️⚡</div>
      </div>
    );
  }

  if (!producer) {
    return <Register onRegistered={handleRegistered} />;
  }

  return <Dashboard producer={producer} onLogout={handleLogout} />;
}

export default App;
