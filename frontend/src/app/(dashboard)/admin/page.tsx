"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DataTable } from "@/components/ui/data-table";
import { KpiCard } from "@/components/ui/kpi-card";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { api, type AdminDashboard, type AdminUser, type CommercialCatalogVersion, type OpsChecklist } from "@/lib/api";
import { Activity, Database, HardDrive, Server, Shield, Users } from "lucide-react";

export default function AdminPage() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [daily, setDaily] = useState<OpsChecklist | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [commercialVersions, setCommercialVersions] = useState<CommercialCatalogVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dash, checklist, userData, commercial] = await Promise.all([
        api.getAdminDashboard(),
        api.getDailyChecklist(),
        api.getAdminUsers(),
        api.getCommercialVersions().catch(() => ({ versions: [] })),
      ]);
      setDashboard(dash);
      setDaily(checklist);
      setUsers(userData.users);
      setRoles(userData.roles);
      setCommercialVersions(commercial.versions ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load admin dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleImport = async (file: File) => {
    setImporting(true);
    try {
      const result = await api.importCommercialPriceGuide(file);
      toast("success", `Draft v${result.version} imported (${result.sku_count} SKUs)`);
      await load();
    } catch (e) {
      toast("error", e instanceof Error ? e.message : "Import failed");
    } finally {
      setImporting(false);
    }
  };

  const handleApprove = async (versionId: string) => {
    try {
      const result = await api.approveCommercialVersion(versionId);
      toast("success", `Published commercial catalog v${result.version}`);
      await load();
    } catch (e) {
      toast("error", e instanceof Error ? e.message : "Approve failed");
    }
  };

  if (loading) return <PageSkeleton />;
  if (error) {
    return (
      <div className="cios-card p-6">
        <p className="text-sm text-red-600">{error}</p>
        <p className="mt-2 text-xs text-[var(--cios-secondary)]">System Administrator role required.</p>
      </div>
    );
  }
  if (!dashboard) return null;

  return (
    <div className="space-y-6">
      <p className="text-sm text-[var(--cios-secondary)]">
        Volume 14 — System status, operational checklists, user administration, and notifications.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="System Status"
          value={dashboard.systemStatus === "up" ? "Healthy" : "Degraded"}
          icon={Server}
        />
        <KpiCard label="CPU Usage" value={`${dashboard.cpuUsagePercent ?? "—"}%`} icon={Activity} />
        <KpiCard label="Memory" value={`${dashboard.memoryUsagePercent ?? "—"}%`} icon={Activity} />
        <KpiCard
          label="Storage"
          value={`${dashboard.storageUsage.storageUsagePercent}%`}
          icon={HardDrive}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="cios-card p-5">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Database className="h-4 w-4" /> Database & API
          </h2>
          <dl className="grid gap-2 text-sm">
            <Row label="Database" value={dashboard.databaseStatus.status} />
            <Row label="DB Ping" value={`${dashboard.databasePingMs ?? "—"} ms`} />
            <Row label="API Health" value={dashboard.apiHealth.status} />
            <Row label="Environment" value={dashboard.environment} />
            <Row label="Version" value={dashboard.version} />
          </dl>
        </section>

        <section className="cios-card p-5">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Shield className="h-4 w-4" /> Daily Checklist
          </h2>
          {daily && (
            <ul className="space-y-2 text-sm">
              {daily.items.map((item) => (
                <li key={item.label} className="flex items-start gap-2">
                  <span className={item.passed ? "text-green-600" : "text-amber-600"}>
                    {item.passed ? "✓" : "○"}
                  </span>
                  <span>
                    {item.label}
                    {item.detail ? <span className="text-[var(--cios-secondary)]"> — {item.detail}</span> : null}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="cios-card p-5">
        <h2 className="mb-3 text-base font-semibold text-gray-900">Notification Center</h2>
        {dashboard.notificationCenter.length === 0 ? (
          <p className="text-sm text-[var(--cios-secondary)]">No active alerts.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {dashboard.notificationCenter.map((n, i) => (
              <li key={i} className="rounded-lg bg-gray-50 px-3 py-2">
                <span className="font-medium capitalize">{n.severity}</span> — {n.message}
                <span className="text-[var(--cios-secondary)]"> ({n.module})</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="cios-card p-5">
        <h2 className="mb-3 text-base font-semibold text-gray-900">Commercial Intelligence Administration</h2>
        <p className="mb-4 text-sm text-[var(--cios-secondary)]">
          Manage SKU pricing in{" "}
          <a href="/admin/catalog" className="font-medium text-[var(--cios-primary)] hover:underline">
            SKU Catalog
          </a>
          . Bulk CSV import/export with version control remains below.
        </p>
        <div className="mb-4 flex flex-wrap gap-3">
          <a
            href={api.downloadCommercialPriceGuide()}
            className="cios-btn border border-[var(--cios-border)] bg-white px-4 py-2 hover:bg-gray-50"
          >
            Export Price Guide CSV
          </a>
          <button
            type="button"
            className="cios-btn bg-[var(--cios-primary)] px-4 py-2 text-white disabled:opacity-50"
            disabled={importing}
            onClick={() => fileInputRef.current?.click()}
          >
            {importing ? "Importing…" : "Import Price Guide CSV"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            aria-label="Import commercial price guide CSV"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleImport(file);
              e.target.value = "";
            }}
          />
        </div>
        {commercialVersions.length === 0 ? (
          <p className="text-sm text-[var(--cios-secondary)]">No catalog versions yet — registry default is active.</p>
        ) : (
          <DataTable
            rows={commercialVersions}
            rowKey={(r) => r.id}
            searchable={false}
            onRowClick={(r) => {
              if (r.status === "draft") void handleApprove(r.id);
            }}
            columns={[
              { key: "version", header: "Version", getValue: (r) => r.version },
              { key: "status", header: "Status", getValue: (r) => r.status, filterable: true },
              { key: "sku", header: "SKUs", getValue: (r) => String(r.sku_count) },
              { key: "created", header: "Created", getValue: (r) => r.created_at?.slice(0, 10) ?? "—" },
              {
                key: "action",
                header: "Action",
                getValue: (r) => (r.status === "draft" ? "Click to approve" : r.status === "published" ? "Active" : "Archived"),
              },
            ]}
          />
        )}
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-gray-900">Running Campaigns</h2>
        <DataTable
          rows={dashboard.runningCampaigns}
          rowKey={(r) => r.campaignId}
          searchable={false}
          columns={[
            { key: "name", header: "Campaign", getValue: (r) => r.campaignName },
            { key: "status", header: "Status", getValue: (r) => r.status ?? "—", filterable: true },
            { key: "provider", header: "Provider", getValue: (r) => r.provider ?? "—" },
          ]}
        />
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
          <Users className="h-4 w-4" /> User Administration
        </h2>
        <DataTable
          rows={users}
          rowKey={(r) => r.email}
          searchable
          columns={[
            { key: "email", header: "Email", getValue: (r) => r.email },
            { key: "name", header: "Name", getValue: (r) => r.name },
            { key: "role", header: "Role", getValue: (r) => r.role, filterable: true },
            {
              key: "active",
              header: "Status",
              getValue: (r) => (r.isLocked ? "Locked" : r.isActive ? "Active" : "Disabled"),
              filterable: true,
            },
          ]}
        />
        <p className="mt-2 text-xs text-[var(--cios-secondary)]">
          Roles: {roles.join(", ")}. Manage users and role-based menu access in{" "}
          <a href="/admin/users" className="font-medium text-indigo-600 hover:underline">
            User Management
          </a>
          .
        </p>
      </section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-gray-100 py-1">
      <dt className="text-[var(--cios-secondary)]">{label}</dt>
      <dd className="font-medium text-gray-900">{value}</dd>
    </div>
  );
}
