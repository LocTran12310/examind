import { Panel } from "@/components/common/Panel/Panel";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TYPE_LABEL } from "@/constants/question.constant";
import type { ExamSettings } from "@/interfaces/exam.interface";
import type { QuestionType } from "@/interfaces/question.interface";

/** "Điểm mặc định theo loại câu": saved when a field loses focus with a new value. */
export function PointsByType({ settings, onChange }: { settings: ExamSettings; onChange: (type: QuestionType, points: number) => void }) {
  return (
    <Panel id="diem-mac-dinh">
      <h2 className="mb-2 font-medium">Điểm mặc định theo loại câu</h2>
      <p className="mb-2 text-sm text-muted-foreground">Đổi ở đây sẽ áp lại cho mọi câu cùng loại trong đề, kể cả câu đã sửa điểm riêng — xem “Thang điểm của đề”.</p>
      <div className="grid grid-cols-2 gap-2 text-sm">
        {(Object.keys(TYPE_LABEL) as QuestionType[]).map((t) => (
          <Label key={t} className="justify-between font-normal">
            {TYPE_LABEL[t]}
            <Input
              aria-label={`Điểm ${TYPE_LABEL[t]}`}
              type="number"
              step="0.05"
              min={0.05}
              className="h-8 w-20"
              defaultValue={settings.points_by_type[t]}
              onBlur={(e) => Number(e.target.value) !== settings.points_by_type[t] && onChange(t, Number(e.target.value))}
            />
          </Label>
        ))}
      </div>
    </Panel>
  );
}
