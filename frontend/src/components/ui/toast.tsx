"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "warning" | "error";
type Toast = { id: number; type: ToastType; message: string };

type ToastContextValue = {
  toast: (type: ToastType, message: string) => void;
};

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((type: ToastType, message: string) => {
    const id = Date.now();
    setToasts((t) => [...t, { id, type, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-4 py-3 text-sm shadow-lg",
              t.type === "success" && "border-green-200 bg-green-50 text-green-900",
              t.type === "warning" && "border-amber-200 bg-amber-50 text-amber-900",
              t.type === "error" && "border-red-200 bg-red-50 text-red-900",
            )}
          >
            {t.type === "success" && <CheckCircle2 className="h-4 w-4" />}
            {t.type === "warning" && <AlertTriangle className="h-4 w-4" />}
            {t.type === "error" && <XCircle className="h-4 w-4" />}
            <span>{t.message}</span>
            <button type="button" className="ml-2" onClick={() => setToasts((x) => x.filter((i) => i.id !== t.id))} aria-label="Dismiss">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
