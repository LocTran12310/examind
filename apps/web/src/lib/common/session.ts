import "server-only";
import { cookies } from "next/headers";
import type { Me } from "@/interfaces/auth.interface";

const API = process.env.API_INTERNAL_URL ?? "http://localhost:58100";

/** Server-side fetch to the API with the browser's cookies forwarded. */
export async function serverApi<T>(path: string): Promise<{ status: number; data: T | null }> {
  const jar = await cookies();
  const cookie = jar
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");
  const res = await fetch(`${API}/api${path}`, { headers: { cookie }, cache: "no-store" });
  if (!res.ok) return { status: res.status, data: null };
  return { status: res.status, data: (await res.json()) as T };
}

export async function getMe(): Promise<Me | null> {
  const { data } = await serverApi<Me>("/auth/me");
  return data;
}
