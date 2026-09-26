import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ClassesPage from "@/app/(app)/org/classes/page";
import { ClassForm } from "@/components/page-components/Classes/ClassForm/ClassForm";
import { MemberManager } from "@/components/page-components/Classes/MemberManager/MemberManager";
import { currentSchoolYear } from "@/lib/page-libs/classes/school-year";
import type { SchoolClass } from "@/interfaces/class.interface";
import type { User } from "@/interfaces/user.interface";
import { lastBody, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const student = (username: string, class_ids: string[] = []): User => ({
  id: username,
  username,
  full_name: username.toUpperCase(),
  email: null,
  role: "student",
  is_active: true,
  must_change_password: false,
  last_login_at: null,
  created_at: "",
  class_ids,
});
/** `POST /users/search`: the members of a class (`class_id`) or the student picker (`q`). */
const usersSearch = (members: User[], found: User[] = []) => (url: string, init?: RequestInit) => {
  if (url !== "/api/users/search" || init?.method !== "POST") return undefined;
  const body = JSON.parse(String(init.body));
  return { body: searchPage(body.class_id ? members : found) };
};
const klass = (o: Partial<SchoolClass> = {}): SchoolClass => ({ id: "c1", name: "10A1", grade: 10, school_year: "2026-2027", member_count: 1, created_at: "", ...o });

beforeEach(() => setUrl("/org/classes"));
afterEach(() => vi.unstubAllGlobals());

describe("classes", () => {
  it("school year rolls over in August", () => {
    expect(currentSchoolYear(new Date(2026, 8, 1))).toBe("2026-2027");
    expect(currentSchoolYear(new Date(2027, 2, 1))).toBe("2026-2027");
  });

  it("creates a class with a grade picked by level", async () => {
    const f = mockFetch(
      route("POST", "/api/classes", { id: "c" }, 201),
      route("POST", "/api/school-levels/search", searchPage([{ id: "thpt", code: "thpt", name: "Trung học phổ thông", grade_from: 10, grade_to: 12, sort: 1, grade_count: 1 }])),
      route("POST", "/api/grades/search", searchPage([{ id: "g10", level: 10, name: "Lớp 10", school_level_id: "thpt", class_count: 0 }])),
    );
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<ClassForm onDone={onDone} />);
    await u.type(screen.getByLabelText("Tên lớp"), "10A1");
    await u.click(screen.getByLabelText("Khối"));
    const listbox = await screen.findByRole("listbox");
    expect(within(listbox).getByText("Trung học phổ thông")).toBeInTheDocument();
    await u.click(within(listbox).getByRole("option", { name: "Lớp 10" }));
    await u.click(screen.getByRole("button", { name: "Tạo lớp" }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const post = f.mock.calls.find(([url, init]) => url === "/api/classes" && (init as RequestInit)?.method === "POST");
    expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ name: "10A1", grade_id: "g10" });
  });

  it("selecting a class shows its students in a detail table with its own URL params", async () => {
    const fetch = mockFetch(
      route("POST", "/api/classes/search", searchPage([klass(), klass({ id: "c2", name: "11B", grade: 11 })])),
      usersSearch([student("hs01", ["c1"])]),
    );
    const u = userEvent.setup();
    render(<ClassesPage />);
    await u.click(await screen.findByText("10A1"));
    expect(await screen.findByText("HS01")).toBeInTheDocument();
    expect(lastBody(fetch, "/users/search").class_id).toBe("c1");
    // jsdom has no layout, so the resize handle's hit-test claims every pointer down; set the value directly
    fireEvent.change(screen.getAllByRole("textbox", { name: "Lọc Họ tên" })[0], { target: { value: "an" } });
    await waitFor(() => expect(searchOf().get("m.full_name")).toBe("an"), { timeout: 1500 });
    await waitFor(() => expect(lastBody(fetch, "/users/search").filters).toEqual({ full_name: { value: "an" } }));
    expect(lastBody(fetch, "/classes/search").filters).toBeUndefined(); // the member filter stays on the member table
  });

  it("adds a student and removes one after confirmation", async () => {
    const f = mockFetch(
      usersSearch([student("hs01", ["c1"])], [student("hs01", ["c1"]), student("hs02")]),
      route("POST", "/api/classes/c1/members", undefined, 204),
      route("DELETE", "/api/classes/c1/members/hs01", undefined, 204),
    );
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await screen.findByText("HS01");
    await u.click(screen.getByRole("button", { name: "Thêm học sinh" }));
    await u.click(await screen.findByRole("tab", { name: "Tìm từng em" }));
    await u.type(screen.getByRole("textbox", { name: "Tìm học sinh" }), "hs");
    const dialog = await screen.findByRole("dialog");
    await u.click(await within(dialog).findByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(f.mock.calls.some((c) => c[0] === "/api/classes/c1/members")).toBe(true));
    await waitFor(() => expect(within(dialog).queryByRole("button", { name: "Thêm" })).toBeNull()); // hs02 leaves the list once added
    expect(lastBody(f, "/users/search")).toMatchObject({ q: "hs", filters: { role: { value: "student" } } });
    expect(JSON.parse(String(f.mock.calls.find((c) => c[0] === "/api/classes/c1/members")?.[1]?.body)).user_ids).toEqual(["hs02"]);
    await u.keyboard("{Escape}");
    await u.click(screen.getByRole("checkbox", { name: "Chọn dòng" }));
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(f.mock.calls.some(([url, init]) => url === "/api/classes/c1/members/hs01" && (init as RequestInit)?.method === "DELETE")).toBe(true));
  });
});

describe("thêm cả một lớp cũ", () => {
  /** `POST /users/search` keyed by the class asked for, so the source class and the target class differ */
  const rosters = (byClass: Record<string, User[]>) => (url: string, init?: RequestInit) => {
    if (url !== "/api/users/search" || init?.method !== "POST") return undefined;
    const body = JSON.parse(String(init.body));
    return { body: searchPage(byClass[String(body.class_id)] ?? []) };
  };

  it("chọn một lớp cũ rồi thêm cả lớp trong một lời gọi (AC-08)", async () => {
    // the reported cost: filling a 25-student class meant 25 searches and 25 clicks
    const f = mockFetch(
      route("POST", "/api/classes/search", searchPage([klass({ id: "c1", name: "12A99", school_year: "2027-2028", member_count: 0 }), klass({ id: "c0", name: "11A1", member_count: 2 })])),
      rosters({ c1: [], c0: [student("hs01", ["c0"]), student("hs02", ["c0"])] }),
      route("POST", "/api/classes/c1/members", undefined, 204),
    );
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    // the old classes are on screen with their year and size, not behind a search box
    const list = await screen.findByTestId("source-classes");
    expect(within(list).getByText(/11A1/)).toBeInTheDocument();
    expect(within(list).queryByText(/12A99/)).toBeNull(); // the class being filled is not a source for itself
    await u.click(within(list).getByRole("button", { name: /11A1/ }));
    // everyone is ticked to begin with: "chọn toàn lớp" is the case, not the exception
    await waitFor(() => expect(screen.getByRole("button", { name: "Thêm 2 học sinh" })).toBeEnabled());
    await u.click(screen.getByRole("button", { name: "Thêm 2 học sinh" }));
    await waitFor(() => expect(lastBody(f, "/classes/c1/members")).toEqual({ user_ids: ["hs01", "hs02"] }));
    // one request for the whole class, not one per student
    expect(f.mock.calls.filter((c) => c[0] === "/api/classes/c1/members")).toHaveLength(1);
  });

  it("bỏ tích được từng em, và em đã ở trong lớp thì không tích lại được (AC-09, AC-10)", async () => {
    const f = mockFetch(
      route("POST", "/api/classes/search", searchPage([klass({ id: "c1" }), klass({ id: "c0", name: "11A1" })])),
      rosters({ c1: [student("hs03", ["c0", "c1"])], c0: [student("hs01", ["c0"]), student("hs02", ["c0"]), student("hs03", ["c0", "c1"])] }),
      route("POST", "/api/classes/c1/members", undefined, 204),
    );
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    await u.click(await within(await screen.findByTestId("source-classes")).findByRole("button", { name: /11A1/ }));
    // hs03 is already a member: it is not counted in, and its box cannot be ticked
    await waitFor(() => expect(screen.getByRole("button", { name: "Thêm 2 học sinh" })).toBeEnabled());
    expect(screen.getByRole("checkbox", { name: "Chọn HS03" })).toBeDisabled();
    await u.click(screen.getByRole("checkbox", { name: "Chọn HS02" }));
    await u.click(screen.getByRole("button", { name: "Thêm 1 học sinh" }));
    await waitFor(() => expect(lastBody(f, "/classes/c1/members")).toEqual({ user_ids: ["hs01"] }));
  });

  it("chỉ sang Chuyển năm học cho việc cả năm (AC-11)", async () => {
    // the whole-year move already existed and he never found it — which is why this dialog names it
    mockFetch(route("POST", "/api/classes/search", searchPage([klass({ id: "c1" })])), rosters({}));
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    expect(await screen.findByRole("link", { name: /Chuyển năm học/ })).toHaveAttribute("href", "/org/school-years");
  });
});

describe("tìm nâng cao khi thêm học sinh", () => {
  const found = (users: User[], total = users.length) => (url: string, init?: RequestInit) => {
    if (url !== "/api/users/search" || init?.method !== "POST") return undefined;
    const body = JSON.parse(String(init.body));
    return { body: body.class_id === "c1" ? searchPage([]) : searchPage(users, total) };
  };

  it("nút kính lúp mở bảng tìm rộng: lọc theo lớp, tích nhiều em, thêm một lần", async () => {
    // ô tìm cũ chỉ thêm được từng em một, và không nói được "những em chưa có lớp nào"
    const f = mockFetch(
      route("POST", "/api/classes/search", searchPage([klass({ id: "c1" }), klass({ id: "c0", name: "11A1" })])),
      found([student("hs01"), student("hs02")]),
      route("POST", "/api/classes/c1/members", undefined, 204),
    );
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    await u.click(await screen.findByRole("tab", { name: "Tìm từng em" }));
    await u.click(screen.getByRole("button", { name: "Tìm nâng cao" }));
    await u.click(await screen.findByRole("checkbox", { name: "Chọn tất cả" }));
    await u.click(screen.getByRole("button", { name: "Thêm 2 học sinh" }));
    await waitFor(() => expect(lastBody(f, "/classes/c1/members")).toEqual({ user_ids: ["hs01", "hs02"] }));
    expect(f.mock.calls.filter((c) => c[0] === "/api/classes/c1/members")).toHaveLength(1);
  });

  it("em đã ở trong lớp xuống cuối, để màn hình đầu tiên không toàn ô không tích được", async () => {
    // mở từ trong một lớp thì chính học sinh của lớp ấy khớp trước theo tên, và cả màn hình đầu là những dòng
    // "đã ở trong lớp" — thấy được trên ảnh chụp kiểm chứng, sửa bằng thứ tự chứ không bằng cách giấu chúng đi
    mockFetch(
      route("POST", "/api/classes/search", searchPage([klass({ id: "c1" })])),
      found([student("hs01", ["c1"]), student("hs02"), student("hs03", ["c1"]), student("hs04")]),
    );
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    await u.click(await screen.findByRole("tab", { name: "Tìm từng em" }));
    await u.click(screen.getByRole("button", { name: "Tìm nâng cao" }));
    const names = [...(await screen.findByTestId("wide-results")).querySelectorAll("li")].map((li) => li.textContent?.trim().slice(0, 4));
    expect(names).toEqual(["HS02", "HS04", "HS01", "HS03"]);
  });

  it("nói ra khi còn kết quả ngoài trang đang xem", async () => {
    // một danh sách bị cắt mà không nói gì là cách một giáo viên kết luận rằng học sinh ấy không tồn tại
    mockFetch(route("POST", "/api/classes/search", searchPage([klass({ id: "c1" })])), found([student("hs01")], 51));
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    await u.click(await screen.findByRole("tab", { name: "Tìm từng em" }));
    await u.click(screen.getByRole("button", { name: "Tìm nâng cao" }));
    expect(await screen.findByText(/Còn 50 kết quả nữa/)).toBeInTheDocument();
  });
});
