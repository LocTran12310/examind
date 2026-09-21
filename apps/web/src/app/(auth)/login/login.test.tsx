import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginForm, ORG_KEY } from "./LoginForm";

const me = { id: "1", username: "hs01", full_name: "HS", role: "student", must_change_password: false, org: { id: "o", code: "trungtama", name: "A" } };

describe("LoginForm", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("has org, username and password fields and prefills the last org", async () => {
    localStorage.setItem(ORG_KEY, "TrungtamA");
    render(<LoginForm onSuccess={() => {}} />);
    expect(screen.getByLabelText("Tên đăng nhập")).toBeInTheDocument();
    expect(screen.getByLabelText("Mật khẩu")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Tổ chức")).toHaveValue("TrungtamA"));
  });

  it("stores the org code after a successful login", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(me), { status: 200, headers: { "content-type": "application/json" } })));
    const onSuccess = vi.fn();
    render(<LoginForm onSuccess={onSuccess} />);
    await userEvent.type(screen.getByLabelText("Tổ chức"), "TrungtamA");
    await userEvent.type(screen.getByLabelText("Tên đăng nhập"), "hs01");
    await userEvent.type(screen.getByLabelText("Mật khẩu"), "secret");
    await userEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
    expect(localStorage.getItem(ORG_KEY)).toBe("TrungtamA");
  });

  it("shows the generic error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: { code: "invalid_credentials", message: "Sai tổ chức, tên đăng nhập hoặc mật khẩu" } }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    render(<LoginForm onSuccess={() => {}} />);
    await userEvent.type(screen.getByLabelText("Tổ chức"), "x");
    await userEvent.type(screen.getByLabelText("Tên đăng nhập"), "x");
    await userEvent.type(screen.getByLabelText("Mật khẩu"), "x");
    await userEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Sai tổ chức, tên đăng nhập hoặc mật khẩu");
  });
});
