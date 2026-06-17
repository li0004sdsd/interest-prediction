"use client";
import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import NavBar from "@/components/NavBar";
import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { BehaviorEventOut } from "@/types";

const CATEGORIES = [
  "technology","sports","fashion","food","travel",
  "health","finance","entertainment","education","gaming",
];
const ACTIONS = ["view","click","search","add_to_cart","purchase","scroll"];

export default function BehaviorsPage() {
  const router = useRouter();
  const [events, setEvents] = useState<BehaviorEventOut[]>([]);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [action, setAction] = useState(ACTIONS[0]);
  const [weight, setWeight] = useState("1.0");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    api.get<BehaviorEventOut[]>("/behaviors").then(setEvents).catch(() => router.replace("/login"));
  }, [router]);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const ev = await api.post<BehaviorEventOut>("/behaviors", {
        category,
        action,
        weight: parseFloat(weight),
      });
      setEvents((prev) => [ev, ...prev]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add event");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    await api.delete(`/behaviors/${id}`).catch(() => null);
    setEvents((prev) => prev.filter((e) => e.id !== id));
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Behavior Events</h1>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-8">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Log New Behavior</h2>
          <form onSubmit={handleAdd} className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Action</label>
              <select
                value={action}
                onChange={(e) => setAction(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {ACTIONS.map((a) => <option key={a}>{a}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Weight</label>
              <input
                type="number"
                min="0.1"
                max="10"
                step="0.1"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              {submitting ? "Adding..." : "Add Event"}
            </button>
          </form>
          {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {["Category","Action","Weight","Date",""].map((h) => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {events.length === 0 ? (
                <tr><td colSpan={5} className="text-center text-gray-400 py-8">No behavior events yet.</td></tr>
              ) : events.map((ev) => (
                <tr key={ev.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 capitalize font-medium text-gray-700">{ev.category}</td>
                  <td className="px-4 py-3 capitalize text-gray-600">{ev.action}</td>
                  <td className="px-4 py-3 text-gray-600">{ev.weight}</td>
                  <td className="px-4 py-3 text-gray-400">{new Date(ev.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleDelete(ev.id)}
                      className="text-red-500 hover:text-red-700 text-xs font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
