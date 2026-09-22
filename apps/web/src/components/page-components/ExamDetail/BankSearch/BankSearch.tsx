import { Panel } from "@/components/common/Panel/Panel";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ParsedQuestion } from "@/interfaces/question.interface";

export interface BankSearchProps {
  search: string;
  onSearchChange: (v: string) => void;
  onFind: () => void;
  found: ParsedQuestion[];
  inExam: Set<string>;
  onAdd: (id: string) => void;
}

/** "Thêm từ ngân hàng": search the bank and add one question at a time. */
export function BankSearch({ search, onSearchChange, onFind, found, inExam, onAdd }: BankSearchProps) {
  return (
    <Panel>
      <h2 className="mb-2 font-medium">Thêm từ ngân hàng</h2>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          onFind();
        }}
      >
        <Input placeholder="Tìm câu hỏi…" value={search} onChange={(e) => onSearchChange(e.target.value)} />
        <Button variant="outline" type="submit">
          Tìm
        </Button>
      </form>
      <ul className="mt-2 divide-y divide-border text-sm" data-testid="bank-results">
        {found.map((q) => (
          <li key={q.id} className="flex items-start gap-2 py-2">
            <div className="line-clamp-2 min-w-0 flex-1">
              <Markdown>{q.stem}</Markdown>
            </div>
            <Button variant="outline" size="sm" disabled={inExam.has(q.id)} onClick={() => onAdd(q.id)}>
              {inExam.has(q.id) ? "Đã có" : "Thêm"}
            </Button>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
