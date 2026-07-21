"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { UploadDropZone } from "@/components/upload/upload-drop-zone";
import { MockupKpiCard } from "@/components/mockup/mockup-kpi-card";
import { PageHeader } from "@/components/mockup/page-header";
import { PageTabs } from "@/components/mockup/page-tabs";
import { StatusBadge } from "@/components/mockup/status-badge";
import { api, type CampaignDashboard } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export default function CampaignsPage() {
  const router = useRouter();
  const [data, setData] = useState<CampaignDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("all");
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api.getCampaigns().then(setData).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const campaigns = data?.campaigns ?? [];
  const overview = data?.overview;

  const tabCounts = useMemo(
    () => ({
      all: campaigns.length,
      active: campaigns.filter((c) => c.sent > 0).length,
    }),
    [campaigns],
  );

  const handleReportUpload = async (file: File) => {
    setUploadError(null);
    setUploadMsg(null);
    try {
      const res = await api.uploadCampaignReport(file);
      setUploadMsg(`Imported ${res.campaign_name ?? "campaign"} successfully`);
      load();
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Import failed");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Campaign Intelligence"
        subtitle="Did our prediction work? — Measure forecast accuracy and import ESP results."
        actions={
          <button
            type="button"
            className="cios-btn flex items-center gap-2 bg-[var(--cios-primary)] px-4 py-2 text-sm text-white hover:opacity-90"
            onClick={() => router.push("/recommendations")}
          >
            <Plus className="h-4 w-4" /> New Recommendation
          </button>
        }
      />

      <PageTabs
        tabs={[
          { id: "all", label: "All Campaigns", count: tabCounts.all },
          { id: "active", label: "Active", count: tabCounts.active },
          { id: "reports", label: "Report Import" },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab !== "reports" && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MockupKpiCard label="Campaigns" value={formatNumber(overview?.campaign_count ?? campaigns.length)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Total Sent" value={formatNumber(overview?.total_sent ?? 0)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Attributed Revenue" value={formatCurrency(overview?.total_revenue ?? 0)} showSparkline={false} usePlaceholderDelta={false} />
            <MockupKpiCard label="Avg. ROI" value={overview?.avg_roi != null ? formatPercent(overview.avg_roi) : "—"} showSparkline={false} usePlaceholderDelta={false} />
          </div>

          <section className="cios-card overflow-hidden">
            {campaigns.length > 0 ? (
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-xs uppercase text-[var(--cios-secondary)]">
                  <tr>
                    <th className="px-4 py-3 text-left">Campaign</th>
                    <th className="px-4 py-3 text-right">Sent</th>
                    <th className="px-4 py-3 text-right">Revenue</th>
                    <th className="px-4 py-3 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns
                    .filter((c) => tab !== "active" || c.sent > 0)
                    .map((c) => (
                      <tr key={c.campaign_id} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <Link href={`/campaigns/${encodeURIComponent(c.campaign_id)}`} className="font-medium text-[var(--cios-primary)] hover:underline">
                            {c.campaign_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-right">{formatNumber(c.sent)}</td>
                        <td className="px-4 py-3 text-right font-medium">{formatCurrency(c.revenue)}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={c.sent > 0 ? "Active" : "Draft"} />
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            ) : (
              <p className="p-5 text-sm text-[var(--cios-secondary)]">
                No campaigns yet. Approve a recommendation and export to your ESP, then import results here.
              </p>
            )}
          </section>
        </>
      )}

      {tab === "reports" && (
        <section className="cios-card p-5">
          <h2 className="mb-2 text-base font-semibold text-gray-900">Campaign Report Import</h2>
          <p className="mb-4 text-sm text-[var(--cios-secondary)]">
            Import performance data from Mailchimp, Klaviyo, HubSpot, and other providers for learning.
          </p>
          <UploadDropZone onFileSelected={handleReportUpload} />
          {uploadMsg && <p className="mt-3 text-sm text-[var(--cios-success)]">{uploadMsg}</p>}
          {uploadError && <p className="mt-3 text-sm text-[var(--cios-error)]">{uploadError}</p>}
        </section>
      )}

      {loading && <p className="text-sm text-[var(--cios-secondary)]">Syncing campaign analytics...</p>}
    </div>
  );
}
