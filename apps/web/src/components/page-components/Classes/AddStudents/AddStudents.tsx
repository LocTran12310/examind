"use client";

import { Search, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type StudentStaging, useStudentStaging } from "@/hooks/page-hooks/classes/use-member-manager";
import { StudentPicker } from "../StudentPicker/StudentPicker";

/** The draft list of who is about to be added: one row per student, and a last row that is an input. Typing two
 *  characters offers the matching students; picking one turns the input row into a staged row and leaves a fresh
 *  input ready, so a class can be filled by typing names one after another. The magnifier next to it opens the
 *  picker for the other way round — whole old classes, ticked. Nothing is saved until the footer sends the lot in
 *  one request, whichever way the rows arrived.
 *
 *  This is not "Chuyển năm học" and does not replace it (ADR-04): that one moves a whole year by name rule
 *  (10A1 → 11A1) and records how each student left. This one is the small, pointed version — this new class, from
 *  those old classes, chosen by hand. The link below is there because the bigger door is easy to miss from in here,
 *  which is exactly how this screen came to be the only one anybody found. */
export function AddStudents({ classId, onAdd }: { classId: string; onAdd: (userIds: string[]) => Promise<boolean> }) {
  const s = useStudentStaging(classId);
  const [picking, setPicking] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  // the input is the last row of a table that scrolls: what it offers has to be brought into view, not clipped
  useEffect(() => {
    if (s.searching && box.current) box.current.scrollTop = box.current.scrollHeight;
  }, [s.searching, s.matches]);
  return (
    <div className="grid gap-3">
      <div ref={box} className="max-h-96 overflow-y-auto rounded-lg border">
        <Table data-testid="staged-students">
          <TableHeader>
            <TableRow>
              <TableHead>Học sinh</TableHead>
              <TableHead>Tên đăng nhập</TableHead>
              <TableHead>Lớp hiện tại</TableHead>
              <TableHead className="w-8" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {s.staged.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="font-medium">{u.full_name}</TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">{u.username}</TableCell>
                <TableCell className="text-muted-foreground">{s.classLabel(u)}</TableCell>
                <TableCell>
                  <Button type="button" variant="ghost" size="icon-sm" aria-label={`Bỏ ${u.full_name}`} onClick={() => s.unstage(u.id)}>
                    <X />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={4}>
                <div className="flex items-start gap-2">
                  <div className="grid flex-1 gap-1">
                    <Input
                      aria-label="Tìm học sinh để thêm"
                      placeholder="Nhập tên hoặc tên đăng nhập"
                      value={s.q}
                      onChange={(e) => s.setQ(e.target.value)}
                      onKeyDown={(e) => {
                        // Enter takes the first name that can be taken: filling a class is typing, not aiming
                        if (e.key !== "Enter") return;
                        e.preventDefault();
                        const first = s.matches.find((u) => !s.note(u));
                        if (first) pickOne(s, first.id);
                      }}
                    />
                    {s.searching && <Suggestions s={s} />}
                  </div>
                  <Button type="button" variant="outline" size="icon" aria-label="Chọn học sinh từ lớp khác" title="Chọn học sinh từ lớp khác" onClick={() => setPicking(true)}>
                    <Search />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
      <Button disabled={s.staged.length === 0} onClick={() => void onAdd(s.staged.map((u) => u.id))}>
        Thêm {s.staged.length} học sinh
      </Button>
      <p className="text-xs text-muted-foreground">
        Chuyển cả một năm học — mọi lớp, 10A1 lên 11A1, kèm ở lại và tốt nghiệp — thì dùng{" "}
        <Link href="/org/school-years" className="underline hover:text-primary">
          Năm học › Chuyển năm học
        </Link>
        .
      </p>
      <FormDialog open={picking} onOpenChange={setPicking} title="Chọn học sinh" description="Tích cả lớp cũ hoặc từng em, rồi bấm chọn để đưa vào danh sách." wide>
        <StudentPicker
          classId={classId}
          staged={s.ids}
          onConfirm={(users) => {
            s.stage(users);
            setPicking(false);
          }}
          onCancel={() => setPicking(false)}
        />
      </FormDialog>
    </div>
  );
}

/** Stage one match and empty the box, so the next name can be typed straight away. */
function pickOne(s: StudentStaging, id: string) {
  const u = s.matches.find((m) => m.id === id);
  if (!u) return;
  s.stage([u]);
  s.clearQuery();
}

/** What the row input matches, under it inside the same row: in flow rather than floating, because a floating
 *  panel is clipped by the scroll box the table lives in. */
function Suggestions({ s }: { s: StudentStaging }) {
  return (
    <ul aria-label="Học sinh khớp" data-testid="student-suggestions" className="max-h-60 divide-y overflow-y-auto rounded-lg border bg-popover shadow-sm">
      {s.matches.length === 0 && <li className="px-2 py-1.5 text-sm text-muted-foreground">Không có học sinh nào khớp.</li>}
      {s.matches.map((u) => {
        const note = s.note(u);
        return (
          <li key={u.id}>
            {/* whoever cannot be taken stays on the list and says why, instead of the name seeming not to exist */}
            <button
              type="button"
              disabled={!!note}
              onClick={() => pickOne(s, u.id)}
              className="flex w-full items-center gap-2 px-2 py-1.5 text-left text-sm hover:bg-muted disabled:pointer-events-none disabled:opacity-60"
            >
              {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
              <span className="ml-auto text-xs text-muted-foreground">{note || s.classLabel(u)}</span>
            </button>
          </li>
        );
      })}
      {s.more > 0 && <li className="px-2 py-1.5 text-xs text-muted-foreground">Còn {s.more} kết quả nữa — lọc thêm để thấy.</li>}
    </ul>
  );
}
