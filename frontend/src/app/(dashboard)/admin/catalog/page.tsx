"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { DataTable } from "@/components/ui/data-table";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import {
  api,
  type CommercialCatalogProduct,
  type CommercialCatalogSnapshot,
} from "@/lib/api";
import { Package, Plus, RefreshCw, Save } from "lucide-react";

const FAMILIES = ["Master", "Pause", "MediSpa"] as const;
/** LE Frame Incentive = Gross × 15% */
const LE_FRAME_INCENTIVE_RATE = 0.15;

type SkuDraft = CommercialCatalogProduct & { _key: string };

function formatMoney(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function formatPct(value: number | null | undefined) {
  if (value == null) return "—";
  const pct = value > 1 ? value : value * 100;
  return `${pct.toFixed(pct % 1 === 0 ? 0 : 1)}%`;
}

/** Gross = MSRP − Promo (standing promo applied). Final catalog price after promo. */
function computeGross(product: CommercialCatalogProduct) {
  const list = product.gross_sales || product.selling_price || product.msrp || 0;
  const pct = product.default_promotion_pct;
  const code = product.promo_code;
  if (code && pct && pct > 0) {
    const rate = pct > 1 ? pct / 100 : pct;
    return Math.round(list * (1 - rate) * 100) / 100;
  }
  return list;
}

/** Promo $ amount: MSRP − Gross */
function computePromoAmount(product: CommercialCatalogProduct) {
  const msrp = product.msrp || 0;
  const gross = computeGross(product);
  return Math.round(Math.max(0, msrp - gross) * 100) / 100;
}

/** LE Frame Incentive = Gross × 15% */
function computeLeFrameIncentive(product: CommercialCatalogProduct) {
  const gross = computeGross(product);
  return Math.round(gross * LE_FRAME_INCENTIVE_RATE * 100) / 100;
}

/**
 * Net Profit = MSRP − Promo − LE Frame Incentive − COGS
 * (= Gross − LE Frame Incentive − COGS)
 */
function computeNetProfit(product: CommercialCatalogProduct) {
  const gross = computeGross(product);
  const le = computeLeFrameIncentive(product);
  const cogs = product.ceragem_cogs;
  if (cogs == null || Number.isNaN(cogs)) return null;
  return Math.round((gross - le - cogs) * 100) / 100;
}

/** Net Profit (%) = Net Profit / (Gross − LE Frame Incentive) */
function computeNetProfitPct(product: CommercialCatalogProduct) {
  const net = computeNetProfit(product);
  if (net == null) return null;
  const gross = computeGross(product);
  const le = computeLeFrameIncentive(product);
  const base = gross - le;
  if (base <= 0) return null;
  return net / base;
}

function toDraft(product: CommercialCatalogProduct): SkuDraft {
  return { ...product, _key: product.code };
}

function emptyDraft(order: number): SkuDraft {
  return {
    _key: `new-${Date.now()}`,
    code: "",
    name: "",
    family: "Master",
    category: "Core",
    segment: "Wellness",
    msrp: 0,
    selling_price: 0,
    gross_sales: 0,
    max_promotion: 0,
    promo_code: null,
    default_promotion_pct: null,
    le_frame_incentive: 0,
    ceragem_cogs: null,
    order,
    active: true,
  };
}

function serializeProducts(products: SkuDraft[]): CommercialCatalogProduct[] {
  return products.map(
    ({
      _key: _ignored,
      post_promo_price: _pp,
      default_promotion_pct_display: _disp,
      gross: _gross,
      net_profit: _np,
      net_profit_pct: _npp,
      ...product
    }) => {
      const normalized: CommercialCatalogProduct = {
        ...product,
        promo_code: product.promo_code?.trim() || null,
        default_promotion_pct:
          product.promo_code && product.default_promotion_pct
            ? product.default_promotion_pct > 1
              ? product.default_promotion_pct / 100
              : product.default_promotion_pct
            : null,
      };
      normalized.le_frame_incentive = computeLeFrameIncentive(normalized);
      return normalized;
    },
  );
}

export default function SkuCatalogAdminPage() {
  const { toast } = useToast();
  const [snapshot, setSnapshot] = useState<CommercialCatalogSnapshot | null>(null);
  const [products, setProducts] = useState<SkuDraft[]>([]);
  const [baseline, setBaseline] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editor, setEditor] = useState<{ mode: "add" | "edit"; product: SkuDraft } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCommercialCatalog();
      const rows = data.products.map(toDraft);
      setSnapshot(data);
      setProducts(rows);
      setBaseline(JSON.stringify(serializeProducts(rows)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load SKU catalog");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const dirty = useMemo(
    () => baseline !== JSON.stringify(serializeProducts(products)),
    [baseline, products],
  );

  const handleSave = async (publish: boolean) => {
    setSaving(true);
    try {
      const result = await api.saveCommercialCatalog({
        products: serializeProducts(products),
        notes: publish ? "SKU catalog admin publish" : "SKU catalog admin draft",
        publish,
      });
      toast(
        "success",
        publish
          ? `Published catalog v${result.version} (${result.sku_count} SKUs) — live in Mission Control & forecasts`
          : `Saved draft v${result.version} (${result.sku_count} SKUs)`,
      );
      await load();
    } catch (e) {
      toast("error", e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const openAdd = () => {
    const nextOrder = products.reduce((max, row) => Math.max(max, row.order ?? 0), 0) + 1;
    setEditor({ mode: "add", product: emptyDraft(nextOrder) });
  };

  const openEdit = (product: SkuDraft) => {
    setEditor({ mode: "edit", product: { ...product } });
  };

  const handleDelete = (product: SkuDraft) => {
    if (!window.confirm(`Remove SKU "${product.code}" from the catalog?`)) return;
    setProducts((rows) => rows.filter((row) => row._key !== product._key));
  };

  const saveEditor = () => {
    if (!editor) return;
    const draft = { ...editor.product };
    if (!draft.code.trim()) {
      toast("error", "SKU code is required");
      return;
    }
    if (!draft.name.trim()) draft.name = draft.code.trim();
    if (!draft.gross_sales && draft.selling_price) draft.gross_sales = draft.selling_price;
    if (draft.msrp <= 0 || draft.gross_sales <= 0) {
      toast("error", "MSRP and gross sales must be greater than zero");
      return;
    }
    draft.code = draft.code.trim();
    draft.le_frame_incentive = computeLeFrameIncentive(draft);
    draft._key = editor.mode === "add" ? draft.code : editor.product._key;

    if (editor.mode === "add" && products.some((row) => row.code === draft.code)) {
      toast("error", `SKU code "${draft.code}" already exists`);
      return;
    }

    if (editor.mode === "add") {
      setProducts((rows) => [...rows, draft].sort(sortProducts));
    } else {
      setProducts((rows) => rows.map((row) => (row._key === editor.product._key ? draft : row)).sort(sortProducts));
    }
    setEditor(null);
  };

  if (loading) return <PageSkeleton />;
  if (error) {
    const isNotFound = error.includes("Not Found") || error.includes("404");
    return (
      <div className="cios-card p-6">
        <p className="text-sm text-red-600">{error}</p>
        <p className="mt-2 text-xs text-[var(--cios-secondary)]">
          {isNotFound
            ? "The catalog API is unavailable — restart the backend (make dev-restart) so /api/v1/commercial/catalog is loaded."
            : "System Administrator role required."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
            <Package className="h-5 w-5" /> SKU Catalog & Pricing
          </h1>
          <p className="mt-1 text-sm text-[var(--cios-secondary)]">
            Manage active SKUs and standing promotions. Pricing waterfall:{" "}
            <span className="font-medium text-gray-700">MSRP − Promo = Gross</span>. Publishing updates the live
            commercial catalog used by recommendations, forecasts, and Mission Control.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2 hover:bg-gray-50"
            onClick={() => void load()}
            disabled={saving}
          >
            <RefreshCw className="mr-2 inline h-4 w-4" />
            Reload
          </button>
          <button type="button" className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2" onClick={openAdd}>
            <Plus className="mr-2 inline h-4 w-4" />
            Add SKU
          </button>
          <button
            type="button"
            className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2 disabled:opacity-50"
            disabled={!dirty || saving}
            onClick={() => void handleSave(false)}
          >
            Save Draft
          </button>
          <button
            type="button"
            className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white disabled:opacity-50"
            disabled={!dirty || saving}
            onClick={() => {
              if (!window.confirm("Publish catalog changes to production? All dashboards will use the updated prices.")) return;
              void handleSave(true);
            }}
          >
            <Save className="mr-2 inline h-4 w-4" />
            {saving ? "Saving…" : "Save & Publish"}
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetaCard label="Runtime Version" value={snapshot?.version ?? "—"} />
        <MetaCard label="Source" value={snapshot?.source === "published_db" ? "Published DB" : "Registry Default"} />
        <MetaCard label="Active SKUs" value={String(snapshot?.active_sku_count ?? products.filter((p) => p.active).length)} />
        <MetaCard label="Pending Drafts" value={String(snapshot?.draft_versions.length ?? 0)} />
      </div>

      {dirty ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
          Unsaved changes — publish to apply pricing and promo logic across the platform.
        </p>
      ) : null}

      <section className="cios-card p-5">
        <DataTable
          rows={products}
          rowKey={(row) => row._key}
          searchable
          searchPlaceholder="Search SKU, family, segment…"
          columns={[
            { key: "code", header: "SKU", getValue: (r) => r.code, sortable: true },
            { key: "family", header: "Family", getValue: (r) => r.family, filterable: true },
            { key: "segment", header: "Segment", getValue: (r) => r.segment ?? "—" },
            { key: "msrp", header: "MSRP", getValue: (r) => formatMoney(r.msrp), sortable: true },
            {
              key: "promo",
              header: "Promo",
              getValue: (r) => (r.promo_code ? `${r.promo_code} ${formatPct(r.default_promotion_pct)}` : "—"),
            },
            {
              key: "gross",
              header: "Gross",
              getValue: (r) => formatMoney(computeGross(r)),
              sortable: true,
            },
            {
              key: "net_profit",
              header: "Net Profit",
              getValue: (r) => computeNetProfit(r),
              render: (r) => formatMoney(computeNetProfit(r)),
              sortable: true,
            },
            {
              key: "net_profit_pct",
              header: "Net Profit (%)",
              getValue: (r) => {
                const pct = computeNetProfitPct(r);
                return pct == null ? null : Math.round(pct * 1000) / 10;
              },
              render: (r) => {
                const pct = computeNetProfitPct(r);
                if (pct == null) return "—";
                return `${(pct * 100).toFixed(1)}%`;
              },
              sortable: true,
            },
            {
              key: "active",
              header: "Status",
              getValue: (r) => (r.active ? "Active" : "Inactive"),
              filterable: true,
            },
            {
              key: "actions",
              header: "",
              render: (row) => (
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    className="text-xs font-medium text-[var(--cios-primary)] hover:underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      openEdit(row);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="text-xs font-medium text-red-600 hover:underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(row);
                    }}
                  >
                    Delete
                  </button>
                </div>
              ),
            },
          ]}
        />
      </section>

      {editor ? (
        <SkuEditorModal
          mode={editor.mode}
          product={editor.product}
          onChange={(product) => setEditor({ ...editor, product })}
          onClose={() => setEditor(null)}
          onSave={saveEditor}
        />
      ) : null}
    </div>
  );
}

function sortProducts(a: SkuDraft, b: SkuDraft) {
  const activeDiff = Number(b.active ?? true) - Number(a.active ?? true);
  if (activeDiff !== 0) return activeDiff;
  return (a.order ?? 50) - (b.order ?? 50) || a.code.localeCompare(b.code);
}

function MetaCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="cios-card p-4">
      <p className="text-xs text-[var(--cios-secondary)]">{label}</p>
      <p className="mt-1 text-lg font-semibold text-gray-900">{value}</p>
    </div>
  );
}

function SkuEditorModal({
  mode,
  product,
  onChange,
  onClose,
  onSave,
}: {
  mode: "add" | "edit";
  product: SkuDraft;
  onChange: (product: SkuDraft) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  const promoPct =
    product.default_promotion_pct != null
      ? product.default_promotion_pct > 1
        ? product.default_promotion_pct
        : product.default_promotion_pct * 100
      : "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">{mode === "add" ? "Add SKU" : `Edit ${product.code}`}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field label="SKU Code">
            <input
              className="cios-input w-full"
              value={product.code}
              disabled={mode === "edit"}
              onChange={(e) => onChange({ ...product, code: e.target.value })}
            />
          </Field>
          <Field label="Display Name">
            <input className="cios-input w-full" value={product.name} onChange={(e) => onChange({ ...product, name: e.target.value })} />
          </Field>
          <Field label="Family">
            <select
              className="cios-input w-full"
              value={product.family}
              onChange={(e) => onChange({ ...product, family: e.target.value })}
            >
              {FAMILIES.map((family) => (
                <option key={family} value={family}>
                  {family}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Segment">
            <input
              className="cios-input w-full"
              value={product.segment ?? ""}
              onChange={(e) => onChange({ ...product, segment: e.target.value })}
            />
          </Field>
          <Field label="MSRP">
            <input
              type="number"
              className="cios-input w-full"
              value={product.msrp || ""}
              onChange={(e) => onChange({ ...product, msrp: Number(e.target.value) || 0 })}
            />
          </Field>
          <Field label="List Price (pre-promo)">
            <input
              type="number"
              className="cios-input w-full"
              value={product.gross_sales || ""}
              onChange={(e) => onChange({ ...product, gross_sales: Number(e.target.value) || 0, selling_price: Number(e.target.value) || 0 })}
            />
          </Field>
          <Field label="Max Promotion">
            <input
              type="number"
              className="cios-input w-full"
              value={product.max_promotion ?? ""}
              onChange={(e) => onChange({ ...product, max_promotion: Number(e.target.value) || 0 })}
            />
          </Field>
          <Field label="LE Frame Incentive (Gross × 15%)">
            <input
              type="number"
              className="cios-input w-full bg-gray-50"
              value={computeLeFrameIncentive(product) || ""}
              readOnly
              disabled
              title="Automatically calculated as 15% of Gross"
            />
          </Field>
          <Field label="Ceragem COGS">
            <input
              type="number"
              className="cios-input w-full"
              value={product.ceragem_cogs ?? ""}
              onChange={(e) => onChange({ ...product, ceragem_cogs: e.target.value ? Number(e.target.value) : null })}
            />
          </Field>
          <Field label="Sort Order">
            <input
              type="number"
              className="cios-input w-full"
              value={product.order ?? 50}
              onChange={(e) => onChange({ ...product, order: Number(e.target.value) || 50 })}
            />
          </Field>
          <Field label="Promo Code">
            <input
              className="cios-input w-full"
              value={product.promo_code ?? ""}
              placeholder="SAVE20"
              onChange={(e) => onChange({ ...product, promo_code: e.target.value || null })}
            />
          </Field>
          <Field label="Promotion %">
            <input
              type="number"
              className="cios-input w-full"
              value={promoPct}
              placeholder="20"
              onChange={(e) =>
                onChange({
                  ...product,
                  default_promotion_pct: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
          </Field>
          <Field label="Category">
            <input
              className="cios-input w-full"
              value={product.category ?? ""}
              onChange={(e) => onChange({ ...product, category: e.target.value })}
            />
          </Field>
          <Field label="Active">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={product.active ?? true}
                onChange={(e) => onChange({ ...product, active: e.target.checked })}
              />
              Include in live catalog
            </label>
          </Field>
        </div>
        <p className="mt-4 space-y-1 text-sm text-[var(--cios-secondary)]">
          <span className="block">
            Pricing: MSRP → Promo → Gross. Gross = {formatMoney(computeGross(product))}
            {computePromoAmount(product) > 0 ? ` (Promo ${formatMoney(computePromoAmount(product))})` : ""}
          </span>
          <span className="block">
            Net Profit = Gross − LE Frame (15%) − COGS → {formatMoney(computeNetProfit(product))}
            {computeNetProfitPct(product) != null
              ? ` (${(computeNetProfitPct(product)! * 100).toFixed(1)}%)`
              : ""}
          </span>
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" className="cios-btn border border-[var(--cios-border)] px-4 py-2" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white" onClick={onSave}>
            {mode === "add" ? "Add SKU" : "Apply Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-gray-700">{label}</span>
      {children}
    </label>
  );
}
