"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, RefreshCw, Trash2 } from "lucide-react";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import { PageHeader } from "@/components/mockup/page-header";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { api, type AudienceExportRecommendation } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function skuBundle(row: AudienceExportRecommendation) {
  return row.additionalSkus?.length ? `${row.mainSku} + ${row.additionalSkus.join(", ")}` : row.mainSku;
}

export default function ExportPage() {
  const { toast } = useToast();
  const [items, setItems] = useState<AudienceExportRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await api.listAudienceExports();
      setItems(payload.items ?? []);
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Failed to load audience exports");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadItems();
  }, [loadItems]);

  const handleDelete = async (row: AudienceExportRecommendation) => {
    if (!window.confirm(`Delete "${row.name}"?`)) return;
    setBusyId(row.id);
    try {
      await api.deleteAudienceExport(row.id);
      setItems((prev) => prev.filter((item) => item.id !== row.id));
      toast("success", "Audience export deleted");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Delete failed");
    } finally {
      setBusyId(null);
    }
  };

  const handleExport = async (row: AudienceExportRecommendation) => {
    setBusyId(row.id);
    try {
      if (row.forecastCustomers >= 50000) {
        toast("warning", `Generating ${formatNumber(row.forecastCustomers)} rows — this may take several minutes.`);
      }
      await api.downloadAudienceExport(row.id, `audience_${row.mainSku.replace(/\s+/g, "_")}_${row.id.slice(0, 8)}.csv`);
      toast("success", `Downloaded audience export (${formatNumber(row.forecastCustomers)} customers)`);
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusyId(null);
    }
  };

  const columns = useMemo<DataTableColumn<AudienceExportRecommendation>[]>(
    () => [
      {
        key: "name",
        header: "Recommendation",
        sortable: true,
        getValue: (row) => row.name,
        render: (row) => (
          <div>
            <p className="font-medium text-gray-900">{row.name}</p>
            <p className="mt-0.5 text-[10px] text-[var(--cios-secondary)]">{skuBundle(row)}</p>
          </div>
        ),
      },
      {
        key: "forecastCustomers",
        header: "Active Forecast Customers",
        sortable: true,
        getValue: (row) => row.forecastCustomers,
        render: (row) => formatNumber(row.forecastCustomers),
      },
      {
        key: "forecastRevenue",
        header: "Active Forecast Revenue",
        sortable: true,
        getValue: (row) => row.forecastRevenue,
        render: (row) => formatCurrency(row.forecastRevenue),
      },
      {
        key: "predictedConversion",
        header: "Predicted Conversion",
        sortable: true,
        getValue: (row) => row.predictedConversion,
        render: (row) => formatPercent(row.predictedConversion),
      },
      {
        key: "expectedOrders",
        header: "Expected Orders",
        sortable: true,
        getValue: (row) => row.expectedOrders,
        render: (row) => formatNumber(row.expectedOrders),
      },
      {
        key: "geoScope",
        header: "Geo Scope",
        sortable: true,
        getValue: (row) => row.geoScope,
        render: (row) => <span className="max-w-[220px] truncate" title={row.geoScope}>{row.geoScope}</span>,
      },
      {
        key: "createdAt",
        header: "Saved",
        sortable: true,
        getValue: (row) => row.createdAt ?? "",
        render: (row) => formatDate(row.createdAt),
      },
      {
        key: "actions",
        header: "Actions",
        render: (row) => (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busyId === row.id}
              onClick={() => void handleExport(row)}
              className="inline-flex items-center gap-1 rounded-md border border-[var(--cios-border)] bg-white px-2 py-1 text-[11px] font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              {busyId === row.id ? "Exporting..." : "Export"}
            </button>
            <button
              type="button"
              disabled={busyId === row.id}
              onClick={() => void handleDelete(row)}
              className="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-2 py-1 text-[11px] font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </button>
          </div>
        ),
      },
    ],
    [busyId],
  );

  if (loading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audience Export"
        subtitle="Saved Opportunity Finder recommendations — export the matched audience or remove saved rows."
        actions={
          <button
            type="button"
            onClick={() => void loadItems()}
            className="inline-flex items-center gap-1 rounded-md border border-[var(--cios-border)] bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        }
      />

      <section className="cios-card p-5">
        <DataTable
          columns={columns}
          rows={items}
          rowKey={(row) => row.id}
          searchPlaceholder="Search saved recommendations..."
          emptyMessage="No saved recommendations yet. Use Build Recommendation in Opportunity Finder to save one."
        />
      </section>
    </div>
  );
}
