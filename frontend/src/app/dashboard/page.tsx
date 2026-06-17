"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import NavBar from "@/components/NavBar";
import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { PredictionResult } from "@/types";

const CONFIDENCE_COLORS: Record<string, string> = {
  High: "bg-indigo-100 text-indigo-800 border-indigo-200",
  Moderate: "bg-amber-100 text-amber-800 border-amber-200",
  Low: "bg-gray-100 text-gray-600 border-gray-200",
};

function tagColor(tag: string): string {
  if (tag.startsWith("High")) return CONFIDENCE_COLORS.High;
  if (tag.startsWith("Moderate")) return CONFIDENCE_COLORS.Moderate;
  return CONFIDENCE_COLORS.Low;
}

export default function DashboardPage() {
  const router = useRouter();
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    api.get<PredictionResult>("/predictions/me")
      .then(setResult)
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavBar />
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400 text-sm">Loading predictions...</div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Interest Predictions</h1>
            <p className="text-sm text-gray-500 mt-1">
              Based on {result.total_events} behavior event{result.total_events !== 1 ? "s" : ""} for{" "}
              <span className="font-medium text-gray-700">{result.username}</span>
            </p>
          </div>
        </div>

        {result.tags.length > 0 && (
          <section className="mb-8">
            <h2 className="text-base font-semibold text-gray-700 mb-3">Interest Tags</h2>
            <div className="flex flex-wrap gap-2">
              {result.tags.map((t) => (
                <span
                  key={t.tag}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${tagColor(t.tag)}`}
                >
                  {t.tag}
                  <span className="text-xs opacity-60">{Math.round(t.confidence * 100)}%</span>
                </span>
              ))}
            </div>
          </section>
        )}

        {result.scores.length > 0 ? (
          <section>
            <h2 className="text-base font-semibold text-gray-700 mb-4">Category Scores</h2>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="divide-y divide-gray-50">
                {result.scores.map((cs) => (
                  <div key={cs.category} className="px-6 py-4 flex items-center gap-4">
                    <div className="w-6 text-xs font-bold text-gray-300 text-right">
                      #{cs.rank}
                    </div>
                    <div className="w-28 capitalize text-sm font-medium text-gray-700">
                      {cs.category}
                    </div>
                    <div className="flex-1">
                      <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${cs.score}%` }}
                        />
                      </div>
                    </div>
                    <div className="w-12 text-right text-sm font-semibold text-gray-700">
                      {cs.score}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
            <p className="text-gray-400 text-sm">
              No predictions yet. Log some behavior events to see your interest scores.
            </p>
            <a
              href="/behaviors"
              className="mt-4 inline-block text-sm text-indigo-600 hover:underline font-medium"
            >
              Log behaviors
            </a>
          </div>
        )}
      </main>
    </div>
  );
}
