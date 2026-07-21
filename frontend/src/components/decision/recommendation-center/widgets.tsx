"use client";

import { Cell, Bar, BarChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { formatCurrency } from "@/lib/utils";
import { mergeProductChartRows } from "@/lib/product-legend-groups";

const COLORS = ["#6366F1", "#818CF8", "#A5B4FC", "#14B8A6", "#F59E0B"];

export function ProductFitTreemap({ data }: { data: { product: string; revenue: number; customers: number }[] }) {
  const chartData = mergeProductChartRows(data);

  if (!chartData.length) {
    return <p className="text-sm text-[var(--cios-secondary)]">No product fit data in audience.</p>;
  }

  return (
    <div className="h-[220px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
          <XAxis type="number" tickFormatter={(v) => `$${Math.round(Number(v) / 1000)}k`} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="product" width={110} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => formatCurrency(Number(v))} />
          <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PromotionStrategy({
  selected,
  onChange,
}: {
  selected: string;
  onChange: (value: string) => void;
}) {
  const options = [
    { id: "none", label: "No Promotion", desc: "Brand awareness focus" },
    { id: "gift", label: "Gift With Purchase", desc: "Wellness accessory bundle" },
    { id: "percent", label: "10% Online Discount", desc: "Promo code attribution" },
    { id: "financing", label: "Financing Offer", desc: "0% APR messaging" },
    { id: "bundle", label: "Product Bundle", desc: "Master V9 + accessories" },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {options.map((opt) => (
        <button
          key={opt.id}
          type="button"
          onClick={() => onChange(opt.id)}
          className={`rounded-xl border p-4 text-left transition-all ${
            selected === opt.id ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-200" : "border-gray-200 bg-white hover:border-indigo-200"
          }`}
        >
          <p className="font-semibold text-gray-900">{opt.label}</p>
          <p className="mt-1 text-xs text-[var(--cios-secondary)]">{opt.desc}</p>
        </button>
      ))}
    </div>
  );
}

export function ConfidenceGauge({ score }: { score: number }) {
  const label = score >= 95 ? "Very High" : score >= 85 ? "High" : score >= 70 ? "Moderate" : "Review Recommended";
  const circumference = 2 * Math.PI * 50;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-32 w-32">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#E5E7EB" strokeWidth="10" />
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke="#6366F1"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-2xl font-bold text-gray-900">{Math.round(score)}</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--cios-secondary)]">Confidence</p>
        </div>
      </div>
      <p className="mt-2 text-sm font-semibold text-indigo-700">{label}</p>
    </div>
  );
}

export function MessageRecommendation({
  category,
  headline,
  supporting,
  tone,
  conversion,
}: {
  category: string;
  headline: string;
  supporting: string;
  tone: string;
  conversion: number;
}) {
  return (
    <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">{category}</p>
      <h3 className="mt-2 text-lg font-semibold text-gray-900">{headline}</h3>
      <p className="mt-2 text-sm text-gray-700">{supporting}</p>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <dt className="text-xs text-[var(--cios-secondary)]">Creative Tone</dt>
          <dd className="text-sm font-medium text-gray-900">{tone}</dd>
        </div>
        <div>
          <dt className="text-xs text-[var(--cios-secondary)]">Expected Conversion</dt>
          <dd className="text-sm font-medium text-indigo-600">{(conversion * 100).toFixed(2)}%</dd>
        </div>
      </dl>
    </div>
  );
}
