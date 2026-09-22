"use client";

import { Building2, Check, ChevronsUpDown, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ROLE_LABEL } from "@/constants/role.constant";
import { useOrgSwitcher } from "@/hooks/page-hooks/layout/use-org-switcher";
import type { Me } from "@/interfaces/auth.interface";

/** Header organisation selector: the orgs the user belongs to (every org for a super admin). */
export function OrgSwitcher({ me }: { me: Me }) {
  const { open, setOpen, busy, single, searchable, orgs, choose } = useOrgSwitcher(me);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} aria-label="Chọn tổ chức" className="max-w-28 min-w-0 justify-between gap-1.5 px-2 sm:max-w-64 sm:gap-2 sm:px-2.5" disabled={busy}>
          <Building2 className="text-muted-foreground" />
          <span className="truncate">{me.org.name}</span>
          {!single && <ChevronsUpDown className="hidden text-muted-foreground sm:block" />}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <Command>
          {searchable && <CommandInput placeholder="Tìm tổ chức…" />}
          <CommandList>
            <CommandEmpty>Không có tổ chức</CommandEmpty>
            <CommandGroup heading={single ? "Bạn chỉ thuộc một tổ chức" : "Chuyển tổ chức"}>
              {orgs.map((o) => (
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
