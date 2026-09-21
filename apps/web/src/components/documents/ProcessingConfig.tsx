"use client";

import { Field, Input, Select } from "@/components/ui";
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
      <Field label="Chế độ tách câu">
        <Select className="w-full" value={value.split_mode} onChange={(e) => set("split_mode", e.target.value as ProcessingConfig["split_mode"])}>
          {MODES.map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Đọc ảnh scan (OCR)">
        <Select className="w-full" value={value.ocr} onChange={(e) => set("ocr", e.target.value as ProcessingConfig["ocr"])}>
          {OCR.map(([k, v]) => (
            <option key={k} value={k} disabled={k === "vision" && vision.length === 0}>
              {v}
            </option>
          ))}
        </Select>
      </Field>
      {value.split_mode !== "rule" && (
        <>
          <Field label="Model tách câu" hint={text.length ? undefined : "Chưa có model — thêm ở trang Model AI"}>
            <Select className="w-full" value={primary} onChange={(e) => set("split_models", [e.target.value, fallback].filter(Boolean))}>
              <option value="">—</option>
              {text.map((m) => (
                <option key={m.id} value={m.id}>
                  {label(m)}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Model dự phòng">
            <Select className="w-full" value={fallback} onChange={(e) => set("split_models", [primary, e.target.value].filter(Boolean))}>
              <option value="">—</option>
              {text.filter((m) => m.id !== primary).map((m) => (
                <option key={m.id} value={m.id}>
                  {label(m)}
                </option>
              ))}
            </Select>
          </Field>
        </>
      )}
      <Field label="Model gắn chuyên đề" hint="Để trống: chỉ dùng từ khóa">
        <Select className="w-full" value={value.tag_model ?? ""} onChange={(e) => set("tag_model", e.target.value || null)}>
          <option value="">—</option>
          {text.map((m) => (
            <option key={m.id} value={m.id}>
              {label(m)}
            </option>
          ))}
        </Select>
      </Field>
      {value.ocr === "vision" && (
        <Field label="Model đọc ảnh">
          <Select className="w-full" value={value.vision_model ?? ""} onChange={(e) => set("vision_model", e.target.value || null)}>
            <option value="">—</option>
            {vision.map((m) => (
              <option key={m.id} value={m.id}>
                {label(m)}
              </option>
            ))}
          </Select>
        </Field>
      )}
      {showThreshold && (
        <Field label="Ngưỡng tự duyệt" hint="Câu có độ tin cậy từ ngưỡng này trở lên được duyệt tự động">
          <Input type="number" step="0.05" min={0.5} max={1} value={value.threshold} onChange={(e) => set("threshold", Number(e.target.value))} />
        </Field>
      )}
    </div>
  );
}

export function ProcessingConfigPanel(props: Parameters<typeof ProcessingConfigFields>[0]) {
  return (
    <details className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-2" data-testid="processing-config">
      <summary className="cursor-pointer text-sm font-medium text-gray-700">Cấu hình xử lý</summary>
      <div className="pt-3">
        <ProcessingConfigFields {...props} />
      </div>
    </details>
  );
}
