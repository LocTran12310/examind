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

  it("removes a student after confirmation", async () => {
    const f = mockFetch(usersSearch([student("hs01", ["c1"])]), route("DELETE", "/api/classes/c1/members/hs01", undefined, 204));
    const u = userEvent.setup();
    render(<MemberManager classId="c1" />);
    await screen.findByText("HS01");
    await u.click(screen.getByRole("checkbox", { name: "Chọn dòng" }));
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(f.mock.calls.some(([url, init]) => url === "/api/classes/c1/members/hs01" && (init as RequestInit)?.method === "DELETE")).toBe(true));
  });
});

describe("thêm học sinh vào lớp", () => {
  /** `POST /users/search`: the roster of the class asked for, or the matches of a query. */
  const users =
    (byClass: Record<string, User[]>, found: User[] = [], total = found.length) =>
    (url: string, init?: RequestInit) => {
      if (url !== "/api/users/search" || init?.method !== "POST") return undefined;
      const body = JSON.parse(String(init.body));
      return { body: body.class_id ? searchPage(byClass[String(body.class_id)] ?? []) : searchPage(found, total) };
    };
  const classes = (...list: SchoolClass[]) => route("POST", "/api/classes/search", searchPage(list));
  const target = klass({ id: "c1", name: "12A99", school_year: "2027-2028", member_count: 0 });
  /** open the dialog and hand back its row input */
  const openDialog = async (u: ReturnType<typeof userEvent.setup>) => {
    render(<MemberManager classId="c1" />);
    await u.click(await screen.findByRole("button", { name: "Thêm học sinh" }));
    return await screen.findByRole("textbox", { name: "Tìm học sinh để thêm" });
  };
  const staged = () => screen.getByTestId("staged-students");
  const openPicker = (u: ReturnType<typeof userEvent.setup>) => u.click(screen.getByRole("button", { name: "Chọn học sinh từ lớp khác" }));

  it("gõ tên vào dòng nhập của bảng là đưa em ấy vào danh sách chờ", async () => {
    // the reported cost: filling a class meant hunting each em through a separate search box
    const f = mockFetch(classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })), users({ c1: [] }, [student("hs01", ["c0"])]));
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "h"); // one letter matches the whole school: nothing is searched yet
    expect(screen.queryByTestId("student-suggestions")).toBeNull();
    await u.type(box, "s");
    await waitFor(() => expect(lastBody(f, "/users/search")).toMatchObject({ q: "hs", filters: { role: { value: "student" } } }));
    await u.click(await screen.findByRole("button", { name: /HS01/ }));
    // the row now names the em, the account and the class he is in today
    expect(within(staged()).getByText("HS01")).toBeInTheDocument();
    expect(within(staged()).getByText("hs01")).toBeInTheDocument();
    expect(within(staged()).getByText("Lớp 11A1")).toBeInTheDocument();
    expect(box).toHaveValue(""); // a fresh input row, ready for the next name
    expect(screen.queryByTestId("student-suggestions")).toBeNull();
    expect(screen.getByRole("button", { name: "Thêm 1 học sinh" })).toBeEnabled();
    expect(f.mock.calls.filter((c) => c[0] === "/api/classes/c1/members")).toHaveLength(0); // staged, not saved
  });

  it("danh sách chờ còn nguyên khi mở hộp chọn, và hộp chọn thêm vào chứ không thay thế", async () => {
    mockFetch(classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })), users({ c1: [], c0: [student("hs02", ["c0"])] }, [student("hs01", ["c0"])]));
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "hs");
    await u.click(await screen.findByRole("button", { name: /HS01/ }));
    await openPicker(u);
    await u.click(await screen.findByRole("checkbox", { name: "Chọn lớp 11A1" }));
    await u.click(await screen.findByRole("button", { name: "Chọn 1 học sinh" }));
    // what was typed and what was ticked are the same kind of row, and both are still waiting
    await waitFor(() => expect(screen.getByRole("button", { name: "Thêm 2 học sinh" })).toBeEnabled());
    expect(within(staged()).getByText("HS01")).toBeInTheDocument();
    expect(within(staged()).getByText("HS02")).toBeInTheDocument();
  });

  it("hộp chọn tích hai lớp một lúc: cả hai vào danh sách chờ và chưa lưu gì", async () => {
    // the picker chooses; it does not save. The footer of the dialog underneath is the one request.
    const f = mockFetch(
      classes(target, klass({ id: "c0", name: "11A1" }), klass({ id: "c00", name: "11A2" })),
      users({ c1: [], c0: [student("hs01", ["c0"])], c00: [student("hs02", ["c00"])] }),
      route("POST", "/api/classes/c1/members", undefined, 204),
    );
    const u = userEvent.setup();
    await openDialog(u);
    await openPicker(u);
    await u.click(await screen.findByRole("checkbox", { name: "Chọn lớp 11A1" }));
    await u.click(screen.getByRole("checkbox", { name: "Chọn lớp 11A2" }));
    await u.click(await screen.findByRole("button", { name: "Chọn 2 học sinh" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Thêm 2 học sinh" })).toBeEnabled());
    expect(within(staged()).getByText("HS01")).toBeInTheDocument();
    expect(within(staged()).getByText("HS02")).toBeInTheDocument();
    expect(f.mock.calls.filter((c) => c[0] === "/api/classes/c1/members")).toHaveLength(0);
  });

  it("footer lưu mọi em đang chờ trong đúng một lời gọi mang mọi id (AC-08)", async () => {
    const f = mockFetch(
      classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })),
      users({ c1: [], c0: [student("hs02", ["c0"])] }, [student("hs01", ["c0"])]),
      route("POST", "/api/classes/c1/members", undefined, 204),
    );
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "hs");
    await u.click(await screen.findByRole("button", { name: /HS01/ }));
    await openPicker(u);
    await u.click(await screen.findByRole("checkbox", { name: "Chọn lớp 11A1" }));
    await u.click(await screen.findByRole("button", { name: "Chọn 1 học sinh" }));
    await u.click(await screen.findByRole("button", { name: "Thêm 2 học sinh" }));
    await waitFor(() => expect(lastBody(f, "/classes/c1/members")).toEqual({ user_ids: ["hs01", "hs02"] }));
    // one request for the whole list, not one per student, however many ways the rows arrived
    expect(f.mock.calls.filter((c) => c[0] === "/api/classes/c1/members")).toHaveLength(1);
  });

  it("em đã ở trong lớp thì không gõ vào danh sách được, cũng không tích được trong hộp chọn (AC-09, AC-10)", async () => {
    mockFetch(
      classes(target, klass({ id: "c0", name: "11A1", member_count: 2 })),
      users({ c1: [student("hs03", ["c0", "c1"])], c0: [student("hs01", ["c0"]), student("hs03", ["c0", "c1"])] }, [student("hs03", ["c0", "c1"])]),
    );
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "hs");
    // offered, so nobody concludes the em does not exist — but not takeable, and the row says why
    const hit = await screen.findByRole("button", { name: /HS03/ });
    expect(hit).toBeDisabled();
    expect(within(hit).getByText("đã ở trong lớp")).toBeInTheDocument();
    await u.clear(box);
    await openPicker(u);
    await u.click(await screen.findByRole("button", { name: "Xem học sinh lớp 11A1" }));
    await screen.findByText("đã ở trong lớp");
    expect(screen.getByRole("checkbox", { name: "Chọn HS03" })).toBeDisabled();
    // ticking the class takes the one em it can offer, not the member it cannot
    await u.click(screen.getByRole("checkbox", { name: "Chọn lớp 11A1" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Chọn 1 học sinh" })).toBeEnabled());
  });

  it("em đã trong danh sách chờ thì hộp chọn không cho chọn lại", async () => {
    mockFetch(classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })), users({ c1: [], c0: [student("hs01", ["c0"])] }, [student("hs01", ["c0"])]));
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "hs");
    await u.click(await screen.findByRole("button", { name: /HS01/ }));
    await openPicker(u);
    await u.click(await screen.findByRole("button", { name: "Xem học sinh lớp 11A1" }));
    expect(await screen.findByText("đã trong danh sách")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Chọn HS01" })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: "Chọn lớp 11A1" })).toBeDisabled(); // nothing left to offer
  });

  it("hủy hộp chọn thì không thêm gì vào danh sách chờ", async () => {
    const f = mockFetch(
      classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })),
      users({ c1: [], c0: [student("hs01", ["c0"])] }),
      route("POST", "/api/classes/c1/members", undefined, 204),
    );
    const u = userEvent.setup();
    await openDialog(u);
    await openPicker(u);
    await u.click(await screen.findByRole("checkbox", { name: "Chọn lớp 11A1" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Chọn 1 học sinh" })).toBeEnabled());
    await u.click(screen.getByRole("button", { name: "Hủy" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Tìm học sinh" })).toBeNull());
    expect(screen.getByRole("button", { name: "Thêm 0 học sinh" })).toBeDisabled();
    expect(within(staged()).queryByText("HS01")).toBeNull();
    expect(f.mock.calls.filter((c) => c[0] === "/api/classes/c1/members")).toHaveLength(0);
  });

  it("hộp chọn là hộp thoại riêng, và Escape chỉ đóng hộp trên", async () => {
    mockFetch(classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })), users({ c1: [], c0: [student("hs02", ["c0"])] }, [student("hs01", ["c0"])]));
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "hs");
    await u.click(await screen.findByRole("button", { name: /HS01/ }));
    await openPicker(u);
    // the picker is its own dialog: while it is on top the draft list underneath is out of reach
    const find = await screen.findByRole("textbox", { name: "Tìm học sinh" });
    expect(screen.queryByRole("textbox", { name: "Tìm học sinh để thêm" })).toBeNull();
    // one press is enough — nothing in the header opens a layer that eats the first Escape
    await u.click(find);
    await u.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Tìm học sinh" })).toBeNull());
    expect(screen.getByRole("dialog")).toHaveAccessibleName("Thêm học sinh vào lớp");
    expect(within(staged()).getByText("HS01")).toBeInTheDocument(); // the draft list came back as it was
  });

  it("lớp không còn em nào để thêm thì không tích được", async () => {
    mockFetch(classes(target, klass({ id: "c0", name: "11A1", member_count: 1 })), users({ c1: [student("hs01", ["c0", "c1"])], c0: [student("hs01", ["c0", "c1"])] }));
    const u = userEvent.setup();
    await openDialog(u);
    await openPicker(u);
    await u.click(await screen.findByRole("button", { name: "Xem học sinh lớp 11A1" }));
    await screen.findByText("đã ở trong lớp");
    expect(screen.getByRole("checkbox", { name: "Chọn lớp 11A1" })).toBeDisabled();
  });

  it("chỉ sang Chuyển năm học cho việc cả năm (AC-11)", async () => {
    // the whole-year move already existed and he never found it — which is why this dialog names it
    mockFetch(classes(target), users({ c1: [] }));
    const u = userEvent.setup();
    await openDialog(u);
    expect(await screen.findByRole("link", { name: /Chuyển năm học/ })).toHaveAttribute("href", "/org/school-years");
  });

  it("tìm trong hộp chọn: tích nhiều em một lúc, em đã ở trong lớp xuống cuối", async () => {
    // mở từ trong một lớp thì chính học sinh của lớp ấy khớp trước theo tên, và cả màn hình đầu là những dòng
    // "đã ở trong lớp" — thấy được trên ảnh chụp kiểm chứng, sửa bằng thứ tự chứ không bằng cách giấu chúng đi
    const f = mockFetch(classes(target), users({ c1: [] }, [student("hs01", ["c1"]), student("hs02"), student("hs03", ["c1"]), student("hs04")]));
    const u = userEvent.setup();
    await openDialog(u);
    await openPicker(u);
    await u.type(await screen.findByRole("textbox", { name: "Tìm học sinh" }), "hs");
    await waitFor(() => expect(lastBody(f, "/users/search")).toMatchObject({ q: "hs", filters: { role: { value: "student" } } }));
    const names = [...(await screen.findByTestId("found-students")).querySelectorAll("li")].map((li) => li.textContent?.trim().slice(0, 4));
    expect(names).toEqual(["HS02", "HS04", "HS01", "HS03"]);
    await u.click(screen.getByRole("checkbox", { name: "Chọn tất cả" }));
    await u.click(await screen.findByRole("button", { name: "Chọn 2 học sinh" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Thêm 2 học sinh" })).toBeEnabled());
  });

  it("nói ra khi còn kết quả ngoài danh sách đang xem", async () => {
    // một danh sách bị cắt mà không nói gì là cách một giáo viên kết luận rằng học sinh ấy không tồn tại
    mockFetch(classes(target), users({ c1: [] }, [student("hs01")], 51));
    const u = userEvent.setup();
    const box = await openDialog(u);
    await u.type(box, "hs");
    expect(await screen.findByText(/Còn 50 kết quả nữa/)).toBeInTheDocument();
    await u.clear(box);
    await openPicker(u);
    await u.type(await screen.findByRole("textbox", { name: "Tìm học sinh" }), "hs");
    expect(await screen.findByText(/Còn 50 kết quả nữa/)).toBeInTheDocument();
  });
});
