import type { UploadSummary } from "@/lib/api";

export function uploadRowCount(upload: UploadSummary): number {
  const summary = upload.summary ?? {};
  const processed = summary.rows_processed;
  if (typeof processed === "number" && processed > 0) return processed;
  return upload.total_rows ?? 0;
}

/** Keep current selection when still usable; otherwise fall back to all uploads (aggregate DB totals). */
export function resolveUploadSelection(list: UploadSummary[], current: string | null): string | null {
  if (!current) return null;
  const selected = list.find((u) => u.id === current);
  if (isUploadUsable(selected)) return current;
  return null;
}

/** Prefer the completed prospect upload with the most imported rows (skip failed/empty/buyer batches). */
export function pickDefaultUploadId(list: UploadSummary[]): string | null {
  const candidates = list.filter(
    (u) =>
      u.status === "completed" &&
      uploadRowCount(u) > 0 &&
      (u.dataset_type ?? "prospect") === "prospect",
  );
  if (!candidates.length) return null;
  candidates.sort((a, b) => uploadRowCount(b) - uploadRowCount(a));
  return candidates[0]?.id ?? null;
}

export function isUploadUsable(upload: UploadSummary | undefined): boolean {
  if (!upload) return false;
  if (upload.status === "failed") return false;
  if ((upload.dataset_type ?? "prospect") !== "prospect") return false;
  return upload.status === "completed" && uploadRowCount(upload) > 0;
}
