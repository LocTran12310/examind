"use client";

import { usePathname } from "next/navigation";
import { createContext, useContext } from "react";
import { AppSidebar } from "@/components/app/AppSidebar";
import { OrgSwitcher } from "@/components/app/OrgSwitcher";
import { ThemeToggle } from "@/components/app/ThemeToggle";
import { UserMenu } from "@/components/app/UserMenu";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { activeItem, groupsFor } from "@/lib/nav";
import type { Me } from "@/lib/types";

const MeContext = createContext<Me | null>(null);

/** Provides the signed-in user without the shell (tests, isolated widgets). */
export const MeProvider = MeContext.Provider;

export function useMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useMe outside AppShell");
  return me;
}

export function AppShell({ me, children, sidebarOpen = true }: { me: Me; children: React.ReactNode; sidebarOpen?: boolean }) {
  const pathname = usePathname();
  const item = activeItem(me.role, pathname);
  const group = item && groupsFor(me.role).find((g) => g.items.includes(item));
  return (
    <MeContext.Provider value={me}>
      <SidebarProvider defaultOpen={sidebarOpen}>
        <AppSidebar me={me} />
        <SidebarInset className="min-w-0">
          <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 px-3 backdrop-blur">
            <SidebarTrigger aria-label="Mở menu" />
            <Separator orientation="vertical" className="mx-1 h-5" />
            <div className="min-w-0 flex-1 truncate text-sm">
              {group && <span className="hidden text-muted-foreground md:inline">{group.label} / </span>}
              <span className="font-medium">{item?.label ?? "Examind"}</span>
            </div>
            <div className="flex items-center gap-1">
              <OrgSwitcher current={me.org} />
              <Separator orientation="vertical" className="mx-1 h-5" />
              <ThemeToggle />
              <UserMenu me={me} />
            </div>
          </header>
          <main className="min-w-0 flex-1 p-4 lg:p-6">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </MeContext.Provider>
  );
}
