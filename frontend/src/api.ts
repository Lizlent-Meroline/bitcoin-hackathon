import axios from "axios";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL: BASE });

// ---- Types ---------------------------------------------------------------

export interface Producer {
  id: number;
  meter_id: string;
  name: string;
  lightning_address: string;
  created_at: string;
}

export interface Payment {
  id: number;
  reading_id: string;
  meter_id: string;
  sats_amount: number;
  kwh_amount: number;
  status: string;
  lightning_address: string;
  invoice_request: string | null;
  paid_at: string | null;
  created_at: string;
}

export interface Stats {
  meter_id: string;
  total_payments: number;
  total_sats: number;
  total_kwh: number;
  history: { sats: number; kwh: number; paid_at: string | null }[];
}

// ---- API calls -----------------------------------------------------------

export const getProducers = () => api.get<Producer[]>("/api/producers").then((r) => r.data);

export const registerProducer = (data: {
  meter_id: string;
  name: string;
  lightning_address: string;
  node_pubkey?: string;
}) => api.post<Producer>("/api/producers", data).then((r) => r.data);

export const getPayments = (meter_id?: string) =>
  api
    .get<Payment[]>("/api/payments", { params: meter_id ? { meter_id } : {} })
    .then((r) => r.data);

export const getStats = (meter_id: string) =>
  api.get<Stats>(`/api/stats/${meter_id}`).then((r) => r.data);
