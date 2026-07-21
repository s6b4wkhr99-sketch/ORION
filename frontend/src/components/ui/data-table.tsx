"use client";

import { useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
} from "@tanstack/react-table";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { SearchInput } from "@/components/ui/search-input";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (row: T) => React.ReactNode;
  getValue?: (row: T) => string | number | null;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  searchable?: boolean;
  searchPlaceholder?: string;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  className?: string;
};

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  searchable = true,
  searchPlaceholder = "Search table...",
  onRowClick,
  emptyMessage = "No data available.",
  className,
}: DataTableProps<T>) {
  const [globalFilter, setGlobalFilter] = useState("");
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const columnDefs = useMemo<ColumnDef<T>[]>(
    () =>
      columns.map((col) => ({
        id: col.key,
        accessorFn: (row) => col.getValue?.(row) ?? (row as Record<string, unknown>)[col.key],
        header: col.header,
        cell: ({ row }) =>
          col.render
            ? col.render(row.original)
            : String(col.getValue?.(row.original) ?? (row.original as Record<string, unknown>)[col.key] ?? "—"),
        enableSorting: col.sortable !== false,
        enableColumnFilter: col.filterable === true,
        filterFn: (row, columnId, filterValue) => {
          if (!filterValue) return true;
          const val = row.getValue(columnId);
          return String(val ?? "") === String(filterValue);
        },
      })),
    [columns],
  );

  const table = useReactTable({
    data: rows,
    columns: columnDefs,
    state: { sorting, globalFilter, columnFilters },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: "includesString",
    getRowId: (row) => rowKey(row),
  });

  const filterableCols = columns.filter((c) => c.filterable);

  return (
    <div className={cn("cios-card overflow-hidden", className)}>
      {(searchable || filterableCols.length > 0) && (
        <div className="flex flex-wrap gap-3 border-b border-[var(--cios-border)] p-4">
          {searchable && (
            <SearchInput
              value={globalFilter}
              onChange={setGlobalFilter}
              placeholder={searchPlaceholder}
              className="min-w-[200px] flex-1"
            />
          )}
          {filterableCols.map((col) => {
            const options = [
              ...new Set(rows.map((r) => String(col.getValue?.(r) ?? (r as Record<string, unknown>)[col.key] ?? ""))),
            ].filter(Boolean);
            const column = table.getColumn(col.key);
            const value = (column?.getFilterValue() as string) ?? "";
            return (
              <select
                key={col.key}
                className="cios-input bg-white px-2 py-1.5 text-sm"
                value={value}
                onChange={(e) => column?.setFilterValue(e.target.value || undefined)}
                aria-label={`Filter ${col.header}`}
              >
                <option value="">All {col.header}</option>
                {options.map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
            );
          })}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-[var(--cios-secondary)]">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sorted = header.column.getIsSorted();
                  return (
                    <th key={header.id} className="px-4 py-3">
                      {canSort ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 hover:text-gray-900"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {sorted === "asc" && <ChevronUp className="h-3 w-3" />}
                          {sorted === "desc" && <ChevronDown className="h-3 w-3" />}
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-[var(--cios-secondary)]">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className={cn("border-t border-gray-100", onRowClick && "cursor-pointer hover:bg-gray-50")}
                  onClick={() => onRowClick?.(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
