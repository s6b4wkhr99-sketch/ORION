"use client";

import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CustomerDetailDrawer } from "@/components/customer/customer-detail-drawer";
import {
  CustomerFilterPanel,
  EMPTY_CUSTOMER_FILTERS,
  indexLevel,
  useFilteredCustomers,
  type CustomerFilters,
} from "@/components/customer/customer-filters";
import { MockupKpiCard } from "@/components/mockup/mockup-kpi-card";
import { PageHeader } from "@/components/mockup/page-header";
import { PageTabs } from "@/components/mockup/page-tabs";
import { RadarPanel } from "@/components/mockup/radar-panel";
import { useFilters } from "@/contexts/filter-context";
import { api, type CustomerDashboard, type CustomerRow } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

const TABS = [
  { id: "overview", label: "Customer Dashboard" },
  { id: "explorer", label: "Intelligence Explorer" },
];

const PIE_COLORS = ["#0056D2", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#CBD5E1"];

export default function CustomersPage() {
  const { selectedUploadId, dataRevision, filtersReady, uploads } = useFilters();
  const [data, setData] = useState<CustomerDashboard | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [filters, setFilters] = useState<CustomerFilters>(EMPTY_CUSTOMER_FILTERS);
  const [selected, setSelected] = useState<CustomerRow | null>(null);
  const [sortKey, setSortKey] = useState<keyof CustomerRow>("campaign_priority");
  const [sortAsc, setSortAsc] = useState(false);
  const [tab, setTab] = useState("overview");

  useEffect(() => {
    if (!filtersReady) return;
    const hasCompletedUpload = uploads.some((u) => u.status === "completed");
    if (!selectedUploadId && hasCompletedUpload) return;
    let cancelled = false;
    setLoadError(null);
    api
      .getCustomers(selectedUploadId ?? undefined)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((err) => {
        if (!cancelled) {
          setData(null);
          setLoadError(err instanceof Error ? err.message : "Failed to load customer intelligence");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [selectedUploadId, dataRevision, filtersReady, uploads]);

  const items = data?.customers.items ?? [];
  const totalCustomers = data?.customers.total ?? 0;
  const filtered = useFilteredCustomers(items, filters);
  const hasData = totalCustomers > 0;

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";
      if (typeof av === "number" && typeof bv === "number") return sortAsc ? av - bv : bv - av;
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [filtered, sortKey, sortAsc]);

  const avgIndices = data?.distribution.average_indices ?? {};
  const ceragemDonut = useMemo(() => {
    const dist = data?.distribution.ceragem_distribution ?? {};
    const total = Object.values(dist).reduce((s, v) => s + v, 0) || 1;
    return Object.entries(dist).map(([name, value]) => ({
      name,
      value: Math.round((value / total) * 100),
    }));
  }, [data]);
  const topStates = useMemo(() => {
    return [...(data?.distribution.by_state ?? [])]
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [data]);
  const intelligenceRadar = useMemo(() => {
    return Object.entries(avgIndices).map(([axis, score]) => ({ axis, score: Math.round(score) }));
  }, [avgIndices]);

  const availableStates = useMemo(
    () => [...new Set(items.map((r) => r.state).filter(Boolean) as string[])].sort(),
    [items],
  );
  const availableZips = useMemo(
    () => [...new Set(items.map((r) => r.zip).filter(Boolean) as string[])].sort(),
    [items],
  );

  const exportCsv = () => {
    const headers = ["ID", "Email", "State", "ZIP", "Ceragem", "Product", "Priority", "Expected Revenue"];
    const rows = sorted.map((r) => [
      r.id, r.email, r.state, r.zip, r.ceragem_segment, r.recommended_product,
      indexLevel(r.campaign_priority), r.expected_revenue,
    ]);
    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "customer_intelligence.csv";
    a.click();
  };

  const toggleSort = (key: keyof CustomerRow) => {
    if (sortKey === key) setSortAsc((v) => !v);
    else { setSortKey(key); setSortAsc(false); }
  };

  const pageShell = (
    <>
      <PageHeader
        title="Customer Database"
        subtitle="Analyze customer database, intelligence scores, and segment distribution."
      />
      <PageTabs tabs={TABS} active={tab} onChange={setTab} />
    </>
  );

  if (!data) {
    return (
      <div className="space-y-6">
        {pageShell}
        {loadError ? (
          <p className="text-sm text-red-600">{loadError}</p>
        ) : (
          <p className="text-sm text-[var(--cios-secondary)]">Loading customer intelligence…</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {pageShell}

      {tab === "overview" && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <MockupKpiCard label="Total Customers" value={formatNumber(totalCustomers)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Target Customers" value={formatNumber(filtered.length)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="High Priority Customers" value={formatNumber(filtered.filter((r) => indexLevel(r.campaign_priority) === "High").length)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Avg. Purchase Power" value={avgIndices.purchase_power != null ? `${Math.round(avgIndices.purchase_power)}/100` : "—"} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Avg. Pain Index" value={avgIndices.pain_index != null ? `${Math.round(avgIndices.pain_index)}/100` : "—"} showSparkline={false} usePlaceholderDelta={false} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="cios-card p-5">
              <h2 className="mb-4 text-base font-semibold text-gray-900">Customers by State</h2>
              {topStates.length > 0 ? (
                <div className="h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={topStates.map((s) => ({ state: s.state, count: s.count }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="state" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" name="Customers" stroke="#0056D2" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-[var(--cios-secondary)]">No state distribution data.</p>
              )}
            </section>
            <section className="cios-card p-5">
              <h2 className="mb-4 text-base font-semibold text-gray-900">Customers by Ceragem Segment</h2>
              {ceragemDonut.length > 0 ? (
                <div className="h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={ceragemDonut} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={75}>
                        {ceragemDonut.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v) => `${Number(v)}%`} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-[var(--cios-secondary)]">No segment distribution data.</p>
              )}
            </section>
          </div>

          <section className="cios-card overflow-hidden">
            <h2 className="border-b border-[var(--cios-border)] px-5 py-4 text-base font-semibold text-gray-900">Top States</h2>
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-[var(--cios-secondary)]">
                <tr>
                  <th className="px-4 py-2 text-left">State</th>
                  <th className="px-4 py-2 text-right">Customers</th>
                </tr>
              </thead>
              <tbody>
                {topStates.length > 0 ? (
                  topStates.map((s) => (
                    <tr key={s.state} className="border-t border-gray-100">
                      <td className="px-4 py-2 font-medium">{s.state}</td>
                      <td className="px-4 py-2 text-right">{formatNumber(s.count)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={2} className="px-4 py-6 text-center text-sm text-[var(--cios-secondary)]">No state data.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        </>
      )}

      {tab === "explorer" && (
        <>
          <CustomerFilterPanel filters={filters} onChange={setFilters} availableStates={availableStates} availableZips={availableZips} />
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <MockupKpiCard label="Avg. Purchase Power" value={avgIndices.purchase_power != null ? `${Math.round(avgIndices.purchase_power)}/100` : "—"} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Avg. Pain Index" value={avgIndices.pain_index != null ? `${Math.round(avgIndices.pain_index)}/100` : "—"} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="High Priority Customers" value={formatNumber(filtered.filter((r) => indexLevel(r.campaign_priority) === "High").length)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Filtered Customers" value={formatNumber(filtered.length)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Target Customers" value={formatNumber(totalCustomers)} showSparkline={false} usePlaceholderDelta={false} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            {intelligenceRadar.length > 0 ? (
              <RadarPanel data={intelligenceRadar} title="Intelligence Distribution Radar" />
            ) : (
              <section className="cios-card p-5">
                <p className="text-sm text-[var(--cios-secondary)]">No intelligence radar data in scope.</p>
              </section>
            )}
            <section className="cios-card p-5">
              <h2 className="mb-4 text-base font-semibold text-gray-900">Intelligence Score Distribution</h2>
              {["Purchase Power", "Pain Index", "Lifestyle", "PRIZM Proxy", "Ceragem Segment"].map((label, i) => (
                <div key={label} className="mb-3">
                  <div className="mb-1 flex justify-between text-xs text-[var(--cios-secondary)]">
                    <span>{label}</span>
                    <span>High {62 - i * 4}%</span>
                  </div>
                  <div className="flex h-3 overflow-hidden rounded-full bg-gray-100">
                    <div className="bg-[var(--cios-primary)]" style={{ width: `${62 - i * 4}%` }} />
                    <div className="bg-emerald-400" style={{ width: `${22 + i}%` }} />
                    <div className="bg-amber-300" style={{ width: `${16 - i}%` }} />
                  </div>
                </div>
              ))}
            </section>
          </div>
        </>
      )}

      <section className="cios-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-[var(--cios-border)] px-4 py-3">
          <h2 className="text-base font-semibold text-gray-900">Customer Intelligence Table</h2>
          <button type="button" onClick={exportCsv} className="cios-btn flex items-center gap-2 border border-[var(--cios-border)] px-3 py-1.5 text-sm hover:bg-gray-50">
            <Download className="h-4 w-4" /> CSV Export
          </button>
        </div>
        <div className="max-h-[400px] overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-gray-50 text-xs uppercase text-[var(--cios-secondary)]">
              <tr>
                {[["email", "Email"], ["state", "State"], ["zip", "ZIP"], ["ceragem_segment", "Segment"], ["recommended_product", "Product"], ["brand_familiarity_index", "Brand"], ["email_response_index", "Digital"], ["campaign_priority", "Priority"], ["expected_revenue", "Revenue"]].map(([key, label]) => (
                  <th key={key} className="cursor-pointer px-3 py-2" onClick={() => toggleSort(key as keyof CustomerRow)}>{label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(sorted.length ? sorted : []).slice(0, 50).map((row) => (
                <tr key={row.id} className="cursor-pointer border-t border-gray-100 hover:bg-[var(--cios-primary-light)]/40" onClick={() => setSelected(row)}>
                  <td className="px-3 py-2">{row.email ?? "—"}</td>
                  <td className="px-3 py-2">{row.state ?? "—"}</td>
                  <td className="px-3 py-2">{row.zip ?? "—"}</td>
                  <td className="px-3 py-2">{row.ceragem_segment ?? "—"}</td>
                  <td className="px-3 py-2" title={row.recommendation_rationale_summary ?? undefined}>{row.recommended_product ?? "—"}</td>
                  <td className="px-3 py-2">{indexLevel(row.brand_familiarity_index)}</td>
                  <td className="px-3 py-2">{indexLevel(row.email_response_index)}</td>
                  <td className="px-3 py-2">{indexLevel(row.campaign_priority)}</td>
                  <td className="px-3 py-2">{formatCurrency(row.expected_revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <CustomerDetailDrawer customer={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
