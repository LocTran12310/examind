"use client";

import { Building2, Check, ChevronsUpDown } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { OrgRef } from "@/lib/types";

/** Header organisation selector. `orgs` defaults to the current org only (switching arrives with memberships). */
export function OrgSwitcher({ current, orgs = [current], onSwitch }: { current: OrgRef; orgs?: OrgRef[]; onSwitch?: (org: OrgRef) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} aria-label="Chọn tổ chức" className="max-w-64 justify-between gap-2">
          <Building2 className="text-muted-foreground" />
          <span className="truncate">{current.name}</span>
          <ChevronsUpDown className="text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-72 p-0">
        <Command>
          {orgs.length > 6 && <CommandInput placeholder="Tìm tổ chức…" />}
          <CommandList>
            <CommandEmpty>Không có tổ chức</CommandEmpty>
            <CommandGroup heading="Tổ chức">
              {orgs.map((o) => (
                <CommandItem
                  key={o.id}
                  value={`${o.code} ${o.name}`}
                  onSelect={() => {
                    setOpen(false);
                    if (o.id !== current.id) onSwitch?.(o);
                  }}
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate">{o.name}</div>
                    <div className="text-xs text-muted-foreground">{o.code}</div>
                  </div>
                  {o.id === current.id && <Check />}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
