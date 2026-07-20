"use client";
import { useEffect, useState, type ReactNode } from "react";
import { apiRequest } from "@/lib/api-client";
type Role = "user" | "doctor" | "admin";
export function RoleGate({ allowed, children }: { allowed: Role[]; children: ReactNode }) {
  const [state, setState] = useState<"loading" | "allowed" | "denied">("loading");
  const roleKey = allowed.join(",");
  useEffect(() => { const accepted = roleKey.split(","); apiRequest<{ role: Role }>("/auth/me").then((user) => setState(accepted.includes(user.role) ? "allowed" : "denied")).catch(() => setState("denied")); }, [roleKey]);
  if (state === "loading") return <p role="status">Checking permissions...</p>;
  if (state === "denied") return <section className="access-denied"><h1>Access restricted</h1><p>Your account does not have permission to view this area.</p></section>;
  return <>{children}</>;
}
