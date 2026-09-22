/** Folder rules of the web app (architecture-refactor AC-04, T-07-03): the old layout is gone, routes are thin,
 *  screens get data through query hooks only. ESLint enforces the import rules file by file; this checks the tree. */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const SRC = path.resolve(process.cwd(), "src");
const rel = (f: string) => path.relative(SRC, f).split(path.sep).join("/");

function files(dir: string, keep: (f: string) => boolean = () => true): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const f = path.join(dir, name);
    if (statSync(f).isDirectory()) out.push(...files(f, keep));
    else if (keep(f)) out.push(f);
  }
  return out;
}
const source = (f: string) => /\.(ts|tsx)$/.test(f);
const isTest = (f: string) => /\.test\.(ts|tsx)$/.test(f) || rel(f).startsWith("__tests__/");
const imports = (code: string) => [...code.matchAll(/^import\s[^;]*?from\s+"([^"]+)";?$/gm)].map((m) => m[1]);

describe("web architecture", () => {
  it("the old layout is gone", () => {
    const removed = [
      "components/app", "components/data-table", "components/adaptive", "components/reports", "components/topics",
      "lib/hooks.ts", "lib/api.ts", "lib/types.ts", "app/(app)/AppShell.tsx",
    ];
    expect(removed.filter((p) => existsSync(path.join(SRC, p)))).toEqual([]);
    expect(readdirSync(path.join(SRC, "components")).sort()).toEqual(["common", "layout", "page-components", "ui"]);
    expect(readdirSync(path.join(SRC, "lib")).sort()).toEqual(["common", "page-libs", "utils.ts"]);
  });

  it("every route is thin: a page.tsx renders one page component (or only redirects)", () => {
    const bad: string[] = [];
    for (const f of files(path.join(SRC, "app"), (x) => path.basename(x) === "page.tsx")) {
      const code = readFileSync(f, "utf8");
      const from = imports(code);
      const pages = from.filter((m) => m.startsWith("@/components/page-components/"));
      if (/<[A-Z]/.test(code)) {
        const other = from.filter((m) => m !== "react" && !m.startsWith("@/components/page-components/"));
        if (pages.length !== 1 || other.length) bad.push(`${rel(f)}: ${from.join(", ")}`);
      } else if (!/\bredirect\(/.test(code) || from.some((m) => m.startsWith("@/components/") || m.startsWith("@/hooks/") || m.startsWith("@/services/"))) {
        bad.push(`${rel(f)}: neither a page component nor a redirect`);
      }
    }
    expect(bad).toEqual([]);
  });

  it("no useApi, and no fetch outside services and the http client", () => {
    const all = files(SRC, source).filter((f) => rel(f) !== "__tests__/architecture.test.ts");
    expect(all.filter((f) => /\buseApi\b/.test(readFileSync(f, "utf8"))).map(rel)).toEqual([]);
    const screens = all.filter((f) => !isTest(f) && /^(components|hooks\/page-hooks)\//.test(rel(f)) && !rel(f).startsWith("components/ui/"));
    expect(screens.filter((f) => /\bfetch\(/.test(readFileSync(f, "utf8"))).map(rel)).toEqual([]);
  });

  it("services, query hooks and page hooks follow their naming", () => {
    const names = (dir: string) => readdirSync(path.join(SRC, dir));
    expect(names("services").filter((n) => !/^[a-z-]+\.service\.ts$/.test(n))).toEqual([]);
    expect(names("hooks/react-query").filter((n) => !/^use-(query-[a-z-]+|search-query)\.ts$/.test(n))).toEqual([]);
    const pageHooks = files(path.join(SRC, "hooks/page-hooks"), source).map(rel);
    expect(pageHooks.filter((f) => !/^hooks\/page-hooks\/[a-z-]+\/use-[a-z-]+\.tsx?$/.test(f))).toEqual([]);
  });

  it("page components live in PascalCase folders named after their file", () => {
    const bad = files(path.join(SRC, "components/page-components"), (f) => f.endsWith(".tsx") && !isTest(f))
      .map(rel)
      .filter((f) => {
        const parts = f.split("/");
        const file = parts.at(-1)!.replace(/\.tsx$/, "");
        const folder = parts.at(-2)!;
        return !/^[A-Z][A-Za-z]+$/.test(folder) || !(file === folder || file === `${folder}Page`);
      });
    expect(bad).toEqual([]);
  });
});
