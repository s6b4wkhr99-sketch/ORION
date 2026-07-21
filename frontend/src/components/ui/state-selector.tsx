"use client";

import { useMemo, useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { SearchInput } from "@/components/ui/search-input";

const RECENT_KEY = "cios-recent-states";
const FAV_KEY = "cios-favorite-states";

type StateSelectorProps = {
  states: string[];
  value: string | null;
  onChange: (state: string | null) => void;
  className?: string;
};

function loadList(key: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(key) ?? "[]") as string[];
  } catch {
    return [];
  }
}

function saveList(key: string, list: string[]) {
  localStorage.setItem(key, JSON.stringify(list.slice(0, 8)));
}

export function StateSelector({ states, value, onChange, className }: StateSelectorProps) {
  const [query, setQuery] = useState("");
  const [recent, setRecent] = useState<string[]>(() => loadList(RECENT_KEY));
  const [favorites, setFavorites] = useState<string[]>(() => loadList(FAV_KEY));

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return states;
    return states.filter((s) => s.toLowerCase().includes(q));
  }, [states, query]);

  const select = (state: string | null) => {
    if (state) {
      const next = [state, ...recent.filter((s) => s !== state)].slice(0, 8);
      setRecent(next);
      saveList(RECENT_KEY, next);
    }
    onChange(state);
  };

  const toggleFavorite = (state: string) => {
    const next = favorites.includes(state) ? favorites.filter((s) => s !== state) : [...favorites, state];
    setFavorites(next);
    saveList(FAV_KEY, next);
  };

  return (
    <section className={cn("cios-card p-5", className)}>
      <h2 className="mb-3 text-base font-semibold text-gray-900">State Selector</h2>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <SearchInput value={query} onChange={setQuery} placeholder="Search states..." className="sm:max-w-xs" />
        <select
          className="cios-input flex-1 bg-white px-3 py-2"
          value={value ?? ""}
          onChange={(e) => select(e.target.value || null)}
          aria-label="Select state"
        >
          <option value="">All States</option>
          {filtered.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      {(favorites.length > 0 || recent.length > 0) && (
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          {favorites.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-[var(--cios-secondary)]">Favorites</p>
              <div className="flex flex-wrap gap-2">
                {favorites.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => select(s)}
                    className={cn(
                      "inline-flex items-center gap-1 rounded-full border px-3 py-1",
                      value === s ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] text-[var(--cios-primary)]" : "border-[var(--cios-border)]",
                    )}
                  >
                    <Star className="h-3 w-3 fill-current" />
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {recent.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-[var(--cios-secondary)]">Recent</p>
              <div className="flex flex-wrap gap-2">
                {recent.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => select(s)}
                    className={cn(
                      "rounded-full border px-3 py-1",
                      value === s ? "border-[var(--cios-primary)] bg-[var(--cios-primary-light)] text-[var(--cios-primary)]" : "border-[var(--cios-border)]",
                    )}
                  >
                    {s}
                    <span
                      role="button"
                      tabIndex={0}
                      className="ml-2 text-xs text-[var(--cios-secondary)] hover:text-[var(--cios-primary)]"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(s);
                      }}
                      onKeyDown={(e) => e.key === "Enter" && toggleFavorite(s)}
                      aria-label={`Toggle favorite ${s}`}
                    >
                      ★
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
