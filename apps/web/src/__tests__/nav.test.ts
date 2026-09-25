import { describe, expect, it } from "vitest";
import type { Role } from "@/interfaces/auth.interface";
import { NAV_GROUPS, activeItem, groupsFor, homeFor, navFor, rolesUnder } from "@/lib/common/nav";

const hrefs = (role: Role, isSuper = false) => navFor(role, isSuper).map((i) => i.href);

describe("nested roles (AC-06, ADR-02)", () => {
  it("HS ⊂ GV ⊂ Admin, with the platform role outside the chain", () => {
    expect(rolesUnder("student")).toEqual(["student"]);
    expect(rolesUnder("teacher")).toEqual(["student", "teacher"]);
    expect(rolesUnder("org_admin")).toEqual(["student", "teacher", "org_admin"]);
    expect(rolesUnder("super_admin")).toEqual(["super_admin"]);
  });

  it("a teacher sees everything a student sees plus the teacher's own", () => {
    const student = hrefs("student");
    const teacher = hrefs("teacher");
    expect(student).toEqual(["/home", "/me/stats"]);
    for (const href of student) expect(teacher).toContain(href);
    expect(teacher.length).toBeGreaterThan(student.length);
    expect(groupsFor("teacher").map((g) => g.label)).toContain("Học tập");
  });

  it("an org admin sees everything a teacher sees plus their own", () => {
    const teacher = hrefs("teacher");
    const admin = hrefs("org_admin");
    for (const href of teacher) expect(admin).toContain(href);
    // nesting goes one way only: what belongs to the org admin stays out of a teacher's menu
    expect(admin).toContain("/org/settings/ingestion");
    expect(admin).toContain("/org/ai-models");
    expect(teacher).not.toContain("/org/settings/ingestion");
    expect(teacher).not.toContain("/org/ai-models");
  });

  it("an item names only the lowest role that may see it", () => {
    for (const item of NAV_GROUPS.flatMap((g) => g.items)) {
      // the point of ADR-02: one rung of the chain (none at all for what only a platform admin may see),
      // so a new item never has to remember to list all three
      expect(item.roles.filter((r) => r !== "super_admin").length, item.href).toBeLessThanOrEqual(1);
    }
  });

  it("the platform admin is still granted apart from the chain", () => {
    expect(groupsFor("super_admin").map((g) => g.label)).toEqual(["Cài đặt", "Hệ thống"]);
    expect(hrefs("org_admin", true)).toContain("/admin/orgs");
    expect(hrefs("org_admin", false)).not.toContain("/admin/orgs");
  });

  it("where each role lands, and the deepest match, do not move", () => {
    expect(homeFor("student")).toBe("/home");
    expect(homeFor("teacher")).toBe("/org/review");
    expect(homeFor("org_admin")).toBe("/org/review");
    expect(homeFor("super_admin")).toBe("/admin/orgs");
    expect(activeItem("teacher", "/org/review/untagged")?.label).toBe("Chưa gắn chuyên đề");
    expect(activeItem("org_admin", "/me/stats")?.label).toBe("Tiến độ của tôi");
  });
});

describe("thứ tự nhóm Lớp & học sinh", () => {
  it("đi theo trình tự làm việc: năm học, cơ cấu, lớp, rồi người", () => {
    // AC-07. Lập lớp trước rồi mới xếp người vào, nên Lớp học đứng trước Người dùng.
    const group = groupsFor("org_admin").find((g) => g.label === "Lớp & học sinh");
    expect(group?.items.map((i) => i.label)).toEqual(["Năm học", "Cơ cấu trường", "Lớp học", "Người dùng"]);
  });
});
