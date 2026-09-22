"use client";

import { Building2, Check, ChevronsUpDown, Home } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { homeFor } from "@/lib/nav";
import { type Me, type MyOrg, ROLE_LABEL } from "@/lib/types";

/** Header organisation selector: the orgs the user belongs to (every org for a super admin). */
export function OrgSwitcher({ me }: { me: Me }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const { data } = useApi<MyOrg[]>("/me/orgs");
  const orgs = data ?? [];
  const single = orgs.length <= 1;

  async function choose(o: MyOrg) {
    setOpen(false);
    if (o.id === me.org.id) return;
    setBusy(true);
    try {
      const next = await api<Me>("/auth/switch-org", { body: { org_id: o.id } });
      window.location.assign(homeFor(next.role)); // full reload: every screen refetches inside the new org
    } catch (e) {
      setBusy(false);
      toast.error(e instanceof ApiError ? e.message : "Không chuyển được tổ chức");
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} aria-label="Chọn tổ chức" className="max-w-64 justify-between gap-2" disabled={busy}>
          <Building2 className="text-muted-foreground" />
          <span className="truncate">{me.org.name}</span>
          {!single && <ChevronsUpDown className="text-muted-foreground" />}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <Command>
          {orgs.length > 6 && <CommandInput placeholder="Tìm tổ chức…" />}
          <CommandList>
            <CommandEmpty>Không có tổ chức</CommandEmpty>
            <CommandGroup heading={single ? "Bạn chỉ thuộc một tổ chức" : "Chuyển tổ chức"}>
              {(orgs.length ? orgs : [{ ...me.org, role: me.role, is_home: true }]).map((o) => (
                <CommandItem key={o.id} value={`${o.code} ${o.name}`} onSelect={() => void choose(o)}>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1 truncate">
                      {o.name}
                      {o.is_home && <Home className="size-3 text-muted-foreground" aria-label="Tổ chức gốc" />}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {o.code} · {ROLE_LABEL[o.role]}
                    </div>
                  </div>
                  {o.id === me.org.id && <Check />}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
