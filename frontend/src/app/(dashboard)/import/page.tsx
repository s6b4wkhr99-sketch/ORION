"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Loader2 } from "lucide-react";
import { UploadDropZone } from "@/components/upload/upload-drop-zone";
import { MappingReportPanel } from "@/components/upload/mapping-report";
import { UPLOAD_STAGES, UploadProgressPanel, type UploadStage } from "@/components/upload/upload-progress";
import { UploadResultPanel } from "@/components/upload/upload-result";
import { ValidationSummaryPanel } from "@/components/upload/validation-summary";
import { PageHeader } from "@/components/mockup/page-header";
import { useFilters } from "@/contexts/filter-context";
import { api, type UploadPreview, type UploadProcessingProfile, type UploadResult, type UploadSummary } from "@/lib/api";
import { SHOW_CAMPAIGN_MODULES } from "@/lib/config";
import { cn, formatDateTimeEST } from "@/lib/utils";

type Step = "idle" | "preview" | "uploading" | "done";

const STEPS = ["Upload File", "Auto Mapping", "Mapping Report", "Validation", "Complete"];

function initStages(): UploadStage[] {
  return UPLOAD_STAGES.map((s, i) => ({
    ...s,
    progress: 0,
    status: i === 0 ? "active" : "pending",
    eta: i === 0 ? "~5s" : undefined,
  }));
}

export default function ImportPage() {
  const { refreshDashboards, refreshExecutive } = useFilters();
  const [step, setStep] = useState<Step>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [uploadProfile, setUploadProfile] = useState<UploadProcessingProfile | null>(null);
  const [stages, setStages] = useState<UploadStage[]>(initStages);
  const [overall, setOverall] = useState(0);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [processingMs, setProcessingMs] = useState<number>();
  const [error, setError] = useState<string | null>(null);
  const [uiStep, setUiStep] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [mappingReportOpen, setMappingReportOpen] = useState(false);
  const [recentUploads, setRecentUploads] = useState<UploadSummary[]>([]);
  const [systemHealth, setSystemHealth] = useState<{
    postgres?: boolean;
    readyFor2_5m?: boolean;
    dbDriver?: string;
  } | null>(null);

  useEffect(() => {
    api.getUploadProcessingProfile().then(setUploadProfile).catch(() => setUploadProfile(null));
    api
      .getHealth()
      .then((h) =>
        setSystemHealth({
          postgres: h.database?.postgres,
          readyFor2_5m: h.upload_pipeline?.ready_for_2_5m,
          dbDriver: h.database?.url_scheme,
        }),
      )
      .catch(() => setSystemHealth(null));
  }, []);

  useEffect(() => {
    if (preview?.total_rows == null) return;
    api.getUploadProcessingProfile(preview.total_rows).then(setUploadProfile).catch(() => undefined);
  }, [preview?.total_rows]);

  useEffect(() => {
    api.getUploads().then(setRecentUploads).catch(() => setRecentUploads([]));
  }, [step, result]);

  const canUpload = useMemo(() => preview != null && (preview.fatal_errors?.length ?? 0) === 0, [preview]);

  const handleFileSelected = useCallback(async (selected: File) => {
    setError(null);
    setFile(selected);
    setResult(null);
    setStep("preview");
    setUiStep(1);
    setStages(initStages());
    setOverall(5);
    try {
      const data = await api.previewUpload(selected);
      setPreview(data);
      setMappingReportOpen(true);
      setUiStep(2);
      setStages((prev) =>
        prev.map((s, i) =>
          i <= 3
            ? { ...s, progress: 100, status: "done" as const }
            : i === 4
              ? { ...s, status: "active" as const, progress: 50 }
              : s,
        ),
      );
      setOverall(55);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
      setStep("idle");
      setUiStep(0);
    }
  }, []);

  const mostlyDuplicates =
    preview != null &&
    preview.total_rows > 0 &&
    (preview.stats.duplicate_email_in_db ?? 0) >= preview.total_rows * 0.9;

  const handleConfirmUpload = async () => {
    if (!file || !canUpload || isUploading) return;
    setError(null);
    setIsUploading(true);
    setMappingReportOpen(false);
    setStep("uploading");
    setUiStep(3);
    setStages((prev) =>
      prev.map((s, i) =>
        i <= 4 ? { ...s, progress: 100, status: "done" as const } : i === 5 ? { ...s, status: "active" as const, progress: 20 } : s,
      ),
    );
    setOverall(70);
    const start = Date.now();
    try {
      const res = await api.uploadFile(file, {
        estimatedRows: preview?.total_rows,
        onProgress: (pct) => {
          const clamped = Math.max(70, Math.min(99, Math.round(pct * 0.29 + 70)));
          setOverall(clamped);
          setStages((prev) =>
            prev.map((s, i) =>
              i === 5
                ? { ...s, status: "active" as const, progress: Math.max(20, Math.round(pct)), eta: pct > 0 ? "processing" : "~minutes" }
                : s,
            ),
          );
        },
      });
      setProcessingMs(Date.now() - start);
      setResult(res);
      setUiStep(4);
      setStep("done");
      setStages((prev) => prev.map((s) => ({ ...s, progress: 100, status: "done" as const })));
      setOverall(100);
      await refreshDashboards();
      await refreshExecutive();
    } catch (e) {
      const message = e instanceof Error ? e.message : "Upload failed";
      setError(
        message.includes("Invalid or expired token")
          ? "Session expired. Refresh the page and try again — local dev no longer requires login."
          : message.includes("timed out while waiting for the background job")
          ? "Browser wait timed out, but the upload may still be processing on the server. Refresh this page and check Recent Uploads — do not re-upload the same file."
          : message.includes("socket hang up") || message.includes("ECONNRESET")
          ? "Upload timed out in the browser proxy. If processing continued on the server, refresh and check Recent Uploads."
          : message,
      );
      setStep("preview");
    } finally {
      setIsUploading(false);
    }
  };

  const reset = () => {
    setStep("idle");
    setUiStep(0);
    setFile(null);
    setPreview(null);
    setResult(null);
    setStages(initStages());
    setOverall(0);
    setError(null);
    setIsUploading(false);
    setMappingReportOpen(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader subtitle="Import customer files with automatic field mapping, validation, and intelligence generation." />

      {uploadProfile && (uploadProfile.bulk_upload_mode || uploadProfile.customer_analysis_only) && (
        <section className="cios-card border-blue-200 bg-blue-50/80 p-4 text-sm text-blue-950">
          <p className="font-semibold">Large-scale upload profile active</p>
          {systemHealth && (
            <p className="mt-1 text-xs font-medium">
              Database: {systemHealth.postgres ? "PostgreSQL" : systemHealth.dbDriver ?? "unknown"}
              {systemHealth.readyFor2_5m ? " · ready for 2.5M async upload" : " · switch to PostgreSQL + worker for 2.5M scale"}
            </p>
          )}
          <p className="mt-1 text-blue-900/90">
            {uploadProfile.upload_async ? "Async background processing" : "Synchronous processing"} · Bulk threshold{" "}
            {uploadProfile.bulk_upload_row_threshold.toLocaleString()} rows
            {uploadProfile.bulk_active_for_estimate && preview ? " · applies to this file" : ""}
          </p>
          <ul className="mt-2 list-inside list-disc text-xs text-blue-900/80">
            <li>Raw row storage: {uploadProfile.store_raw_rows ? "on" : "off (slim DB)"}</li>
            <li>Full intelligence trace: {uploadProfile.store_full_trace ? "on" : "off (slim DB)"}</li>
            <li>Version history: {uploadProfile.record_intelligence_versions ? "on" : "off"}</li>
          </ul>
          {uploadProfile.customer_analysis_only && (
            <p className="mt-2 text-xs font-medium text-blue-900">
              Customer analysis only — campaign modules hidden in navigation.
            </p>
          )}
        </section>
      )}

      <div className="flex flex-wrap gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <span
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold",
                i <= uiStep ? "bg-[var(--cios-primary)] text-white" : "bg-gray-200 text-gray-500",
              )}
            >
              {i + 1}
            </span>
            <span className={cn("text-sm", i <= uiStep ? "font-medium text-gray-900" : "text-[var(--cios-secondary)]")}>
              {label}
            </span>
            {i < STEPS.length - 1 && <span className="mx-1 text-gray-300">→</span>}
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-8">
          {(step === "idle" || step === "preview") && (
            <UploadDropZone onFileSelected={handleFileSelected} disabled={step === "preview" && !canUpload} />
          )}
          {error && <p className="text-sm text-[var(--cios-error)]">{error}</p>}
          {(step === "uploading" || step === "done") && <UploadProgressPanel stages={stages} overall={overall} />}
          {preview && step !== "done" && (
            <>
              {step === "preview" && preview.detected_headers && preview.detected_headers.length > 0 && (
                <section className="cios-card p-5">
                  <h2 className="text-base font-semibold text-gray-900">Detected Headers</h2>
                  <p className="mt-2 text-sm text-[var(--cios-secondary)]">{preview.detected_headers.join(" · ")}</p>
                </section>
              )}
              <MappingReportPanel
                rows={preview.mapping_report ?? []}
                summary={preview.mapping_summary}
                collapsible
                open={mappingReportOpen}
                onOpenChange={setMappingReportOpen}
              />
              {step === "preview" && (
                <ValidationSummaryPanel
                  totalRows={preview.total_rows}
                  duplicateEmail={preview.stats.duplicate_email}
                  duplicateEmailInDb={preview.stats.duplicate_email_in_db}
                  invalidEmail={preview.stats.invalid_email}
                  missingZip={preview.stats.missing_zip}
                  missingState={preview.stats.missing_state}
                  unknownFields={preview.stats.unknown_fields}
                  fatalErrors={preview.fatal_errors ?? []}
                  warnings={preview.warnings ?? []}
                />
              )}
              {step === "preview" && (
                <div className="flex flex-col gap-3">
                  {mostlyDuplicates && (
                    <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                      Most rows in this file are already in the database. Upload will complete successfully but import{" "}
                      <strong>0 new customers</strong> — duplicates are skipped. Progress still advances while rows are scanned.
                    </p>
                  )}
                  <p className="text-sm text-[var(--cios-secondary)]">
                    Large files are processed in the background. Keep this page open to track progress, or return later from Recent Uploads.
                  </p>
                  <div className="flex gap-3">
                  <button
                    type="button"
                    disabled={!canUpload || isUploading}
                    onClick={handleConfirmUpload}
                    className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white hover:opacity-90 disabled:opacity-50"
                  >
                    {isUploading ? "Processing…" : "Upload & Process"}
                  </button>
                  <button type="button" onClick={reset} disabled={isUploading} className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2 disabled:opacity-50">
                    Cancel
                  </button>
                  </div>
                </div>
              )}
            </>
          )}
          {step === "done" && result && (
            <>
              <UploadResultPanel fileName={result.file_name} summary={result.summary} processingMs={processingMs} />
              <button type="button" onClick={reset} className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2">
                Upload Another File
              </button>
            </>
          )}
        </div>

        <aside className="cios-card space-y-4 p-5 lg:col-span-4">
          <h2 className="text-base font-semibold text-gray-900">Upload Guidelines</h2>
          <ul className="space-y-2 text-sm text-[var(--cios-secondary)]">
            <li>CSV or Excel format, UTF-8 encoding</li>
            <li>Maximum file size 100 MB</li>
            <li>Required: Email (auto-mapped to email_address)</li>
            <li>State, ZIP, and Datalogix fields mapped automatically</li>
            <li>Unknown headers are logged — upload is not blocked</li>
          </ul>
          <h3 className="pt-2 text-sm font-semibold text-gray-900">Recent Uploads</h3>
          <table className="w-full text-xs">
            <thead className="text-[var(--cios-secondary)]">
              <tr>
                <th className="py-1 text-left">File</th>
                <th className="py-1 text-right">Records</th>
              </tr>
            </thead>
            <tbody>
              {recentUploads.length === 0 ? (
                <tr>
                  <td colSpan={2} className="py-3 text-[var(--cios-secondary)]">
                    No uploads yet
                  </td>
                </tr>
              ) : (
                recentUploads.slice(0, 5).map((u) => (
                  <tr key={u.id} className="border-t border-gray-100">
                    <td className="py-2">
                      <p className="font-medium text-gray-800">{u.file_name}</p>
                      <p className="text-[var(--cios-secondary)]">{formatDateTimeEST(u.created_at)}</p>
                    </td>
                    <td className="py-2 text-right align-top">
                      <p>{u.total_rows.toLocaleString()}</p>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1",
                          u.status === "completed" ? "text-[var(--cios-success)]" : u.status === "failed" ? "text-[var(--cios-error)]" : "text-[var(--cios-primary)]",
                        )}
                      >
                        {u.status === "processing" || u.status === "pending" ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <CheckCircle2 className="h-3 w-3" />
                        )}
                        {u.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          {SHOW_CAMPAIGN_MODULES ? (
            <Link href="/campaign-center" className="text-sm text-[var(--cios-primary)] hover:underline">
              Return to Campaign Center
            </Link>
          ) : (
            <Link href="/dashboard" className="text-sm text-[var(--cios-primary)] hover:underline">
              Return to Executive Dashboard
            </Link>
          )}
        </aside>
      </div>
    </div>
  );
}
