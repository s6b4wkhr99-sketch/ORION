"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Download, Loader2, Trash2 } from "lucide-react";
import { UploadDropZone } from "@/components/upload/upload-drop-zone";
import { PageHeader } from "@/components/mockup/page-header";
import {
  api,
  type BuyerGapReport,
  type BuyerProspectMatchStats,
  type BuyerUploadPreview,
  type BuyerUploadResult,
  type UploadSummary,
} from "@/lib/api";
import { cn, formatDateTimeEST } from "@/lib/utils";
import { sortGapSkuEntries } from "@/lib/buyer-gap-order";

export default function BuyerImportPage() {
  const [preview, setPreview] = useState<BuyerUploadPreview | null>(null);
  const [result, setResult] = useState<BuyerUploadResult | null>(null);
  const [gapReport, setGapReport] = useState<BuyerGapReport | null>(null);
  const [matchStats, setMatchStats] = useState<BuyerProspectMatchStats | null>(null);
  const [buyerUploads, setBuyerUploads] = useState<UploadSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = useCallback(async (uploadId: string) => {
    setDownloadError(null);
    setDownloadingId(uploadId);
    try {
      await api.downloadBuyerMatchedCsv(uploadId);
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : "Download failed");
    } finally {
      setDownloadingId(null);
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [stats, uploads] = await Promise.all([
        api.getBuyerProspectMatchStats(),
        api.getUploads("buyer"),
      ]);
      setMatchStats(stats);
      setBuyerUploads(uploads);
    } catch {
      setMatchStats(null);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, result]);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setResult(null);
    setGapReport(null);
    setLoading(true);
    try {
      const p = await api.previewBuyerUpload(file);
      setPreview(p);
      if (p.fatal_errors?.length) {
        setError(p.fatal_errors.join("; "));
        return;
      }
      const r = await api.uploadBuyerFile(file);
      setResult(r);
      setGapReport(r.gap_report ?? null);
      if (r.upload_id && !r.gap_report) {
        const report = await api.getBuyerGapReport(r.upload_id);
        setGapReport(report);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      if (msg === "Not Found" || /404/.test(msg)) {
        setError(
          "Buyer Upload API를 사용할 수 없습니다. 백엔드를 재시작해 주세요 (프로젝트 루트에서 make dev-restart).",
        );
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDelete = useCallback(
    async (upload: UploadSummary) => {
      if (
        !window.confirm(
          `Delete buyer upload "${upload.file_name}"?\n\nThis removes purchase rows and GAP data for this batch. Prospect data is not affected.`,
        )
      ) {
        return;
      }
      setDownloadError(null);
      setDeletingId(upload.id);
      try {
        await api.deleteBuyerUpload(upload.id);
        setBuyerUploads((prev) => prev.filter((u) => u.id !== upload.id));
        if (result?.upload_id === upload.id) {
          setResult(null);
          setGapReport(null);
          setPreview(null);
        }
        await refresh();
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Delete failed";
        setDownloadError(msg);
        setError(msg);
      } finally {
        setDeletingId(null);
      }
    },
    [refresh, result?.upload_id],
  );

  const gapEntries = gapReport?.aggregate_gap?.reweighted_distribution_gap
    ? sortGapSkuEntries(Object.entries(gapReport.aggregate_gap.reweighted_distribution_gap))
    : [];

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Buyer Upload & GAP"
        subtitle="Upload purchaser files, match emails to ORION prospects, and run bias-adjusted GAP analysis."
      />

      {matchStats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Prospect emails (ORION)" value={matchStats.prospect_emails_with_intel.toLocaleString()} />
          <StatCard label="Buyer emails uploaded" value={matchStats.buyer_unique_emails.toLocaleString()} />
          <StatCard
            label="Matched to prospect"
            value={matchStats.buyer_matched_emails.toLocaleString()}
            highlight
          />
          <StatCard label="Match rate" value={`${matchStats.buyer_match_rate_pct}%`} />
        </div>
      )}

      <div className="rounded-lg border border-[var(--cios-border)] bg-[var(--cios-surface)] p-4">
        <UploadDropZone
          onFileSelected={handleFile}
          disabled={loading}
          label="Drag buyer Excel or CSV here"
          hint="Legacy XLSX (PAID) or Shopify CSV (paid orders)"
        />
        {loading && (
          <p className="mt-3 flex items-center gap-2 text-sm text-[var(--cios-secondary)]">
            <Loader2 className="h-4 w-4 animate-spin" /> Processing buyer upload & GAP report…
          </p>
        )}
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      {preview && !error && (
        <section className="rounded-lg border border-[var(--cios-border)] bg-[var(--cios-surface)] p-4 text-sm text-gray-900">
          <h3 className="mb-2 font-medium">Preview — {preview.file_name}</h3>
          <p>
            Format: <strong>{preview.detected_format}</strong> · Chair rows:{" "}
            <strong>{preview.chair_rows}</strong> · Emails: <strong>{preview.unique_emails}</strong>
          </p>
          {preview.warnings?.length > 0 && (
            <p className="mt-1 text-amber-700">{preview.warnings.join(" ")}</p>
          )}
        </section>
      )}

      {result && (
        <section className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
          <h3 className="font-medium text-emerald-900">Upload complete</h3>
          <p className="mt-1 text-sm text-emerald-800">
            {result.file_name} — {result.summary?.chair_rows as number} chair rows ·{" "}
            <strong>{result.matched_emails}</strong> / {result.unique_emails} emails matched to ORION (
            {result.match_rate_pct}%)
          </p>
          {result.matched_emails > 0 && (
            <button
              type="button"
              className="cios-btn mt-3 inline-flex items-center gap-2 rounded-md bg-[var(--cios-primary)] px-3 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
              disabled={downloadingId === result.upload_id}
              onClick={() => handleDownload(result.upload_id)}
            >
              {downloadingId === result.upload_id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Download matched email GAP (CSV)
            </button>
          )}
          {downloadError && <p className="mt-2 text-sm text-red-600">{downloadError}</p>}
        </section>
      )}

      {gapReport && (
        <section className="rounded-lg border border-[var(--cios-border)] bg-[var(--cios-surface)] p-4 text-gray-900">
          <h3 className="mb-3 font-medium">GAP Report (bias-adjusted)</h3>
          <div className="mb-4 grid gap-3 sm:grid-cols-3 text-sm">
            <div>Intel exact hit: <strong>{gapReport.intel_exact_hit_rate_pct ?? 0}%</strong></div>
            <div>State OTHER rows: <strong>{gapReport.state_other_rows ?? 0}</strong></div>
            <div>CA bias index: <strong>{gapReport.reweight_ca_bias_index ?? "—"}</strong></div>
          </div>
          {gapEntries.length > 0 && (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--cios-border)]">
                  <th className="py-2 pr-4">SKU</th>
                  <th className="py-2 pr-4">Buyer %</th>
                  <th className="py-2 pr-4">Prospect %</th>
                  <th className="py-2">GAP (pp)</th>
                </tr>
              </thead>
              <tbody>
                {gapEntries.map(([sku, row]) => (
                  <tr key={sku} className="border-b border-[var(--cios-border)]/60">
                    <td className="py-2 pr-4 font-mono">{sku}</td>
                    <td className="py-2 pr-4">{row.buyer_pct}</td>
                    <td className="py-2 pr-4">{row.prospect_pct}</td>
                    <td className={cn("py-2", row.gap_points > 0 ? "text-emerald-700" : "text-red-700")}>
                      {row.gap_points > 0 ? "+" : ""}
                      {row.gap_points}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {buyerUploads.length > 0 && (
        <section className="rounded-lg border border-[var(--cios-border)] bg-[var(--cios-surface)] p-4 text-gray-900">
          <h3 className="mb-3 font-medium">Recent buyer uploads</h3>
          <ul className="space-y-2 text-sm">
            {buyerUploads.slice(0, 10).map((u) => {
              const s = u.summary as Record<string, number> | null;
              return (
                <li key={u.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--cios-border)]/50 py-2">
                  <span>
                    {u.file_name}{" "}
                    <span className="text-[var(--cios-secondary)]">
                      ({formatDateTimeEST(u.created_at ?? "")})
                    </span>
                  </span>
                  <span className="flex items-center gap-3">
                    <span>
                      matched <strong>{s?.matched_emails ?? 0}</strong> / {s?.unique_emails ?? 0}
                    </span>
                    {(s?.matched_emails ?? 0) > 0 && (
                      <button
                        type="button"
                        className="font-medium text-[var(--cios-primary)] underline hover:opacity-80 disabled:opacity-50"
                        disabled={downloadingId === u.id || deletingId === u.id}
                        onClick={() => handleDownload(u.id)}
                      >
                        {downloadingId === u.id ? "…" : "CSV"}
                      </button>
                    )}
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 rounded-md border border-red-200 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                      disabled={deletingId === u.id || downloadingId === u.id}
                      onClick={() => handleDelete(u)}
                      aria-label={`Delete ${u.file_name}`}
                    >
                      {deletingId === u.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                      Delete
                    </button>
                  </span>
                </li>
              );
            })}
          </ul>
          {downloadError && <p className="mt-2 text-sm text-red-600">{downloadError}</p>}
        </section>
      )}

      <p className="text-xs text-[var(--cios-secondary)]">
        Supports Legacy XLSX (PAID/PROCESSING + Material Name + E MAIL + LOCATION) and Shopify CSV (paid +
        Lineitem name). Dashboard KPIs use prospect uploads only — buyer batches are isolated for GAP
        validation.{" "}
        <Link href="/import" className="text-[var(--cios-primary)] underline">
          Prospect Upload Center
        </Link>
      </p>
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        highlight ? "border-[var(--cios-primary)] bg-blue-50/40" : "border-[var(--cios-border)] bg-[var(--cios-surface)]",
      )}
    >
      <p className="text-xs text-[var(--cios-secondary)]">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums text-gray-900">{value}</p>
    </div>
  );
}
