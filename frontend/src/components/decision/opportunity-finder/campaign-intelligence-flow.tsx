"use client";

import Link from "next/link";
import { ArrowRight, Compass, Home, Map } from "lucide-react";
import type { LayerSignal, SimulatedCampaignPlan } from "@/lib/campaign-kpi-simulator";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

const LAYER_META = {
  mission: { icon: Home, accent: "border-indigo-200 bg-indigo-50 text-indigo-900", chip: "bg-indigo-100 text-indigo-700" },
  market: { icon: Map, accent: "border-teal-200 bg-teal-50 text-teal-900", chip: "bg-teal-100 text-teal-700" },
  metro: { icon: Compass, accent: "border-amber-200 bg-amber-50 text-amber-900", chip: "bg-amber-100 text-amber-700" },
} as const;

export function CampaignIntelligenceFlow({ plan }: { plan: SimulatedCampaignPlan | null }) {
  const signals = plan?.signals ?? [];

  return (
    <section className="orion-widget overflow-hidden p-5">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Intelligence → Campaign KPI Flow</h2>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            Pre-launch simulator combining analyzed outputs from Mission Control, Market Intelligence, and Metro Intelligence.
          </p>
        </div>
        {plan ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{plan.geoScope}</span>
        ) : null}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_auto_1fr_auto_1fr_auto_minmax(220px,0.9fr)] xl:items-stretch">
        {(["mission", "market", "metro"] as const).map((layer, index) => {
          const signal = signals.find((row) => row.layer === layer);
          const meta = LAYER_META[layer];
          const Icon = meta.icon;
          return (
            <div key={layer} className="contents">
              <SourceCard signal={signal} meta={meta} Icon={Icon} />
              {index < 2 ? <FlowArrow weight={plan?.intelligenceWeight[layer === "mission" ? "mission" : layer === "market" ? "market" : "metro"]} /> : null}
            </div>
          );
        })}
        <FlowArrow weight={1} />
        <TargetCard plan={plan} />
      </div>

      {plan ? (
        <p className="mt-4 text-xs text-[var(--cios-secondary)]">
          Blend weights — Mission {Math.round(plan.intelligenceWeight.mission * 100)}% · Market{" "}
          {Math.round(plan.intelligenceWeight.market * 100)}% · Metro {Math.round(plan.intelligenceWeight.metro * 100)}%
        </p>
      ) : null}
    </section>
  );
}

function SourceCard({
  signal,
  meta,
  Icon,
}: {
  signal: LayerSignal | undefined;
  meta: (typeof LAYER_META)[keyof typeof LAYER_META];
  Icon: typeof Home;
}) {
  const active = signal?.active ?? false;
  return (
    <div className={`rounded-xl border p-4 ${active ? meta.accent : "border-dashed border-gray-200 bg-gray-50 text-gray-600"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 shrink-0" />
          <div>
            <p className="text-sm font-semibold">{signal?.label ?? "Intelligence Layer"}</p>
            <p className="text-xs opacity-80">{signal?.geoLabel ?? "Not in scope"}</p>
          </div>
        </div>
        {signal ? (
          <Link href={signal.href} className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${meta.chip}`}>
            Open
          </Link>
        ) : null}
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <Metric label="Customers" value={active ? formatNumber(signal?.customers ?? 0) : "—"} />
        <Metric label="Revenue" value={active ? formatCurrency(signal?.revenue ?? 0) : "—"} />
        <Metric label="Conversion" value={active ? formatPercent(signal?.conversion ?? 0) : "—"} />
        <Metric label="Opp. Score" value={active && signal?.opportunityScore != null ? String(Math.round(signal.opportunityScore)) : "—"} />
      </dl>
      {active && signal?.topProduct ? (
        <p className="mt-3 text-xs">
          Top SKU: <span className="font-medium">{signal.topProduct}</span>
        </p>
      ) : null}
    </div>
  );
}

function TargetCard({ plan }: { plan: SimulatedCampaignPlan | null }) {
  return (
    <div className="rounded-xl border border-violet-300 bg-gradient-to-br from-violet-50 to-white p-4 shadow-sm">
      <p className="text-sm font-semibold text-violet-950">Campaign KPI Target</p>
      <p className="mt-1 text-xs text-violet-700">Pre-launch operating plan</p>
      {plan ? (
        <>
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-violet-700">Target Customers</dt>
              <dd className="font-semibold text-violet-950">{formatNumber(plan.targets.customers)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-violet-700">Expected Revenue</dt>
              <dd className="font-semibold text-violet-950">{formatCurrency(plan.targets.revenue)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-violet-700">Predicted Conversion</dt>
              <dd className="font-semibold text-violet-950">{formatPercent(plan.targets.conversion)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-violet-700">Expected Orders</dt>
              <dd className="font-semibold text-violet-950">{formatNumber(plan.targets.orders)}</dd>
            </div>
          </dl>
          <p className="mt-3 rounded-lg bg-white/80 px-3 py-2 text-xs text-violet-900">{plan.campaignMessage}</p>
        </>
      ) : (
        <p className="mt-4 text-sm text-violet-700">Run simulation to compose KPI targets from intelligence layers.</p>
      )}
    </div>
  );
}

function FlowArrow({ weight }: { weight?: number }) {
  return (
    <div className="hidden flex-col items-center justify-center px-1 xl:flex">
      <ArrowRight className="h-5 w-5 text-gray-400" />
      {weight != null && weight > 0 ? (
        <span className="mt-1 text-[10px] font-medium text-gray-500">{Math.round(weight * 100)}%</span>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wide opacity-70">{label}</dt>
      <dd className="font-semibold">{value}</dd>
    </div>
  );
}
