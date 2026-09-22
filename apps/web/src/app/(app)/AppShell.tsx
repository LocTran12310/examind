"use client";

import { usePathname } from "next/navigation";
import { createContext, useContext } from "react";
import { AppSidebar } from "@/components/app/AppSidebar";
import { OrgSwitcher } from "@/components/app/OrgSwitcher";
import { ThemeToggle } from "@/components/app/ThemeToggle";
import { YearSwitcher } from "@/components/app/YearSwitcher";
import { UserMenu } from "@/components/app/UserMenu";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { activeItem, groupsFor } from "@/lib/nav";
import type { Me } from "@/lib/types";

const MeContext = createContext<Me | null>(null);

/** Provides the signed-in user without the shell (tests, isolated widgets). */
export const MeProvider = MeContext.Provider;

/** The signed-in user when inside the shell, else null (components that also render standalone). */
export function useMeMaybe(): Me | null {
  return useContext(MeContext);
}

export function useMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useMe outside AppShell");
  return me;
}

export function AppShell({ me, children, sidebarOpen = true }: { me: Me; children: React.ReactNode; sidebarOpen?: boolean }) {
  const pathname = usePathname();
  const item = activeItem(me.role, pathname, me.is_super);
  const group = item && groupsFor(me.role, me.is_super).find((g) => g.items.includes(item));
  return (
    <MeContext.Provider value={me}>
      <SidebarProvider defaultOpen={sidebarOpen}>
        <AppSidebar me={me} />
        <SidebarInset className="h-svh min-w-0 overflow-hidden">
          <header className="z-20 flex h-14 shrink-0 items-center gap-1 border-b bg-background px-2 sm:gap-2 sm:px-3">
            <SidebarTrigger aria-label="Mở menu" />
            <Separator orientation="vertical" className="mx-1 hidden h-5 sm:block" />
            <div className="hidden min-w-0 flex-1 truncate text-sm sm:block">
              {group && <span className="hidden text-muted-foreground md:inline">{group.label} / </span>}
              <span className="font-medium">{item?.label ?? "Examind"}</span>
            </div>
            <div className="ml-auto flex min-w-0 shrink-0 items-center gap-1">
              <OrgSwitcher me={me} />
              <YearSwitcher />
              <Separator orientation="vertical" className="mx-1 hidden h-5 sm:block" />
              <ThemeToggle />
              <UserMenu me={me} />
            </div>
          </header>
          <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-auto p-2 sm:p-3 lg:p-4">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </MeContext.Provider>
  );
}
