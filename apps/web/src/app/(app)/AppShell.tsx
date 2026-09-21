"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, useContext } from "react";
import { api } from "@/lib/api";
import { navFor } from "@/lib/nav";
import { ROLE_LABEL, type Me } from "@/lib/types";

const MeContext = createContext<Me | null>(null);

export function useMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useMe outside AppShell");
  return me;
}

export function AppShell({ me, children }: { me: Me; children: React.ReactNode }) {
  const pathname = usePathname();
  async function logout() {
    await api("/auth/logout", { method: "POST" }).catch(() => undefined);
    window.location.assign("/login");
  }
  return (
    <MeContext.Provider value={me}>
      <div className="min-h-screen">
        <header className="border-b border-gray-200 bg-white">
          <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-4">
            <Link href="/" className="font-semibold text-brand-700">
              Examind
            </Link>
            <nav className="flex flex-1 gap-1 overflow-x-auto">
              {navFor(me.role).map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className={clsx(
                    "whitespace-nowrap rounded-md px-3 py-1.5 text-sm",
                    pathname.startsWith(n.href) ? "bg-brand-50 font-medium text-brand-700" : "text-gray-600 hover:bg-gray-100",
                  )}
                >
                  {n.label}
                </Link>
              ))}
            </nav>
            <div className="text-right text-xs leading-tight">
              <div className="font-medium">{me.full_name}</div>
              <div className="text-gray-500">
                {me.org.name} · {ROLE_LABEL[me.role]}
              </div>
            </div>
            <button onClick={logout} className="text-sm text-gray-600 hover:text-gray-900">
              Đăng xuất
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </div>
    </MeContext.Provider>
  );
}
