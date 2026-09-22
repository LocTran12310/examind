"use client";

import { FormField } from "@/components/app/FormField";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import type { AiModel, ProcessingConfig } from "@/lib/types";

const MODES: [ProcessingConfig["split_mode"], string][] = [
  ["rule", "Chỉ quy tắc (nhanh, miễn phí)"],
  ["rule_ai", "Quy tắc + AI cho câu khó"],
  ["ai", "AI cho toàn bộ"],
];
const OCR: [ProcessingConfig["ocr"], string][] = [
  ["auto", "Tự động (Tesseract)"],
  ["tesseract", "Tesseract"],
  ["vision", "AI đọc ảnh"],
];

export function ProcessingConfigFields({
  value,
  onChange,
  models,
  showThreshold,
}: {
  value: ProcessingConfig;
  onChange: (v: ProcessingConfig) => void;
  models: AiModel[];
  showThreshold?: boolean;
}) {
  const text = models.filter((m) => m.enabled && m.capabilities.includes("text"));
  const vision = models.filter((m) => m.enabled && m.capabilities.includes("vision"));
  const set = <K extends keyof ProcessingConfig>(k: K, v: ProcessingConfig[K]) => onChange({ ...value, [k]: v });
  const label = (m: AiModel) => `${m.name}${m.is_free ? " · Free" : " · Trả phí"}${m.system ? " · Hệ thống" : ""}`;
  const [primary, fallback] = [value.split_models[0] ?? "", value.split_models[1] ?? ""];

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <FormField label="Chế độ tách câu">
        <NativeSelect className="w-full" value={value.split_mode} onChange={(e) => set("split_mode", e.target.value as ProcessingConfig["split_mode"])}>
          {MODES.map(([k, v]) => (
            <NativeSelectOption key={k} value={k}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </FormField>
      <FormField label="Đọc ảnh scan (OCR)">
        <NativeSelect className="w-full" value={value.ocr} onChange={(e) => set("ocr", e.target.value as ProcessingConfig["ocr"])}>
          {OCR.map(([k, v]) => (
            <NativeSelectOption key={k} value={k} disabled={k === "vision" && vision.length === 0}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </FormField>
      {value.split_mode !== "rule" && (
        <>
          <FormField label="Model tách câu" hint={text.length ? undefined : "Chưa có model — thêm ở trang Model AI"}>
            <NativeSelect className="w-full" value={primary} onChange={(e) => set("split_models", [e.target.value, fallback].filter(Boolean))}>
              <NativeSelectOption value="">—</NativeSelectOption>
              {text.map((m) => (
                <NativeSelectOption key={m.id} value={m.id}>
                  {label(m)}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </FormField>
          <FormField label="Model dự phòng">
            <NativeSelect className="w-full" value={fallback} onChange={(e) => set("split_models", [primary, e.target.value].filter(Boolean))}>
              <NativeSelectOption value="">—</NativeSelectOption>
              {text.filter((m) => m.id !== primary).map((m) => (
                <NativeSelectOption key={m.id} value={m.id}>
                  {label(m)}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </FormField>
        </>
      )}
      <FormField label="Model gắn chuyên đề" hint="Để trống: chỉ dùng từ khóa">
        <NativeSelect className="w-full" value={value.tag_model ?? ""} onChange={(e) => set("tag_model", e.target.value || null)}>
          <NativeSelectOption value="">—</NativeSelectOption>
          {text.map((m) => (
            <NativeSelectOption key={m.id} value={m.id}>
              {label(m)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </FormField>
      {value.ocr === "vision" && (
        <FormField label="Model đọc ảnh">
          <NativeSelect className="w-full" value={value.vision_model ?? ""} onChange={(e) => set("vision_model", e.target.value || null)}>
            <NativeSelectOption value="">—</NativeSelectOption>
            {vision.map((m) => (
              <NativeSelectOption key={m.id} value={m.id}>
                {label(m)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FormField>
      )}
      {showThreshold && (
        <FormField label="Ngưỡng tự duyệt" hint="Câu có độ tin cậy từ ngưỡng này trở lên được duyệt tự động">
          <Input type="number" step="0.05" min={0.5} max={1} value={value.threshold} onChange={(e) => set("threshold", Number(e.target.value))} />
        </FormField>
      )}
    </div>
  );
}

export function ProcessingConfigPanel(props: Parameters<typeof ProcessingConfigFields>[0]) {
  return (
    <Collapsible className="group/config rounded-lg border border-border bg-muted/50 px-4 py-2" data-testid="processing-config">
      <CollapsibleTrigger className="flex w-full cursor-pointer items-center gap-1.5 text-left text-sm font-medium text-foreground/80">
        <ChevronRight className="size-4 transition-transform group-data-[state=open]/config:rotate-90" />
        Cấu hình xử lý
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-3">
        <ProcessingConfigFields {...props} />
      </CollapsibleContent>
    </Collapsible>
  );
}
