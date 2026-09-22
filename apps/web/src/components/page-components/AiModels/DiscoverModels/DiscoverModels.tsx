"use client";

import { Radar } from "lucide-react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDiscoverModels } from "@/hooks/page-hooks/ai-models/use-discover-models";
import type { ModelDraft } from "@/interfaces/ai-model.interface";
import { emptyDraft } from "@/lib/page-libs/ai-models/model-draft";

/** Lists the models of an Ollama server; "Thêm" opens the add form pre-filled. */
export function DiscoverModels({ onPick }: { onPick: (draft: ModelDraft) => void }) {
  const { url, setUrl, busy, found, run } = useDiscoverModels();
  return (
    <div className="grid gap-3">
      <div className="flex items-end gap-2">
        <FormField label="Máy chủ Ollama" className="flex-1">
          <Input placeholder="Mặc định theo cấu hình máy chủ (OLLAMA_URL)" value={url} onChange={(e) => setUrl(e.target.value)} />
        </FormField>
        <Button disabled={busy} onClick={run}>
          <Radar /> Phát hiện
        </Button>
      </div>
      {found?.error && <FormAlert kind="warning">{found.error}</FormAlert>}
      {found && !found.error && found.models.length === 0 && <p className="text-sm text-muted-foreground">Ollama chưa có model nào — chạy `ollama pull qwen2.5:7b`.</p>}
      {found && found.models.length > 0 && (
        <ul className="divide-y text-sm" data-testid="discovered">
          {found.models.map((d) => (
            <li key={d.model} className="flex items-center justify-between py-2">
              <span>
                <span className="font-mono">{d.model}</span> <span className="text-muted-foreground">{d.parameter_size}</span>
                {d.capabilities.includes("vision") && <span className="ml-2 text-xs text-primary">đọc ảnh</span>}
              </span>
              <Button variant="outline" size="sm" onClick={() => onPick(emptyDraft({ name: d.model, model: d.model, base_url: found.base_url, capabilities: d.capabilities }))}>
                Thêm
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
