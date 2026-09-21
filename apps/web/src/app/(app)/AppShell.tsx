"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { groupsFor, navFor } from "@/lib/nav";
import { ROLE_LABEL, type Me } from "@/lib/types";

const MeContext = createContext<Me | null>(null);

export function useMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useMe outside AppShell");
  return me;
}

async function logout() {
  await api("/auth/logout", { method: "POST" }).catch(() => undefined);
  window.location.assign("/login");
}

export function Sidebar({ me, pathname, onNavigate }: { me: Me; pathname: string; onNavigate?: () => void }) {
  return (
    <nav aria-label="Điều hướng chính" className="space-y-5 text-sm">
      {groupsFor(me.role).map((g) => (
        <div key={g.label}>
          <div className="mb-1 px-3 text-xs font-medium uppercase tracking-wide text-gray-400">{g.label}</div>
          <ul>
            {g.items.map((n) => (
              <li key={n.href}>
                <Link
                  href={n.href}
                  onClick={onNavigate}
                  aria-current={pathname.startsWith(n.href) ? "page" : undefined}
                  className={clsx(
                    "block rounded-md px-3 py-1.5",
                    pathname.startsWith(n.href) ? "bg-brand-50 font-medium text-brand-700" : "text-gray-700 hover:bg-gray-100",
                  )}
                >
                  {n.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function UserBox({ me }: { me: Me }) {
  return (
    <div className="text-xs leading-tight">
      <div className="font-medium">{me.full_name}</div>
      <div className="text-gray-500">
        {me.org.name} · {ROLE_LABEL[me.role]}
      </div>
      <button onClick={logout} className="mt-2 text-gray-600 hover:text-gray-900">
        Đăng xuất
      </button>
    </div>
  );
}

export function AppShell({ me, children }: { me: Me; children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);

  if (me.role === "student") {
    return (
      <MeContext.Provider value={me}>
        <div className="min-h-screen">
          <header className="border-b border-gray-200 bg-white">
            <div className="mx-auto flex h-14 max-w-5xl items-center gap-4 px-4">
              <Link href="/home" className="font-semibold text-brand-700">
                Examind
              </Link>
              <nav className="flex flex-1 gap-1 overflow-x-auto text-sm">
                {navFor(me.role).map((n) => (
                  <Link key={n.href} href={n.href} className={clsx("whitespace-nowrap rounded-md px-3 py-1.5", pathname.startsWith(n.href) ? "bg-brand-50 font-medium text-brand-700" : "text-gray-600 hover:bg-gray-100")}>
                    {n.label}
                  </Link>
                ))}
              </nav>
              <button onClick={logout} className="text-sm text-gray-600">
                Đăng xuất
              </button>
            </div>
          </header>
          <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
        </div>
      </MeContext.Provider>
    );
  }

  return (
    <MeContext.Provider value={me}>
      <div className="min-h-screen lg:flex">
        <aside className="hidden w-60 shrink-0 flex-col justify-between border-r border-gray-200 bg-white p-4 lg:flex">
          <div>
            <Link href="/" className="mb-6 block px-3 font-semibold text-brand-700">
              Examind
            </Link>
            <Sidebar me={me} pathname={pathname} />
          </div>
          <UserBox me={me} />
        </aside>
        <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 lg:hidden">
          <button aria-label="Mở menu" onClick={() => setOpen(true)} className="rounded-md px-2 py-1 text-xl">
            ☰
          </button>
          <span className="font-semibold text-brand-700">Examind</span>
          <span className="w-8" />
        </header>
        {open && (
          <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-label="Menu">
            <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
            <div className="absolute inset-y-0 left-0 flex w-72 flex-col justify-between overflow-y-auto bg-white p-4">
              <Sidebar me={me} pathname={pathname} onNavigate={() => setOpen(false)} />
              <UserBox me={me} />
            </div>
          </div>
        )}
        <main className="min-w-0 flex-1 px-4 py-6 lg:px-8">{children}</main>
      </div>
    </MeContext.Provider>
  );
}
