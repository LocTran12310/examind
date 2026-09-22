import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProcessingConfigFields } from "@/components/common/ProcessingConfig/ProcessingConfig";
import { UploadForm } from "@/components/page-components/Documents/UploadForm/UploadForm";
import type { AiModel, ProcessingConfig } from "@/lib/types";
import { mockFetch, renderWithQuery as render, route } from "./helpers";

const base: ProcessingConfig = { split_mode: "rule", ocr: "auto", split_models: [], tag_model: null, vision_model: null, threshold: 0.85 };
const m = (id: string, caps: AiModel["capabilities"] = ["text"], is_free = true): AiModel => ({
  id, name: id, provider: "ollama", model: id, base_url: null, capabilities: caps, is_free, enabled: true, system: false, has_key: false, editable: true,
});

function Harness({ onChange }: { onChange: (v: ProcessingConfig) => void }) {
  const [v, setV] = useState(base);
  return <ProcessingConfigFields value={v} onChange={(x) => (setV(x), onChange(x))} models={[m("qwen"), m("gpt", ["text"], false), m("vl", ["text", "vision"])]} />;
}

afterEach(() => vi.unstubAllGlobals());

async function pick(field: string, option: string) {
  await userEvent.click(screen.getByRole("combobox", { name: field }));
  await userEvent.click(await screen.findByRole("option", { name: option }));
}

describe("processing config", () => {
  it("picks mode, split models with fallback, and vision model", async () => {
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);
    expect(screen.queryByLabelText("Model tách câu")).toBeNull();
    await pick("Chế độ tách câu", "Quy tắc + AI cho câu khó");
    await pick("Model tách câu", "qwen · Free");
    await pick("Model dự phòng", "gpt · Trả phí");
    await pick("Đọc ảnh scan (OCR)", "AI đọc ảnh");
    await pick("Model đọc ảnh", "vl · Free");
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ split_mode: "rule_ai", split_models: ["qwen", "gpt"], ocr: "vision", vision_model: "vl" }));
    expect(screen.getByRole("combobox", { name: "Model dự phòng" })).toHaveTextContent("gpt · Trả phí");
  });

  it("upload sends the chosen config", async () => {
    const f = mockFetch(route("POST", "/api/documents", { document: { id: "d" }, duplicate: false }, 201));
    const tax = { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [], semesters: [] };
    render(<UploadForm taxonomy={tax} onUploaded={() => {}} config={{ ...base, split_mode: "rule_ai", split_models: ["qwen"] }} />);
    fireEvent.change(screen.getByTestId("file"), { target: { files: [new File(["x"], "a.docx")] } });
    await userEvent.click(await screen.findByRole("button", { name: "Tải lên và tách câu" })); // after the duplicate check
    const upload = () => f.mock.calls.find(([url, init]) => url === "/api/documents" && init?.method === "POST");
    await waitFor(() => expect(upload()).toBeDefined());
    const form = upload()![1]?.body as FormData;
    expect(JSON.parse(String(form.get("config")))).toMatchObject({ split_mode: "rule_ai", split_models: ["qwen"] });
  });
});
