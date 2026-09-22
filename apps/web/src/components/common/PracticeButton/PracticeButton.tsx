"use client";

import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { Button } from "@/components/ui/button";
import { usePracticeButton } from "@/hooks/common/use-practice-button";

/** A student starts a personal practice exam (home, my progress). */
export function PracticeButton({ count = 20 }: { count?: number }) {
  const p = usePracticeButton(count);
  return (
    <div>
      <Button disabled={p.busy} onClick={p.start}>
        {p.busy ? "Đang tạo đề…" : "Tạo đề ôn tập"}
      </Button>
      {p.error && (
        <div className="mt-2">
          <FormAlert>{p.error}</FormAlert>
        </div>
      )}
    </div>
  );
}
