const TOKEN_KEY = "cios_auth_token";
const SESSION_KEY = "cios_auth_session";

type ApiEnvelope<T> = { success: boolean; data?: T; message?: string; error?: { message?: string } };

export type AuthSession = {
  email: string;
  name: string;
  role: string;
  modules?: string[];
  allowedMenus?: string[] | null;
};

function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured) return `${configured}/api/v1`;

  if (typeof window !== "undefined") {
    return "http://127.0.0.1:8000/api/v1";
  }

  const backend = process.env.BACKEND_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";
  return `${backend}/api/v1`;
}

const inflightGets = new Map<string, Promise<unknown>>();

async function fetchJsonDeduped<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? "GET").toUpperCase();
  if (method !== "GET") {
    return fetchJson<T>(path, init);
  }
  const key = `${method}:${path}`;
  const existing = inflightGets.get(key);
  if (existing) {
    return existing as Promise<T>;
  }
  const promise = fetchJson<T>(path, init).finally(() => {
    inflightGets.delete(key);
  });
  inflightGets.set(key, promise);
  return promise;
}

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null) return fallback;
  const record = body as Record<string, unknown>;
  if (typeof record.detail === "string" && record.detail) return record.detail;
  if (typeof record.detail === "object" && record.detail !== null) {
    const detail = record.detail as Record<string, unknown>;
    if (typeof detail.message === "string" && detail.message) return detail.message;
  }
  if (typeof record.message === "string" && record.message) return record.message;
  const nested = record.error;
  if (typeof nested === "object" && nested !== null && typeof (nested as { message?: string }).message === "string") {
    return (nested as { message: string }).message;
  }
  return fallback;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = { ...getAuthHeaders(), ...(init?.headers ?? {}) };
  let res: Response;
  try {
    res = await fetch(`${getApiBase()}${path}`, { ...init, headers });
  } catch (err) {
    const hint =
      typeof window !== "undefined" && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost"
        ? " Open the app at http://localhost:3002 or http://127.0.0.1:3002 and ensure the backend is running on port 8000."
        : " Ensure the backend is running (port 8000) and try refreshing the page.";
    const message = err instanceof Error ? err.message : "Network request failed";
    throw new Error(message === "Failed to fetch" ? `Failed to fetch — cannot reach the API.${hint}` : message);
  }
  const raw = await res.text();
  let body: ApiEnvelope<T> | T | null = null;
  if (raw) {
    try {
      body = JSON.parse(raw) as ApiEnvelope<T> | T;
    } catch {
      throw new Error(raw || `Request failed: ${res.status}`);
    }
  }
  if (!res.ok) {
    const message = extractErrorMessage(body, raw || `Request failed: ${res.status}`);
    if (res.status === 401 && typeof window !== "undefined") {
      api.clearSession();
    }
    throw new Error(message);
  }
  if (typeof body === "object" && body !== null && "success" in body) {
    const envelope = body as ApiEnvelope<T>;
    if (!envelope.success) {
      throw new Error(extractErrorMessage(envelope, envelope.message ?? "Request failed"));
    }
    return envelope.data as T;
  }
  return body as T;
}

function mapCustomerRow(row: Record<string, unknown>): CustomerRow {
  return {
    id: String(row.id),
    email: (row.email as string) ?? null,
    name: (row.name as string) ?? null,
    state: (row.state as string) ?? null,
    zip: (row.zip as string) ?? null,
    prizm_proxy_segment: (row.prizmProxySegment as string) ?? (row.prizm_proxy_segment as string) ?? null,
    ceragem_segment: (row.ceragemSegment as string) ?? (row.ceragem_segment as string) ?? null,
    message_direction: (row.messageDirection as string) ?? (row.message_direction as string) ?? null,
    recommended_product: (row.recommendedProduct as string) ?? (row.recommended_product as string) ?? null,
    expected_conversion_rate: (row.expectedConversion as number) ?? (row.expected_conversion_rate as number) ?? null,
    expected_revenue: (row.expectedRevenue as number) ?? (row.expected_revenue as number) ?? null,
    campaign_priority: (row.campaignPriorityValue as number) ?? (row.campaign_priority as number) ?? null,
    purchase_power_index: (row.purchasePowerIndex as number) ?? (row.purchase_power_index as number) ?? null,
    pain_index: (row.painIndexValue as number) ?? (row.pain_index as number) ?? null,
    lifestyle_index: (row.lifestyleIndex as number) ?? (row.lifestyle_index as number) ?? null,
    email_response_index: (row.emailResponseIndex as number) ?? (row.email_response_index as number) ?? null,
    brand_familiarity_index: (row.brandFamiliarityIndex as number) ?? (row.brand_familiarity_index as number) ?? null,
    sleep_segment: (row.sleepSegment as string) ?? (row.sleep_segment as string) ?? null,
    sleep_segment_label: (row.sleepSegmentLabel as string) ?? (row.sleep_segment_label as string) ?? null,
    recommendation_rationale_summary:
      (row.recommendationRationaleSummary as string) ?? (row.recommendation_rationale_summary as string) ?? null,
  };
}

export const api = {
  hasStoredToken: (): boolean => {
    if (typeof window === "undefined") return false;
    return Boolean(localStorage.getItem(TOKEN_KEY));
  },
  persistSession: (session: AuthSession) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  },
  readStoredSession: (): AuthSession | null => {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthSession;
    } catch {
      return null;
    }
  },
  clearSession: () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
  },
  login: async (email: string, password: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    const res = await fetch(`${getApiBase()}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: normalizedEmail, password }),
    });
    const body = (await res.json()) as ApiEnvelope<{ token: string; expires: string; role: string; email?: string; name?: string }>;
    if (!res.ok || !body.success || !body.data) throw new Error(body.message ?? "Login failed");
    localStorage.setItem(TOKEN_KEY, body.data.token);
    try {
      const me = await fetchJson<AuthSession & { modules: string[]; allowedModules: string[] | null }>("/auth/me");
      const session: AuthSession = {
        ...me,
        allowedMenus:
          me.allowedModules?.length && me.allowedModules[0]?.startsWith("/") ? me.allowedModules : null,
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
      return session;
    } catch {
      const session: AuthSession = {
        email: body.data.email ?? normalizedEmail,
        name: body.data.name ?? normalizedEmail.split("@")[0],
        role: body.data.role ?? "Read Only",
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
      return session;
    }
  },
  logout: () => {
    api.clearSession();
  },
  getAuthMe: () =>
    fetchJson<AuthSession & { modules: string[]; allowedModules: string[] | null }>("/auth/me"),
  getHealth: () =>
    fetchJson<{
      database?: { status?: string; postgres?: boolean; url_scheme?: string };
      upload_pipeline?: { async?: boolean; bulk_mode?: boolean; customer_analysis_only?: boolean; ready_for_2_5m?: boolean };
    }>("/health"),
  getUploads: (datasetType?: "prospect" | "buyer") =>
    fetchJsonDeduped<{ uploads: UploadSummary[] }>(
      `/uploads${datasetType ? `?dataset_type=${datasetType}` : ""}`,
    ).then((d) => d.uploads ?? (d as unknown as UploadSummary[])),
  getUploadProcessingProfile: (estimatedRows?: number) =>
    fetchJson<UploadProcessingProfile>(
      `/uploads/processing-profile${estimatedRows != null ? `?estimated_rows=${estimatedRows}` : ""}`,
    ),
  getUploadStatus: (uploadId: string) => fetchJson<UploadStatus>(`/upload/${uploadId}`),
  cancelUpload: (uploadId: string) =>
    fetchJson<UploadStatus>(`/upload/${uploadId}/cancel`, { method: "POST" }),
  previewUpload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchJson<UploadPreview>("/customers/upload/preview", { method: "POST", body: form });
  },
  uploadFile: async (
    file: File,
    options?: { sync?: boolean; onProgress?: (pct: number) => void; estimatedRows?: number },
  ) => {
    const form = new FormData();
    form.append("file", file);
    const query = options?.sync ? "?sync=true" : "";
    const data = await fetchJson<{
      status: string;
      uploadId: string;
      customers: number;
      updated: number;
      warnings: number;
      fileName: string;
      totalRows?: number;
      progressPct?: number;
      async?: boolean;
    }>(`/customers/upload${query}`, { method: "POST", body: form });

    if (data.status === "pending" || data.status === "processing") {
      const rowEstimate = options?.estimatedRows ?? data.totalRows ?? data.customers;
      const pollTimeoutMs = uploadPollTimeoutMs(rowEstimate);
      const finalStatus = await pollUploadStatus(data.uploadId, options?.onProgress, 2000, pollTimeoutMs);
      return {
        upload_id: data.uploadId,
        file_name: data.fileName,
        status: finalStatus.status,
        summary: {
          rows_processed: finalStatus.customers,
          duplicates_updated: finalStatus.updated,
          total_rows: finalStatus.totalRows || finalStatus.customers,
          invalid_emails: finalStatus.warnings,
        },
      } satisfies UploadResult;
    }

    return {
      upload_id: data.uploadId,
      file_name: data.fileName,
      status: data.status,
      summary: {
        rows_processed: data.customers,
        duplicates_updated: data.updated,
        total_rows: data.totalRows || data.customers,
        invalid_emails: data.warnings,
      },
    } satisfies UploadResult;
  },
  previewBuyerUpload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchJson<BuyerUploadPreview>("/buyers/upload/preview", { method: "POST", body: form });
  },
  uploadBuyerFile: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchJson<BuyerUploadResult>("/buyers/upload", { method: "POST", body: form });
  },
  getBuyerGapReport: (uploadId: string) => fetchJson<BuyerGapReport>(`/buyers/upload/${uploadId}/gap-report`),
  getBuyerProspectMatchStats: () => fetchJson<BuyerProspectMatchStats>("/buyers/prospect-match-stats"),
  deleteBuyerUpload: async (uploadId: string) => {
    try {
      return await fetchJson<{ deleted: string }>(`/buyers/upload/${uploadId}`, { method: "DELETE" });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Delete failed";
      if (message === "Not Found" || /404/.test(message)) {
        return fetchJson<{ deleted: string }>(`/upload/${uploadId}`, { method: "DELETE" });
      }
      throw err;
    }
  },
  downloadBuyerMatchedCsv: async (uploadId: string) => {
    const res = await fetch(`${getApiBase()}/buyers/upload/${uploadId}/matched-download`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const raw = await res.text();
      let message = raw || `Download failed: ${res.status}`;
      try {
        const body = JSON.parse(raw) as { message?: string; detail?: string | { message?: string } };
        if (typeof body.detail === "object" && body.detail?.message) {
          message = body.detail.message;
        } else if (typeof body.detail === "string" && body.detail) {
          message = body.detail;
        } else if (body.message) {
          message = body.message;
        }
      } catch {
        // keep raw message
      }
      throw new Error(message);
    }
    const blob = await res.blob();
    if (!blob.size) {
      throw new Error("Download returned an empty file.");
    }
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `buyer_matched_${uploadId.slice(0, 8)}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  },
  uploadCampaignReport: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const data = await fetchJson<{
      reportId: string;
      campaignId: string | null;
      status: string;
      summary: Record<string, unknown>;
    }>("/report/upload", { method: "POST", body: form });
    return {
      report_id: data.reportId,
      file_name: file.name,
      campaign_id: data.campaignId,
      campaign_name: data.campaignId,
      status: data.status,
      summary: data.summary,
    } satisfies CampaignReportResult;
  },
  getExecutive: (uploadId?: string) =>
    fetchJsonDeduped<ExecutiveSummary>(`/dashboard/executive${uploadId ? `?upload_id=${uploadId}` : ""}`),
  getPurchasesDashboard: () => fetchJsonDeduped<PurchaseDashboard>("/dashboard/purchases"),
  getPromotionCoverage: (uploadId?: string) =>
    fetchJson<PromotionCoverageSnapshot>(
      `/dashboard/promotion-coverage${uploadId ? `?upload_id=${uploadId}` : ""}`,
    ),
  getCustomers: async (uploadId?: string) => {
    const data = await fetchJsonDeduped<CustomerDashboard>(`/dashboard/customer${uploadId ? `?upload_id=${uploadId}` : ""}`);
    return {
      ...data,
      customers: {
        ...data.customers,
        items: data.customers.items.map((r) => mapCustomerRow(r as unknown as Record<string, unknown>)),
      },
    };
  },
  getCustomerIntelligence: (customerId: string) =>
    fetchJson<CustomerIntelligenceDetail>(`/intelligence/customer/${encodeURIComponent(customerId)}`),
  getCustomerRecommendation: (customerId: string) =>
    fetchJson<CustomerRecommendationDetail>(`/intelligence/recommendation/${encodeURIComponent(customerId)}`),
  getIntelligenceFramework: (customerId: string) =>
    fetchJson<IntelligenceFrameworkDetail>(`/intelligence/framework/${encodeURIComponent(customerId)}`),
  getRetail: (params?: Record<string, string>) => {
    const qs = params ? `?${new URLSearchParams(params)}` : "";
    return fetchJson<RetailIntelligence>(`/dashboard/customer${qs}`);
  },
  getCampaigns: (campaignId?: string) =>
    fetchJson<CampaignDashboard>(`/dashboard/campaigns${campaignId ? `?campaign_id=${campaignId}` : ""}`),
  getCampaignDetail: (campaignId: string) =>
    fetchJson<CampaignDetail>(`/report/dashboard/${encodeURIComponent(campaignId)}`),
  createCampaign: async (campaignName: string, campaignType = "Email") => {
    const data = await fetchJson<{ campaignId: string; campaignName: string; status: string }>("/campaign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ campaignName, campaignType }),
    });
    return { campaign_id: data.campaignId, campaign_name: data.campaignName, status: data.status };
  },
  getLearningInsights: () => fetchJson<{ insights: LearningInsight[] }>("/learning/insights"),
  getStateDashboard: (uploadId?: string, state?: string, zipLimit?: number, opts?: { lite?: boolean }) => {
    const params = new URLSearchParams();
    if (uploadId) params.set("upload_id", uploadId);
    if (state) params.set("state", state);
    if (zipLimit != null) params.set("zip_limit", String(zipLimit));
    if (opts?.lite) params.set("lite", "true");
    const qs = params.toString();
    return fetchJsonDeduped<StateDashboard>(`/dashboard/state${qs ? `?${qs}` : ""}`);
  },
  getMetroDashboard: (uploadId?: string, cbsa?: string) => {
    const params = new URLSearchParams();
    if (uploadId) params.set("upload_id", uploadId);
    if (cbsa) params.set("cbsa", cbsa);
    const qs = params.toString();
    return fetchJsonDeduped<MetroDashboard>(`/dashboard/metro${qs ? `?${qs}` : ""}`);
  },
  getZctaChoropleth: (state: string, uploadId?: string) => {
    const params = new URLSearchParams({ state });
    if (uploadId) params.set("upload_id", uploadId);
    return fetchJson<ZctaChoropleth>(`/geo/zcta?${params}`);
  },
  getMetroZctaChoropleth: (cbsa: string, uploadId?: string) => {
    const params = new URLSearchParams({ cbsa });
    if (uploadId) params.set("upload_id", uploadId);
    return fetchJson<ZctaChoropleth>(`/geo/zcta?${params}`);
  },
  getZipDashboard: (uploadId?: string, zip?: string) => {
    const params = new URLSearchParams();
    if (uploadId) params.set("upload_id", uploadId);
    if (zip) params.set("zip", zip);
    const qs = params.toString();
    return fetchJsonDeduped<ZipDashboard>(`/dashboard/zip${qs ? `?${qs}` : ""}`);
  },
  getProductDashboard: (uploadId?: string, product?: string) => {
    const params = new URLSearchParams();
    if (uploadId) params.set("upload_id", uploadId);
    if (product) params.set("product", product);
    const qs = params.toString();
    return fetchJsonDeduped<ProductDashboard>(`/dashboard/product${qs ? `?${qs}` : ""}`);
  },
  getRoiDashboard: () => fetchJson<RoiDashboard>("/dashboard/roi"),
  getExportPreview: (params: Record<string, string>) =>
    fetchJson<ExportPreview>(`/export/preview?${new URLSearchParams(params)}`),
  getSettings: () => fetchJson<SettingsInfo>("/settings"),
  getAdminDashboard: () => fetchJson<AdminDashboard>("/admin/dashboard"),
  getAdminMetrics: () => fetchJson<OperationalMetrics>("/admin/metrics"),
  getDailyChecklist: () => fetchJson<OpsChecklist>("/admin/checklists/daily"),
  getEndOfDayChecklist: () => fetchJson<OpsChecklist>("/admin/checklists/end-of-day"),
  getAdminUsers: () => fetchJson<{ users: AdminUser[]; roles: string[] }>("/admin/users"),
  createAdminUser: (payload: {
    email: string;
    password: string;
    name: string;
    role: string;
    allowedModules?: string[] | null;
  }) =>
    fetchJson<AdminUser>("/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  updateAdminUser: (
    email: string,
    payload: {
      email?: string;
      name?: string;
      role?: string;
      menuAccessMode?: "role" | "custom";
      allowedModules?: string[] | null;
    },
  ) =>
    fetchJson<AdminUser>(`/admin/users/${encodeURIComponent(email)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  assignUserRole: (email: string, role: string) =>
    fetchJson<{ email: string; role: string }>(`/admin/users/${encodeURIComponent(email)}/role`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    }),
  resetUserPassword: (email: string, password: string) =>
    fetchJson<{ email: string }>(`/admin/users/${encodeURIComponent(email)}/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    }),
  disableAdminUser: (email: string) =>
    fetchJson<{ email: string; isActive: boolean }>(`/admin/users/${encodeURIComponent(email)}/disable`, { method: "POST" }),
  activateAdminUser: (email: string) =>
    fetchJson<{ email: string; isActive: boolean }>(`/admin/users/${encodeURIComponent(email)}/activate`, { method: "POST" }),
  unlockAdminUser: (email: string) =>
    fetchJson<{ email: string }>(`/admin/users/${encodeURIComponent(email)}/unlock`, { method: "POST" }),
  deleteAdminUser: (email: string) =>
    fetchJson<{ email: string; deleted: boolean }>(`/admin/users/${encodeURIComponent(email)}`, { method: "DELETE" }),
  createExport: async (opts: {
    provider: string;
    campaignName: string;
    campaignId: string;
    uploadId?: string;
    stateFilter?: string;
    segmentFilter?: string;
    productFilter?: string;
  }) => {
    const queued = await fetchJson<{ exportId: string; status: string }>("/export", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({
        provider: opts.provider,
        campaignName: opts.campaignName,
        campaignId: opts.campaignId,
        uploadId: opts.uploadId,
        stateFilter: opts.stateFilter,
        segmentFilter: opts.segmentFilter,
        productFilter: opts.productFilter,
      }),
    });
    const finalStatus = await pollExportStatus(queued.exportId);
    const downloadPath = finalStatus.downloadUrl ?? `/export/download/${queued.exportId}`;
    const fileUrl = downloadPath.startsWith("http") ? downloadPath : `${getApiBase()}${downloadPath}`;
    return { export_id: queued.exportId, file_url: fileUrl, status: finalStatus.status };
  },
  simulateCommercial: (body: {
    product?: string;
    products?: string[];
    additionalProducts?: string[];
    targetCustomers?: number;
    targetCustomersBySku?: { sku: string; count: number }[];
    sellingPrice?: number;
    promotionPct?: number;
    maxPromotion?: number;
    additionalPromotionPct?: number;
    additionalPromotionMax?: number;
    promoCode?: string;
    leFrameIncentiveRate?: number;
    corporatePriority?: number;
    inventoryUnits?: number;
    conversionRate?: number;
  }) =>
    fetchJson<CommercialSimulationResult>("/commercial/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
    }),
  analyzeAudienceExport: async (
    file: File,
    opts?: {
      corporatePriority?: number;
      leFrameRate?: number;
      inventoryUnits?: number;
      conversionRate?: number;
    },
  ) => {
    const form = new FormData();
    form.append("file", file);
    if (opts?.corporatePriority != null) form.append("corporatePriority", String(opts.corporatePriority));
    if (opts?.leFrameRate != null) form.append("leFrameIncentiveRate", String(opts.leFrameRate));
    if (opts?.inventoryUnits != null) form.append("inventoryUnits", String(opts.inventoryUnits));
    if (opts?.conversionRate != null) form.append("conversionRate", String(opts.conversionRate));
    return fetchJson<AudienceExportAnalysisResult>("/commercial/simulate/audience-upload", {
      method: "POST",
      body: form,
    });
  },
  saveCommercialSimulatorForecast: (body: CommercialSimulatorForecastSaveRequest) =>
    fetchJson<CommercialSimulatorForecastRecord>("/commercial/simulator/forecasts", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
    }),
  listCommercialSimulatorForecasts: () =>
    fetchJsonDeduped<{ items: CommercialSimulatorForecastSummary[] }>("/commercial/simulator/forecasts"),
  getCommercialSimulatorForecast: (id: string) =>
    fetchJson<CommercialSimulatorForecastRecord>(`/commercial/simulator/forecasts/${id}`),
  deleteCommercialSimulatorForecast: (id: string) =>
    fetchJson<{ deleted: boolean; id: string }>(`/commercial/simulator/forecasts/${id}`, {
      method: "DELETE",
    }),
  getCommercialVersions: () => fetchJson<{ versions: CommercialCatalogVersion[] }>("/commercial/versions"),
  getCommercialCatalog: () => fetchJsonDeduped<CommercialCatalogSnapshot>("/commercial/catalog"),
  saveCommercialCatalog: (body: { products: CommercialCatalogProduct[]; notes?: string; publish?: boolean }) =>
    fetchJson<CommercialCatalogSaveResult>("/commercial/catalog", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  simulateCampaignOpportunity: (body: CampaignOpportunitySimulateRequest) =>
    fetchJson<CampaignOpportunitySimulateResult>("/campaign/opportunity-simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
    }),
  listAudienceExports: () => fetchJsonDeduped<{ items: AudienceExportRecommendation[] }>("/audience-exports"),
  saveAudienceExport: (body: AudienceExportCreateRequest) =>
    fetchJson<AudienceExportRecommendation>("/audience-exports", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
    }),
  deleteAudienceExport: (id: string) =>
    fetchJson<{ deleted: boolean; id: string }>(`/audience-exports/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    }),
  downloadAudienceExport: async (id: string, fileName?: string) => {
    const res = await fetch(`${getApiBase()}/audience-exports/${id}/download`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const raw = await res.text();
      let message = raw || `Download failed: ${res.status}`;
      try {
        const body = JSON.parse(raw) as { message?: string; detail?: string | { message?: string } };
        if (typeof body.detail === "object" && body.detail?.message) {
          message = body.detail.message;
        } else if (typeof body.detail === "string" && body.detail) {
          message = body.detail;
        } else if (body.message) {
          message = body.message;
        }
      } catch {
        // keep raw message
      }
      throw new Error(message);
    }
    const blob = await res.blob();
    if (!blob.size) {
      throw new Error("Export returned an empty file.");
    }
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName || `audience_export_${id.slice(0, 8)}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  },
  downloadCommercialPriceGuide: () => `${getApiBase()}/commercial/price-guide`,
  importCommercialPriceGuide: async (file: File, version?: string, notes?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (version) form.append("version", version);
    if (notes) form.append("notes", notes);
    return fetchJson<{ ok: boolean; version_id: string; version: string; status: string; sku_count: number }>(
      "/commercial/price-guide/import",
      { method: "POST", body: form },
    );
  },
  approveCommercialVersion: (versionId: string) =>
    fetchJson<{ ok: boolean; version: string; status: string }>(`/commercial/versions/${versionId}/approve`, {
      method: "POST",
    }),
};

async function pollExportStatus(
  exportId: string,
  intervalMs = 1500,
  timeoutMs = 30 * 60 * 1000,
): Promise<{ status: string; downloadUrl?: string | null; customerCount?: number | null; error?: string | null }> {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const status = await fetchJson<{
      status: string;
      downloadUrl?: string | null;
      customerCount?: number | null;
      error?: string | null;
    }>(`/export/${exportId}/status`);
    if (status.status === "completed" || status.status === "failed") {
      if (status.status === "failed") {
        throw new Error(status.error || "Export failed");
      }
      return status;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error("Export timed out");
}

function uploadPollTimeoutMs(estimatedRows?: number): number {
  const baseMs = 6 * 60 * 60 * 1000;
  if (!estimatedRows || estimatedRows <= 0) return baseMs;
  // ~400 rows/min observed on bulk loads; allow 2x buffer for intelligence + rollup.
  const minutes = (estimatedRows / 400) * 2;
  return Math.max(baseMs, minutes * 60 * 1000);
}

async function pollUploadStatus(
  uploadId: string,
  onProgress?: (pct: number) => void,
  intervalMs = 2000,
  timeoutMs = 6 * 60 * 60 * 1000,
): Promise<UploadStatus> {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const status = await fetchJson<UploadStatus>(`/upload/${uploadId}`);
    onProgress?.(status.progressPct ?? 0);
    if (status.status === "completed" || status.status === "failed") {
      if (status.status === "failed") {
        throw new Error(status.error || "Upload processing failed");
      }
      return status;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error("Upload processing timed out while waiting for the background job.");
}

export type UploadStatus = {
  uploadId: string;
  status: string;
  fileName: string;
  customers: number;
  totalRows: number;
  updated: number;
  warnings: number;
  progressPct: number;
  error?: string | null;
  storageProfile?: string | null;
  createdAt?: string | null;
  completedAt?: string | null;
};

export type UploadProcessingProfile = {
  upload_async: boolean;
  bulk_upload_mode: boolean;
  bulk_upload_row_threshold: number;
  customer_analysis_only: boolean;
  bulk_active_for_estimate: boolean;
  store_raw_rows: boolean;
  store_full_trace: boolean;
  record_intelligence_versions: boolean;
  progress_update_rows: number;
  recommended_for_2_5m: Record<string, unknown>;
};

export type UploadSummary = {
  id: string;
  file_name: string;
  dataset_type?: "prospect" | "buyer" | string;
  total_rows: number;
  valid_emails: number;
  status: string;
  created_at: string | null;
  summary: Record<string, unknown> | null;
};

export type UploadResult = {
  upload_id: string;
  file_name: string;
  status: string;
  summary: Record<string, unknown>;
};

export type BuyerUploadPreview = {
  file_name: string;
  total_rows: number;
  chair_rows: number;
  unique_emails: number;
  sku_distribution: Record<string, number>;
  detected_format: string;
  fatal_errors: string[];
  warnings: string[];
  sample_headers?: string[];
};

export type BuyerUploadResult = {
  upload_id: string;
  file_name: string;
  status: string;
  matched_emails: number;
  unique_emails: number;
  match_rate_pct: number;
  summary: Record<string, unknown>;
  gap_report?: BuyerGapReport;
};

export type BuyerGapReport = {
  upload_id: string;
  chair_rows: number;
  unique_emails: number;
  matched_emails: number;
  matched_rows: number;
  match_rate_pct: number;
  intel_exact_hit_rate_pct?: number;
  aggregate_gap?: {
    raw_distribution_gap?: Record<string, { buyer_pct: number; prospect_pct: number; gap_points: number }>;
    reweighted_distribution_gap?: Record<string, { buyer_pct: number; prospect_pct: number; gap_points: number }>;
  };
  calibration_backlog?: Array<Record<string, unknown>>;
  state_other_rows?: number;
  reweight_ca_bias_index?: number | string | null;
};

export type BuyerProspectMatchStats = {
  buyer_unique_emails: number;
  buyer_matched_emails: number;
  buyer_match_rate_pct: number;
  prospect_emails_with_intel: number;
};

export type UploadPreview = {
  file_name: string;
  total_rows: number;
  headers: string[];
  fatal_errors: string[];
  warnings: string[];
  stats: {
    duplicate_email: number;
    duplicate_email_in_db?: number;
    invalid_email: number;
    missing_zip: number;
    missing_state: number;
    unknown_fields: number;
  };
  unknown_fields: string[];
  detected_headers?: string[];
  mapping_report: {
    uploaded_header: string;
    internal_field: string | null;
    match_type: string;
    confidence: number;
    status: string;
    suggestion?: string | null;
  }[];
  mapping_summary?: {
    total_headers: number;
    mapped: number;
    review: number;
    unknown: number;
    auto_mapped: number;
  };
  mapping_preview: { uploaded_column: string; internal_field: string | null }[];
  unmapped_columns: { uploaded_column: string; internal_field: string | null }[];
  column_map: Record<string, string>;
};

export type CampaignReportResult = {
  report_id: string;
  file_name: string;
  campaign_id: string | null;
  campaign_name: string | null;
  status: string;
  summary: Record<string, unknown>;
};

export type ExecutiveDashboardStatePerformance = {
  state: string;
  revenue: number;
  orders: number;
  customers: number;
  conversion: number;
  lifestyle_score?: number;
  purchase_power_score?: number;
  purchase_power_index_score?: number;
  purchase_power_tier?: string;
  purchase_power_geo_score?: number;
  pain_index_score?: number;
  lifestyle_tier?: string;
  lifestyle_geo_score?: number;
  wellness_segment_pct?: number;
  digital_score?: number;
  digital_engagement_tier?: string;
  digital_engagement_geo_score?: number;
  digital_metro_pct?: number;
  brand_score?: number;
  brand_familiarity_tier?: string;
  brand_familiarity_geo_score?: number;
  brand_enclave_pct?: number;
  top_product?: string | null;
  opportunity_score?: number;
};

export type ExecutiveDashboardZip = {
  zip: string;
  state: string;
  revenue: number;
  orders: number;
  conversion: number;
  customers?: number;
  opportunity_score?: number;
  top_product?: string | null;
  intelligence_product?: string | null;
  promo_outreach_product?: string | null;
  baseline_conversion?: number | null;
  promo_uplift?: number | null;
  purchase_power?: string | null;
  ceragem_segment?: string | null;
  city?: string | null;
};

export type ExecutiveDashboardRadarOpportunity = {
  id: string;
  label: string;
  state: string;
  product: string;
  opportunity_score: number;
  lifestyle_score?: number;
  purchase_power_score?: number;
  purchase_power_tier?: string;
  pain_index_score?: number;
  lifestyle_tier?: string;
  digital_score?: number;
  digital_engagement_tier?: string;
  brand_score?: number;
  brand_familiarity_tier?: string;
  customers: number;
  revenue: number;
};

export type ExecutiveSummary = {
  total_customers: number;
  targetable_customers: number;
  new_customers?: number;
  expected_conversion: number;
  expected_revenue: number;
  expected_orders: number;
  conversion_rate?: number;
  predicted_conversion_rate?: number;
  baseline_conversion_rate?: number;
  promo_uplift_rate?: number;
  le_frame_incentive: number;
  campaign_roi: number | null;
  campaign_performance?: CampaignOverview;
  top_performing_state: string | null;
  top_opportunity_state?: string | null;
  top_performing_segment: string | null;
  top_product_opportunity: string | null;
  revenue_by_state: { state: string; revenue: number }[];
  revenue_by_segment: { segment: string; revenue: number }[];
  product_ranking: { product: string; revenue: number }[];
  state_performance?: ExecutiveDashboardStatePerformance[];
  radar_opportunities?: ExecutiveDashboardRadarOpportunity[];
  top_zips?: ExecutiveDashboardZip[];
  segment_performance?: { segment: string; customers: number; revenue: number; orders: number; conversion: number }[];
  product_distribution?: { product: string; revenue: number; customers: number; share_pct: number }[];
  revenue_over_time?: { day: string; revenue: number; orders: number; customers?: number; conversion_rate?: number; file_name?: string }[];
  top_campaigns?: { name: string; revenue: number; roi: number | null; sent?: number }[];
  intelligence_radar?: { axis: string; score: number }[];
  intelligence_score_distribution?: { label: string; high: number; medium: number; low: number }[];
  purchase_power_distribution?: {
    band: string;
    customers: number;
    pct: number;
    revenue: number;
    products: string[];
  }[];
  ceragem_distribution?: {
    segment: string;
    customers: number;
    pct: number;
    revenue: number;
    products: string[];
  }[];
  recent_activity?: { title: string; detail: string; time: string }[];
  system_status?: { name: string; status: string }[];
  data_source?: string;
  commercial_version?: string;
  pricing_version?: string;
  commercial_intelligence?: CommercialIntelligenceSummary;
  scoped_upload_id?: string | null;
};

export type PurchaseStateRow = {
  state: string;
  purchase_count: number;
  unique_buyers: number;
  purchase_share_pct: number;
  top_sku_token: string | null;
  shopify_count: number;
  legacy_count: number;
};

export type PurchaseRadarRow = {
  id: string;
  label: string;
  state: string;
  sku_token: string;
  product: string;
  purchase_count: number;
  unique_buyers: number;
  purchase_volume_score: number;
  state_volume_score: number;
  buyer_density_score: number;
  national_share_pct: number;
};

export type PurchaseDashboard = {
  kpis: {
    purchase_row_count: number;
    unique_buyer_emails: number;
    top_purchase_state: string | null;
    top_sku_token: string | null;
    shopify_purchase_pct: number;
    prospect_match_rate_pct: number;
  };
  purchases_by_state: PurchaseStateRow[];
  purchase_radar: PurchaseRadarRow[];
  meta: {
    other_count: number;
    other_pct: number;
    buyer_upload_batches: number;
    disclaimer: string;
  };
};

export type CommercialSkuHighlight = {
  product: string | null;
  net_profit_pct: number | null;
  net_profit: number | null;
  recommended_promotion?: number | null;
  promotion_pct?: number | null;
  promo_code?: string | null;
  standing_promotion?: boolean;
  standing_promotion_margin_pct?: number | null;
};

export type CommercialSkuKpiRow = CommercialSkuHighlight & { product: string };

export type PromotionCoverageSnapshot = {
  promotion_coverage_version: string;
  promotion_coverage: CommercialIntelligenceSummary["promotion_coverage"];
  db_customers?: number;
};

export type CommercialIntelligenceSummary = {
  commercial_version: string;
  pricing_version: string;
  kpi_basis?: string;
  active_promotions: {
    product: string;
    promo_code: string;
    max_promotion: number;
    default_promotion_pct: number | null;
    selling_price: number;
    status: string;
  }[];
  promotion_coverage: {
    product?: string | null;
    promo_code: string;
    customers: number;
    coverage_pct: number;
    projected?: boolean;
    primary_direct?: number;
    direct?: number;
    up_convert?: number;
    down_convert?: number;
    segment_in?: number;
    afford_own?: number;
    unreachable?: number;
    kpi_basis?: string;
  }[];
  promotion_coverage_version?: string;
  commercial_health_score: number;
  highest_margin_sku: CommercialSkuHighlight;
  highest_profit_sku: CommercialSkuHighlight;
  best_standing_promo_sku?: CommercialSkuHighlight;
  best_standing_promo_profit_sku?: CommercialSkuHighlight;
  highest_opportunity_sku: {
    product: string | null;
    expected_revenue: number | null;
    customers: number | null;
    customer_share_pct?: number | null;
    revenue_share_pct?: number | null;
    share_pct: number | null;
    projected?: boolean;
    segment_fit?: number | null;
    pp_accessibility?: number | null;
    weighted_conversion?: number | null;
    kpi_basis?: string | null;
  };
  expected_le_frame_revenue: number;
  expected_revenue: number;
  expected_conversion_orders: number;
  sku_commercial_kpis?: CommercialSkuKpiRow[];
};

export type CommercialCatalogVersion = {
  id: string;
  version: string;
  status: string;
  created_by: string | null;
  approved_by: string | null;
  created_at: string | null;
  approved_at: string | null;
  notes: string | null;
  sku_count: number;
};

export type CommercialCatalogProduct = {
  code: string;
  name: string;
  family: string;
  category?: string;
  segment?: string;
  msrp: number;
  selling_price?: number;
  gross_sales: number;
  max_promotion?: number;
  default_promotion_pct?: number | null;
  default_promotion_pct_display?: number | null;
  promo_code?: string | null;
  le_frame_incentive?: number;
  ceragem_cogs?: number | null;
  order?: number;
  active?: boolean;
  post_promo_price?: number;
};

export type CommercialCatalogSnapshot = {
  version: string;
  source: "registry_default" | "published_db";
  published_version_id: string | null;
  active_sku_count: number;
  products: CommercialCatalogProduct[];
  draft_versions: Array<{ id: string; version: string; created_at: string | null; sku_count: number }>;
};

export type CommercialCatalogSaveResult = {
  ok: boolean;
  version_id?: string;
  version?: string;
  status?: string;
  sku_count?: number;
  published?: boolean;
  errors?: string[];
};

export type CampaignOpportunitySimulateRequest = {
  mainSku: string;
  additionalSkus?: string[];
  states?: string[];
  segmentFilters?: {
    ceragem?: string[];
    prizm?: string[];
    lifestyle?: string[];
    pain_index?: string[];
    purchase_power?: string[];
    brand_familiarity?: string[];
  };
  uploadId?: string;
};

export type CampaignOpportunityKpis = {
  customers: number;
  revenue: number;
  orders: number;
  conversion: number;
};

export type CampaignOpportunitySimulateResult = {
  skus: string[];
  main_sku: string;
  db_potential: CampaignOpportunityKpis;
  by_sku: Array<{ product: string; customers: number; revenue: number }>;
  phase1: {
    kpis: CampaignOpportunityKpis;
    by_state: Array<{ state: string; customers: number; revenue: number; orders: number; conversion: number }>;
    sku_by_state: Array<{ state: string; customers: number; revenue: number; orders: number; conversion: number }>;
    top_metros: Array<{
      cbsa_code: string;
      cbsa_name: string;
      states: string[];
      customers: number;
      revenue: number;
      orders: number;
      conversion: number;
      opportunity_score: number;
      asian_relative_index?: number | null;
    }>;
  };
  phase2: {
    kpis: CampaignOpportunityKpis;
    segment_distributions: {
      ceragem?: Record<string, number>;
      prizm?: Record<string, number>;
      lifestyle?: Record<string, number>;
      pain_index?: Record<string, number>;
      purchase_power?: Record<string, number>;
      brand_familiarity?: Record<string, number>;
    };
  };
};

export type AudienceExportCreateRequest = {
  name?: string;
  mainSku: string;
  additionalSkus?: string[];
  states?: string[];
  segmentFilters?: CampaignOpportunitySimulateRequest["segmentFilters"];
  uploadId?: string;
  forecastCustomers: number;
  forecastRevenue: number;
  predictedConversion: number;
  expectedOrders: number;
  geoScope: string;
};

export type AudienceExportRecommendation = {
  id: string;
  name: string;
  mainSku: string;
  additionalSkus: string[];
  states: string[];
  segmentFilters?: CampaignOpportunitySimulateRequest["segmentFilters"];
  uploadId?: string | null;
  forecastCustomers: number;
  forecastRevenue: number;
  predictedConversion: number;
  expectedOrders: number;
  geoScope: string;
  createdAt?: string | null;
  createdBy?: string | null;
  downloadUrl?: string;
};

export type CommercialSimulationResult = {
  simulation: boolean;
  product: string;
  products?: string[];
  main_product?: string;
  multi_sku?: boolean;
  by_product?: CommercialSimulationProductSlice[];
  target_customers: number;
  effective_customers: number;
  opportunity_score: number;
  conversion_prediction: number;
  expected_orders: number;
  revenue_forecast: number;
  net_profit: number;
  le_frame_revenue: number;
  recommended_sku: string;
  recommended_promotion: number;
  promo_code: string | null;
  capped_promotion: boolean;
  recommended_lifestyle: string | null;
};

export type CommercialSimulationProductSlice = {
  product?: string;
  target_customers?: number;
  effective_customers?: number;
  opportunity_score?: number;
  conversion_prediction?: number;
  expected_orders?: number;
  revenue_forecast?: number;
  net_profit?: number;
  le_frame_revenue?: number;
  recommended_promotion?: number;
  promo_code?: string | null;
  capped_promotion?: boolean;
  recommended_lifestyle?: string | null;
};

export type AudienceExportAnalysisResult = {
  audience: {
    target_customers: number;
    product: string;
    campaign_name?: string | null;
    campaign_id?: string | null;
    promo_code?: string | null;
    avg_promotion?: number | null;
    promotion_pct?: number | null;
    avg_selling_price?: number | null;
    top_states: { state: string; count: number }[];
    sku_mix: { sku: string; count: number }[];
    promo_code_mix: { promo_code: string; count: number }[];
    file_rows: number;
  };
  simulation: CommercialSimulationResult;
};

export type CommercialSimulatorForecastInputs = {
  mainSku: string;
  additionalSkus: string[];
  targetCustomers: number;
  additionalPromotionPct: string;
  additionalPromotionMax: string;
  leFrameRate: string;
  conversionRate: string;
  corporatePriority: number;
  inventoryUnits: string;
  audienceFileName?: string | null;
};

export type CommercialSimulatorForecastSummary = {
  id: string;
  name: string;
  mainSku: string;
  additionalSkus: string[];
  targetCustomers: number;
  expectedOrders: number;
  revenueForecast: number;
  netProfit: number;
  conversionPrediction: number;
  opportunityScore: number;
  audienceFileName?: string | null;
  createdAt?: string | null;
  createdBy?: string | null;
};

export type CommercialSimulatorForecastRecord = CommercialSimulatorForecastSummary & {
  inputs: CommercialSimulatorForecastInputs;
  result: CommercialSimulationResult;
  audience?: AudienceExportAnalysisResult["audience"] | null;
};

export type CommercialSimulatorForecastSaveRequest = {
  name?: string;
  mainSku: string;
  additionalSkus?: string[];
  inputs: CommercialSimulatorForecastInputs;
  result: CommercialSimulationResult;
  audience?: AudienceExportAnalysisResult["audience"] | null;
  audienceFileName?: string | null;
};

export type CampaignOverview = {
  total_sent: number;
  total_open: number;
  total_click: number;
  total_revenue: number;
  total_cost: number;
  avg_roi: number | null;
  open_rate: number | null;
  ctr: number | null;
  campaign_count: number;
  total_delivered?: number;
  unique_click?: number;
  ctor?: number | null;
  expected_orders?: number;
  le_frame_incentive?: number;
};

export type CampaignMeta = {
  campaign_name: string | null;
  campaign_type: string | null;
  provider: string | null;
  start_date: string | null;
  end_date: string | null;
  status: string | null;
  budget: number | null;
  owner: string | null;
};

export type CampaignFunnelStage = { stage: string; value: number };

export type CampaignAiSummary = {
  campaign_score: number;
  business_summary: string;
  key_opportunity: string;
  key_risk: string;
  recommended_next_action: string;
};

export type CampaignDashboard = {
  campaign_overview?: CampaignMeta;
  overview: CampaignOverview;
  funnel?: CampaignFunnelStage[];
  ai_summary?: CampaignAiSummary;
  state_performance: {
    state: string;
    sent: number;
    open: number;
    click: number;
    delivered?: number;
    revenue: number;
    roi?: number | null;
    open_rate: number | null;
    ctr: number | null;
  }[];
  click_categories: { campaign_id: string; state: string | null; category: string | null; product: string | null; click_count: number; click_rate: number | null }[];
  learning_insights: LearningInsight[];
  campaigns: { campaign_id: string; campaign_name: string; sent: number; revenue: number }[];
};

export type LearningInsight = {
  id: string;
  campaign_id: string;
  campaign_name: string;
  state: string | null;
  segment: string | null;
  product: string | null;
  insight_summary: string | null;
  recommendation: string | null;
  confidence_score: number | null;
  roi: number | null;
  revenue: number | null;
  ctr?: number | null;
};

export type CustomerDashboard = {
  distribution: {
    by_state: { state: string; count: number }[];
    by_zip: { zip: string; count: number }[];
    prizm_distribution: Record<string, number>;
    ceragem_distribution: Record<string, number>;
    datalogix_online_access: Record<string, number>;
    datalogix_retail_card: Record<string, number>;
    average_indices: Record<string, number>;
  };
  customers: { total: number; items: CustomerRow[] };
};

export type CustomerRow = {
  id: string;
  email: string | null;
  name: string | null;
  state: string | null;
  zip: string | null;
  prizm_proxy_segment: string | null;
  ceragem_segment: string | null;
  message_direction: string | null;
  recommended_product: string | null;
  expected_conversion_rate: number | null;
  expected_revenue: number | null;
  campaign_priority: number | null;
  purchase_power_index: number | null;
  pain_index: number | null;
  lifestyle_index: number | null;
  email_response_index?: number | null;
  brand_familiarity_index?: number | null;
  sleep_segment?: string | null;
  sleep_segment_label?: string | null;
  recommendation_rationale_summary?: string | null;
};

export type RecommendationFactor = {
  key: string;
  label: string;
  level: string;
  score: number;
  detail?: string;
};

export type RecommendationRationale = {
  recommended_product?: string;
  selection_rule?: string;
  ceragem_segment?: string;
  prizm_proxy_segment?: string;
  campaign_strategy?: string;
  message_direction?: string;
  factors?: RecommendationFactor[];
  adjustments?: { type: string; label: string; detail?: string }[];
  sleep_segment?: string;
  sleep_segment_label?: string;
  sleep_deprivation_tier?: string;
  summary?: string;
};

export type CustomerIntelligenceDetail = {
  customerId: string;
  prizmProxy?: string;
  ceragemSegment?: string;
  purchasePower?: string;
  painIndex?: string;
  lifestyle?: string;
  digitalEngagement?: string;
  brandFamiliarity?: string;
  emailResponseIndex?: number;
  brandFamiliarityIndex?: number;
  sleepSegment?: string;
  sleepSegmentLabel?: string;
  recommendationRationale?: RecommendationRationale;
  recommendation?: {
    product?: string;
    messageDirection?: string;
    campaignPriority?: string;
    rationale?: RecommendationRationale;
    rationaleSummary?: string;
  };
  revenue?: {
    expectedConversion?: number;
    expectedRevenue?: number;
  };
  framework?: Record<string, unknown>;
};

export type CustomerRecommendationDetail = {
  customerId: string;
  recommendedProduct?: string;
  messageDirection?: string;
  campaignPriority?: string;
  expectedRevenue?: number;
  expectedConversion?: number;
  product?: {
    primary?: string;
    reason?: string[];
    factors?: RecommendationFactor[];
    selection_rule?: string;
    rationale_summary?: string;
  };
  explanation?: {
    summary?: string;
    recommendation_rationale?: RecommendationRationale;
  };
};

export type IntelligenceFrameworkDetail = {
  customerId: string;
  categories?: Record<string, { score?: number; level?: string; confidence?: number }>;
  recommendationRationale?: RecommendationRationale;
};

export type RetailIntelligence = {
  state_performance: { state: string; count: number; revenue: number }[];
  zip_heatmap: { zip: string; state: string; count: number; revenue: number }[];
  segment_revenue_matrix: { segment: string; product: string; revenue: number }[];
  opportunity_table: Record<string, unknown>[];
};

export type CityOpportunityRow = {
  city: string;
  revenue: number;
  opportunity_score: number;
  customers: number;
  orders: number;
  conversion: number;
  product?: string | null;
  top_product?: string | null;
  purchase_power?: string;
  campaign_priority?: string;
  pain_index_score?: number;
  lifestyle_index_score?: number;
};

export type StateDashboard = {
  selected_state: string | null;
  available_states: string[];
  opportunity_score?: number | null;
  kpis: {
    target_customers: number;
    expected_orders: number;
    expected_revenue: number;
    average_conversion: number;
    campaign_roi: number | null;
    le_frame_incentive: number;
  };
  state_heatmap: { state: string; revenue: number; count: number }[];
  revenue_by_city: CityOpportunityRow[];
  revenue_by_city_by_product?: Record<string, CityOpportunityRow[]>;
  segment_distribution: {
    prizm: Record<string, number>;
    ceragem: Record<string, number>;
    purchase_power: Record<string, number>;
    pain_index: Record<string, number>;
    lifestyle: Record<string, number>;
    brand_familiarity?: Record<string, number>;
  };
  campaign_history: {
    campaign_id: string;
    campaign: string;
    date: string;
    revenue: number;
    roi: number | null;
    ctr: number | null;
    conversion: number;
    status: string | null;
  }[];
  demographics?: {
    median_household_income: number | null;
    population: number | null;
    asian_population_pct: number | null;
    asian_relative_index: number | null;
    income_bands: Record<string, number>;
  };
  geo_intelligence?: {
    lifestyle_score?: number;
    lifestyle_tier?: string;
    purchase_power_score?: number;
    purchase_power_tier?: string;
    pain_index_score?: number;
    pain_index_tier?: string;
    brand_score?: number;
    brand_familiarity_tier?: string;
    brand_enclave_pct?: number;
    digital_score?: number;
    digital_engagement_tier?: string;
    opportunity_score?: number;
  };
  market_sizing?: MarketSizing;
  segment_revenue?: {
    ceragem: Record<string, { customers: number; revenue: number }>;
    pp_band: Record<string, { customers: number; revenue: number }>;
    products: Record<string, { customers: number; revenue: number; orders?: number }>;
  };
  sellable_products?: {
    product: string;
    expected_customers: number;
    expected_revenue: number;
    expected_orders: number;
  }[];
  zip_opportunity: {
    zip: string;
    city: string;
    target_customers: number;
    purchase_power: string;
    recommended_product: string | null;
    expected_revenue: number;
    campaign_priority: string;
    median_income?: number | null;
    population?: number | null;
    asian_relative_index?: number | null;
  }[];
  product_opportunity: {
    product: string;
    expected_customers: number;
    expected_orders: number;
    expected_revenue: number;
  }[];
};

export type MarketSizing = {
  tam_households: number;
  tam_population: number;
  tam_revenue_potential: number;
  tom_households: number;
  tom_revenue_potential: number;
  sam_customers: number;
  penetration_pct: number;
  expected_conversion_rate: number;
  avg_order_value: number;
  ceragem_fit_rate: number;
  purchase_power_access_rate: number;
  methodology: string;
  data_vintage: string;
};

export type MetroDashboardRow = {
  rank: number;
  cbsa_code: string;
  cbsa_name: string;
  states: string[];
  target_customers: number;
  expected_revenue: number;
  expected_orders: number;
  conversion: number;
  demographics: {
    population: number;
    median_household_income: number;
    asian_population_pct: number;
    asian_relative_index: number;
  };
  segment_distribution: {
    ceragem: Record<string, number>;
    purchase_power: Record<string, number>;
    lifestyle: Record<string, number>;
    prizm?: Record<string, number>;
    pain_index?: Record<string, number>;
    brand_familiarity?: Record<string, number>;
  };
  market_sizing: MarketSizing;
  top_product: string | null;
  top_zips: { zip: string; expected_revenue: number }[];
  sellable_products?: { product: string; expected_customers: number; expected_revenue: number; expected_orders: number }[];
  opportunity_score: number;
};

export type MetroDashboard = {
  selected_metro: MetroDashboardRow | null;
  metros: MetroDashboardRow[];
  available_metros: { cbsa_code: string; cbsa_name: string }[];
  data_vintage: string;
  rollup_source: boolean;
  live_source?: boolean;
};

export type ZctaChoropleth = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    id: string;
    properties: Record<string, unknown>;
    geometry: unknown;
  }[];
  meta: {
    state: string | null;
    cbsa?: string;
    cbsa_name?: string;
    count: number;
    scored_count?: number;
    max_revenue: number;
    geometry_source: string;
  };
};

export type ZipDashboard = {
  selected_zip: string | null;
  available_zips: string[];
  summary: {
    zip: string | null;
    city: string;
    state: string;
    median_income: number | null;
    target_customers: number;
    expected_revenue: number;
    campaign_priority: string;
  };
  income_intelligence: {
    median_income: number | null;
    top_50_income_zip: boolean;
    population: number | null;
    county: string | null;
    reference_source: string;
  };
  customer_intelligence: {
    prizm_distribution: Record<string, number>;
    ceragem_distribution: Record<string, number>;
    pain_index: Record<string, number>;
    lifestyle: Record<string, number>;
    purchase_power: Record<string, number>;
  };
  sellable_products?: {
    product: string;
    expected_customers: number;
    expected_revenue: number;
    expected_orders: number;
  }[];
  campaign_opportunity: { type: string; score: number; label: string }[];
  customers: {
    id: string;
    email: string | null;
    prizm_proxy_segment: string | null;
    ceragem_segment: string | null;
    purchase_power: string;
    recommended_product: string | null;
    campaign_priority: string;
    expected_revenue: number;
  }[];
};

export type ProductDashboard = {
  selected_product: string;
  products: string[];
  kpis: {
    expected_customers: number;
    expected_orders: number;
    expected_revenue: number;
    campaign_count: number;
    average_conversion: number;
  };
  best_states: { state: string; revenue: number; count: number }[];
  best_zips: { zip: string; revenue: number; count: number }[];
  segment_matrix: {
    ceragem_segment: string;
    prizm_segment: string;
    target_customers: number;
    expected_revenue: number;
    campaign_priority: string;
  }[];
  campaign_performance: {
    campaign_id: string;
    campaign: string;
    revenue: number;
    conversion: number | null;
    roi: number | null;
    ctr: number | null;
    status: string | null;
  }[];
};

export type RoiDashboard = {
  kpis: {
    revenue: number;
    gross_margin: number;
    roi: number | null;
    cpa: number | null;
    cpc: number | null;
    le_frame_incentive: number;
    campaign_cost: number;
    expected_revenue: number;
  };
  roi_chart: { campaign: string; roi: number; revenue: number; cost: number }[];
  revenue_breakdown: { category: string; value: number }[];
  campaign_ranking: {
    campaign_id: string;
    campaign: string;
    revenue: number;
    roi: number | null;
    conversion: number;
    expected_revenue: number;
    campaign_score: number;
  }[];
};

export type ExportPreview = {
  target_customers: number;
  provider: string;
  export_fields: string[];
  field_count: number;
  estimated_file_size_kb: number;
  estimated_download_seconds: number;
};

export type SettingsInfo = {
  general: { company: string; timezone: string; currency: string; language: string };
  intelligence: { rule_version: string; mapping_version: string; reference_data_version: string; campaign_default: string };
  roles: string[];
  audit: {
    upload_history: { file_name: string; status: string; date: string | null }[];
    export_history: { provider: string; campaign: string | null; date: string }[];
    campaign_history: { campaign: string; status: string | null; date: string }[];
    rule_version_history: { version: string; date: string }[];
  };
};

export type CampaignDetail = {
  header: {
    campaign_name: string;
    campaign_id: string;
    campaign_type: string;
    campaign_owner: string;
    campaign_status: string;
    provider: string;
    campaign_period: { start: string | null; end: string | null };
    budget: number | null;
    forecast_version: string;
    rule_version: string;
  };
  kpis: {
    target_customers: number;
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    unique_click: number;
    expected_orders: number;
    actual_orders: number;
    expected_revenue: number;
    actual_revenue: number;
    forecast_accuracy: number | null;
    campaign_roi: number | null;
    le_frame_incentive: number;
  };
  forecast: Record<string, unknown>;
  forecast_vs_actual: { metric: string; expected: number; actual: number }[];
  audience_distribution: {
    ceragem: Record<string, number>;
    prizm: Record<string, number>;
    purchase_power: Record<string, number>;
    pain_index: Record<string, number>;
    lifestyle: Record<string, number>;
    message_direction: Record<string, number>;
  };
  product_distribution: {
    product: string;
    target_customers: number;
    expected_orders: number;
    actual_orders: number;
    expected_revenue: number;
    actual_revenue: number;
    conversion: number | null;
  }[];
  state_performance: {
    state: string;
    target_customers: number;
    sent: number;
    ctr: number | null;
    conversion: number | null;
    revenue: number;
    forecast_accuracy: number | null;
    campaign_priority: string;
  }[];
  zip_opportunity: {
    zip: string;
    city: string;
    customers: number;
    purchase_power: string;
    recommended_product: string | null;
    expected_revenue: number;
    actual_revenue: number;
    campaign_priority: string;
  }[];
  timeline: { event: string; timestamp: string | null; status: string }[];
  learning_summary: {
    top_performing_segment: string | null;
    top_product: string | null;
    highest_conversion_state: string | null;
    highest_revenue_zip: string | null;
    best_message_direction: string | null;
    recommendation_for_next_campaign: string;
    learning_record?: {
      learning_id: string | null;
      learning_score: number | null;
      forecast_accuracy: number | null;
    } | null;
  };
};

export type AdminDashboard = {
  systemStatus: string;
  environment: string;
  version: string;
  timestamp: string;
  cpuUsagePercent: number | null;
  memoryUsagePercent: number | null;
  databaseStatus: { status: string };
  databasePingMs: number | null;
  storageUsage: {
    storageUsagePercent: number;
    storageUsedMb: number;
    storageTotalMb: number;
  };
  apiHealth: { status: string; version?: string };
  runningCampaigns: { campaignId: string; campaignName: string; status: string | null; provider: string | null }[];
  uploadQueue: { uploadId: string; fileName: string; status: string; createdAt: string | null }[];
  scheduledJobs: { name: string; schedule: string; status: string }[];
  notificationCenter: { severity: string; message: string; module: string }[];
  criticalAlertCount: number;
};

export type OpsChecklist = {
  checklist: string;
  generatedAt: string;
  allPassed: boolean;
  items: { label: string; passed: boolean; detail?: string }[];
};

export type AdminUser = {
  email: string;
  name: string;
  role: string;
  isActive: boolean;
  isLocked: boolean;
  failedLoginAttempts: number;
  createdAt: string | null;
  allowedModules: string[] | null;
};

export type OperationalMetrics = {
  targets: Record<string, number>;
  uploadTime: { count: number; avgMs: number | null; p95Ms: number | null };
  dashboardLoadTime: { count: number; avgMs: number | null; p95Ms: number | null };
  forecastTime: { count: number; avgMs: number | null; p95Ms: number | null };
  exportTime: { count: number; avgMs: number | null; p95Ms: number | null };
};
