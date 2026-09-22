import { readdirSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

describe("components/ui", () => {
  it("contains only shadcn-generated files (no custom barrel)", () => {
    const dir = path.resolve(__dirname, "../components/ui");
    expect(readdirSync(dir)).not.toContain("index.tsx");
  });
});
