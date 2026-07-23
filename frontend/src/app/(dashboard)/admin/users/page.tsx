"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Eye, EyeOff, Shield, UserPlus } from "lucide-react";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/contexts/auth-context";
import { SYSTEM_ROLES } from "@/lib/access-control";
import { api, type AdminUser } from "@/lib/api";
import {
  menuHrefsForRole,
  navigableMenuOptionsForRole,
  usesMenuHrefs,
} from "@/lib/menu-registry";

type UserDraft = {
  email: string;
  name: string;
  role: string;
  menuAccessMode: "role" | "custom";
  selectedMenuHrefs: string[];
};

function draftFromUser(user: AdminUser): UserDraft {
  const hasCustom = Boolean(user.allowedModules?.length && usesMenuHrefs(user.allowedModules));
  return {
    email: user.email,
    name: user.name,
    role: user.role,
    menuAccessMode: hasCustom ? "custom" : "role",
    selectedMenuHrefs: hasCustom ? user.allowedModules! : menuHrefsForRole(user.role),
  };
}

function draftsEqual(a: UserDraft, b: UserDraft): boolean {
  return (
    a.email === b.email &&
    a.name === b.name &&
    a.role === b.role &&
    a.menuAccessMode === b.menuAccessMode &&
    a.selectedMenuHrefs.slice().sort().join("|") === b.selectedMenuHrefs.slice().sort().join("|")
  );
}

export default function AdminUsersPage() {
  const { toast } = useToast();
  const { canAccess, session } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<string[]>([...SYSTEM_ROLES]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null);
  const [form, setForm] = useState({ email: "", name: "", password: "", role: "Marketing Analyst" });
  const [newUserMenuMode, setNewUserMenuMode] = useState<"role" | "custom">("role");
  const [newUserMenuHrefs, setNewUserMenuHrefs] = useState<string[]>(() => menuHrefsForRole("Marketing Analyst"));
  const [showNewUserPassword, setShowNewUserPassword] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [showSelectedUserPassword, setShowSelectedUserPassword] = useState(false);
  const [drafts, setDrafts] = useState<Record<string, UserDraft>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminUsers();
      setUsers(data.users);
      setRoles(data.roles.length ? data.roles : [...SYSTEM_ROLES]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setDrafts(Object.fromEntries(users.map((user) => [user.email, draftFromUser(user)])));
  }, [users]);

  useEffect(() => {
    setNewPassword("");
    setShowSelectedUserPassword(false);
  }, [selectedEmail]);

  const selectedUser = useMemo(
    () => (selectedEmail ? users.find((user) => user.email === selectedEmail) ?? null : null),
    [selectedEmail, users],
  );
  const selectedDraft = selectedEmail ? drafts[selectedEmail] : null;
  const savedDraft = selectedUser ? draftFromUser(selectedUser) : null;
  const selectedDirty = Boolean(selectedDraft && savedDraft && !draftsEqual(selectedDraft, savedDraft));
  const passwordDirty = newPassword.trim().length > 0;
  const canSaveSelected = selectedDirty || passwordDirty;

  const previewRole = selectedDraft?.role ?? form.role;
  const previewMenuOptions = useMemo(() => navigableMenuOptionsForRole(previewRole), [previewRole]);
  const newUserMenuOptions = useMemo(() => navigableMenuOptionsForRole(form.role), [form.role]);

  const syncNewUserMenus = (role: string) => {
    setNewUserMenuHrefs(menuHrefsForRole(role));
  };

  const updateDraft = useCallback((email: string, patch: Partial<UserDraft>) => {
    setDrafts((current) => {
      const existing = current[email];
      if (!existing) return current;
      const next = { ...existing, ...patch };
      if (patch.role && patch.role !== existing.role) {
        const roleHrefs = menuHrefsForRole(patch.role);
        next.selectedMenuHrefs =
          next.menuAccessMode === "custom"
            ? next.selectedMenuHrefs.filter((href) => roleHrefs.includes(href))
            : roleHrefs;
        if (next.menuAccessMode === "custom" && !next.selectedMenuHrefs.length) {
          next.selectedMenuHrefs = roleHrefs.slice(0, 1);
        }
      }
      return { ...current, [email]: next };
    });
  }, []);

  const draftsRef = useRef(drafts);
  const selectedEmailRef = useRef(selectedEmail);
  const currentEmailRef = useRef(session?.email ?? null);
  draftsRef.current = drafts;
  selectedEmailRef.current = selectedEmail;
  currentEmailRef.current = session?.email ?? null;

  const toggleMenuHref = (hrefs: string[], href: string, role: string) => {
    if (hrefs.includes(href)) {
      if (hrefs.length === 1) return hrefs;
      return hrefs.filter((item) => item !== href);
    }
    return [...hrefs, href].sort();
  };

  const toggleActive = useCallback(async (row: AdminUser) => {
    try {
      if (row.isActive) {
        await api.disableAdminUser(row.email);
        toast("success", `${row.email} disabled`);
      } else {
        await api.activateAdminUser(row.email);
        toast("success", `${row.email} activated`);
      }
      await load();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Update failed");
    }
  }, [load, toast]);

  const unlock = useCallback(async (email: string) => {
    try {
      await api.unlockAdminUser(email);
      toast("success", `${email} unlocked`);
      await load();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Unlock failed");
    }
  }, [load, toast]);

  const deleteUser = useCallback(async (row: AdminUser) => {
    if (!window.confirm(`Delete ${row.email}? This cannot be undone.`)) return;
    try {
      await api.deleteAdminUser(row.email);
      toast("success", `${row.email} deleted`);
      if (selectedEmailRef.current === row.email) {
        setSelectedEmail(null);
        setNewPassword("");
        setShowSelectedUserPassword(false);
      }
      await load();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Delete failed");
    }
  }, [load, toast]);

  const userTableColumns = useMemo<DataTableColumn<AdminUser>[]>(
    () => [
      {
        key: "select",
        header: "",
        getValue: () => "",
        render: (r) => (
          <input
            type="radio"
            name="selected-user"
            checked={selectedEmailRef.current === r.email}
            onChange={() => setSelectedEmail(r.email)}
            aria-label={`Select ${r.email}`}
          />
        ),
      },
      {
        key: "email",
        header: "Email",
        getValue: (r) => r.email,
        render: (r) => {
          const draft = draftsRef.current[r.email] ?? draftFromUser(r);
          return (
            <input
              type="email"
              value={draft.email}
              disabled={selectedEmailRef.current !== r.email}
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => updateDraft(r.email, { email: e.target.value })}
              className="w-full min-w-[12rem] rounded border border-[var(--cios-border)] px-2 py-1 text-xs"
            />
          );
        },
      },
      {
        key: "name",
        header: "Name",
        getValue: (r) => r.name,
        render: (r) => {
          const draft = draftsRef.current[r.email] ?? draftFromUser(r);
          return (
            <input
              type="text"
              value={draft.name}
              disabled={selectedEmailRef.current !== r.email}
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => updateDraft(r.email, { name: e.target.value })}
              className="w-full min-w-[10rem] rounded border border-[var(--cios-border)] px-2 py-1 text-xs"
            />
          );
        },
      },
      {
        key: "status",
        header: "Status",
        getValue: (r) => (r.isLocked ? "Locked" : r.isActive ? "Active" : "Disabled"),
        filterable: true,
      },
      {
        key: "actions",
        header: "Actions",
        getValue: () => "",
        render: (r) => (
          <div className="flex flex-wrap gap-2 text-xs" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="text-indigo-600 hover:underline" onClick={() => void toggleActive(r)}>
              {r.isActive ? "Disable" : "Activate"}
            </button>
            {r.isLocked ? (
              <button type="button" className="text-indigo-600 hover:underline" onClick={() => void unlock(r.email)}>
                Unlock
              </button>
            ) : null}
            {currentEmailRef.current !== r.email ? (
              <button type="button" className="text-red-600 hover:underline" onClick={() => void deleteUser(r)}>
                Delete
              </button>
            ) : null}
          </div>
        ),
      },
    ],
    [deleteUser, toggleActive, unlock, updateDraft],
  );

  if (!canAccess("user_administration")) {
    return (
      <div className="cios-card p-6">
        <p className="text-sm text-red-600">System Administrator access required.</p>
      </div>
    );
  }

  if (loading) return <PageSkeleton />;
  if (error) {
    return (
      <div className="cios-card p-6">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    if (newUserMenuMode === "custom" && newUserMenuHrefs.length === 0) {
      toast("error", "Select at least one menu for custom access");
      return;
    }
    setCreating(true);
    try {
      await api.createAdminUser({
        ...form,
        allowedModules: newUserMenuMode === "custom" ? newUserMenuHrefs : null,
      });
      toast("success", `User ${form.email} created`);
      setForm({ email: "", name: "", password: "", role: form.role });
      setNewUserMenuMode("role");
      syncNewUserMenus(form.role);
      await load();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Create failed");
    } finally {
      setCreating(false);
    }
  };

  const saveSelectedUser = async () => {
    if (!selectedEmail || !selectedDraft || !selectedUser) return;
    if (selectedDraft.menuAccessMode === "custom" && selectedDraft.selectedMenuHrefs.length === 0) {
      toast("error", "Select at least one menu for custom access");
      return;
    }
    const password = newPassword.trim();
    if (!selectedDirty && !password) return;
    if (password && password.length < 12) {
      toast("error", "Password must be at least 12 characters");
      return;
    }

    setSaving(true);
    try {
      let finalEmail = selectedEmail;
      if (selectedDirty) {
        await api.updateAdminUser(selectedEmail, {
          email: selectedDraft.email.trim().toLowerCase() !== selectedUser.email ? selectedDraft.email.trim().toLowerCase() : undefined,
          name: selectedDraft.name.trim() !== selectedUser.name ? selectedDraft.name.trim() : undefined,
          role: selectedDraft.role !== selectedUser.role ? selectedDraft.role : undefined,
          menuAccessMode: selectedDraft.menuAccessMode,
          allowedModules: selectedDraft.menuAccessMode === "custom" ? selectedDraft.selectedMenuHrefs : null,
        });
        finalEmail = selectedDraft.email.trim().toLowerCase();
      }
      if (password) {
        await api.resetUserPassword(finalEmail, password);
      }
      toast(
        "success",
        password ? `Saved changes and reset password for ${finalEmail}` : `Saved changes for ${finalEmail}`,
      );
      setNewPassword("");
      setShowSelectedUserPassword(false);
      await load();
      setSelectedEmail(finalEmail);
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const cancelSelectedUser = () => {
    if (!selectedUser) return;
    setDrafts((current) => ({
      ...current,
      [selectedUser.email]: draftFromUser(selectedUser),
    }));
    setNewPassword("");
    setShowSelectedUserPassword(false);
  };

  const renderMenuPreview = (
    mode: "role" | "custom",
    menuHrefs: string[],
    options: ReturnType<typeof navigableMenuOptionsForRole>,
    onToggle: (href: string) => void,
    readOnly: boolean,
  ) => (
    <div className="flex flex-wrap gap-2">
      {options.map((item) => {
        const selected = menuHrefs.includes(item.href);
        if (readOnly || mode === "role") {
          if (!selected && mode === "custom") return null;
          if (mode === "role" || selected) {
            return (
              <span
                key={item.href}
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  mode === "custom" && selected
                    ? "bg-indigo-50 text-indigo-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {item.label}
              </span>
            );
          }
          return null;
        }
        return (
          <label
            key={item.href}
            className={`flex cursor-pointer items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium ${
              selected ? "border-indigo-400 bg-indigo-50 text-indigo-800" : "border-[var(--cios-border)] bg-white text-gray-700"
            }`}
          >
            <input
              type="checkbox"
              className="sr-only"
              checked={selected}
              onChange={() => onToggle(item.href)}
            />
            {item.label}
          </label>
        );
      })}
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Shield className="h-5 w-5" /> User Management
        </h1>
        <p className="mt-1 text-sm text-[var(--cios-secondary)]">
          Select a user to edit profile, role, menu access, or reset password. Click Save to apply changes.
        </p>
      </div>

      <section className="orion-widget p-5">
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
          <UserPlus className="h-4 w-4" /> Add user
        </h2>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={onCreate}>
          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Email</span>
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              className="w-full rounded-lg border border-[var(--cios-border)] px-3 py-2"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Name</span>
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full rounded-lg border border-[var(--cios-border)] px-3 py-2"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Password</span>
            <div className="relative">
              <input
                required
                type={showNewUserPassword ? "text" : "password"}
                minLength={12}
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                className="w-full rounded-lg border border-[var(--cios-border)] px-3 py-2 pr-10"
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowNewUserPassword((current) => !current)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-[var(--cios-secondary)] hover:text-gray-700"
                aria-label={showNewUserPassword ? "Hide password" : "Show password"}
                aria-pressed={showNewUserPassword}
              >
                {showNewUserPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Role</span>
            <select
              value={form.role}
              onChange={(e) => {
                const role = e.target.value;
                setForm((f) => ({ ...f, role }));
                syncNewUserMenus(role);
              }}
              className="w-full rounded-lg border border-[var(--cios-border)] px-3 py-2"
            >
              {roles.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </label>
          <div className="md:col-span-2 space-y-3 border-t border-[var(--cios-border)] pt-4">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={newUserMenuMode === "custom"}
                onChange={(e) => {
                  const custom = e.target.checked;
                  setNewUserMenuMode(custom ? "custom" : "role");
                  if (custom) setNewUserMenuHrefs(menuHrefsForRole(form.role));
                }}
              />
              Custom menu access
            </label>
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Preview</p>
              {renderMenuPreview(
                newUserMenuMode,
                newUserMenuMode === "custom" ? newUserMenuHrefs : menuHrefsForRole(form.role),
                newUserMenuOptions,
                (href) => setNewUserMenuHrefs((current) => toggleMenuHref(current, href, form.role)),
                newUserMenuMode !== "custom",
              )}
            </div>
          </div>
          <div className="md:col-span-2">
            <button type="submit" disabled={creating} className="cios-btn rounded-lg bg-[var(--orion-accent)] px-4 py-2 text-sm font-semibold text-white">
              {creating ? "Creating…" : "Create user"}
            </button>
          </div>
        </form>
      </section>

      <section>
        <DataTable
          rows={users}
          rowKey={(r) => r.email}
          searchable
          onRowClick={(row) => setSelectedEmail(row.email)}
          columns={userTableColumns}
        />
      </section>

      <section className="orion-widget p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-gray-900">Role menu preview</h2>
          {selectedDraft ? (
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={selectedDraft.menuAccessMode === "custom"}
                onChange={(e) => {
                  const custom = e.target.checked;
                  updateDraft(selectedEmail!, {
                    menuAccessMode: custom ? "custom" : "role",
                    selectedMenuHrefs: custom
                      ? selectedDraft.selectedMenuHrefs.length
                        ? selectedDraft.selectedMenuHrefs
                        : menuHrefsForRole(selectedDraft.role)
                      : menuHrefsForRole(selectedDraft.role),
                  });
                }}
              />
              Custom menu access
            </label>
          ) : null}
        </div>

        {!selectedDraft ? (
          <p className="text-sm text-[var(--cios-secondary)]">Select a user from the table to view and edit role menu access.</p>
        ) : (
          <>
            <div className="mb-4 grid gap-3 md:grid-cols-2">
              <label className="text-sm">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Role</span>
                <select
                  value={selectedDraft.role}
                  onChange={(e) => updateDraft(selectedEmail!, { role: e.target.value })}
                  className="w-full rounded-lg border border-[var(--cios-border)] px-3 py-2"
                >
                  {roles.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </label>
              <div className="text-sm">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Selected user</span>
                <p className="rounded-lg border border-[var(--cios-border)] px-3 py-2 text-gray-800">
                  {selectedDraft.name} ({selectedDraft.email})
                </p>
              </div>
            </div>

            <label className="mb-4 block text-sm md:max-w-md">
              <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">
                New password (optional)
              </span>
              <div className="relative">
                <input
                  type={showSelectedUserPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Leave blank to keep current password"
                  minLength={12}
                  autoComplete="new-password"
                  className="w-full rounded-lg border border-[var(--cios-border)] px-3 py-2 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowSelectedUserPassword((current) => !current)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-[var(--cios-secondary)] hover:text-gray-700"
                  aria-label={showSelectedUserPassword ? "Hide password" : "Show password"}
                  aria-pressed={showSelectedUserPassword}
                >
                  {showSelectedUserPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="mt-1 text-xs text-[var(--cios-secondary)]">
                Minimum 12 characters with uppercase, lowercase, number, and special character.
              </p>
            </label>

            <p className="mb-3 text-xs text-[var(--cios-secondary)]">
              {selectedDraft.menuAccessMode === "custom"
                ? "Choose individual menus below. Only options allowed for this role are shown."
                : `All menus enabled for ${selectedDraft.role}. Turn on Custom menu access to pick individual menus.`}
            </p>

            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--cios-secondary)]">Preview</p>
              {renderMenuPreview(
                selectedDraft.menuAccessMode,
                selectedDraft.menuAccessMode === "custom" ? selectedDraft.selectedMenuHrefs : menuHrefsForRole(selectedDraft.role),
                previewMenuOptions,
                (href) =>
                  updateDraft(selectedEmail!, {
                    selectedMenuHrefs: toggleMenuHref(selectedDraft.selectedMenuHrefs, href, selectedDraft.role),
                  }),
                selectedDraft.menuAccessMode !== "custom",
              )}
              {selectedDraft.menuAccessMode === "custom" && !selectedDraft.selectedMenuHrefs.length ? (
                <p className="mt-2 text-xs text-red-600">Select at least one menu.</p>
              ) : null}
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={!canSaveSelected || saving}
                onClick={() => void saveSelectedUser()}
                className="rounded-lg bg-[var(--orion-accent)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              >
                {saving ? "Saving…" : "Save"}
              </button>
              <button
                type="button"
                disabled={!canSaveSelected || saving}
                onClick={cancelSelectedUser}
                className="rounded-lg border border-[var(--cios-border)] px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
