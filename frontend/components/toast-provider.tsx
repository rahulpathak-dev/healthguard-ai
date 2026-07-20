"use client";

import React from "react";

import { createContext, useContext, useState, type ReactNode } from "react";

type Toast = { id: number; message: string };
const ToastContext = createContext<(message: string) => void>(() => undefined);

export function useToast() { return useContext(ToastContext); }

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  function push(message: string) {
    const id = Date.now();
    setToasts((items) => [...items, { id, message }]);
    window.setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 4500);
  }
  return <ToastContext.Provider value={push}>{children}<div className="toast-region" role="status" aria-live="polite">{toasts.map((toast) => <div className="toast" key={toast.id}>{toast.message}</div>)}</div></ToastContext.Provider>;
}
