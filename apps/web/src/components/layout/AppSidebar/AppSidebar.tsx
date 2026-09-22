"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import { APP_ICON, activeItem, groupsFor, homeFor } from "@/lib/common/nav";
import type { Me } from "@/interfaces/auth.interface";

export function AppSidebar({ me }: { me: Me }) {
  const pathname = usePathname();
  const { isMobile, setOpenMobile } = useSidebar();
  const active = activeItem(me.role, pathname, me.is_super);
  const close = () => isMobile && setOpenMobile(false);
  return (
    <Sidebar collapsible="icon" aria-label="Điều hướng chính">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href={homeFor(me.role)} onClick={close}>
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <APP_ICON className="size-4" />
                </div>
                <div className="grid flex-1 text-left leading-tight">
                  <span className="truncate font-semibold">Examind</span>
                  <span className="truncate text-xs opacity-70">{me.org.name}</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {groupsFor(me.role, me.is_super).map((g) => (
          <SidebarGroup key={g.label}>
            <SidebarGroupLabel>{g.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {g.items.map((n) => (
                  <SidebarMenuItem key={n.href}>
                    <SidebarMenuButton asChild isActive={active?.href === n.href} tooltip={n.label}>
                      <Link href={n.href} onClick={close} aria-current={active?.href === n.href ? "page" : undefined}>
                        <n.icon />
                        <span>{n.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter className="text-xs opacity-70 group-data-[collapsible=icon]:hidden">v0.2 · Examind</SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
