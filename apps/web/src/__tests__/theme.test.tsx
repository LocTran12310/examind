import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { ThemeProvider } from "@/components/layout/ThemeProvider/ThemeProvider";
import { ThemeToggle } from "@/components/layout/ThemeToggle/ThemeToggle";

describe("theme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
  });

  it("switches to dark and remembers the choice", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Giao diện" }));
    await user.click(await screen.findByRole("menuitemradio", { name: "Tối" }));
    await waitFor(() => expect(document.documentElement).toHaveClass("dark"));
    expect(localStorage.getItem("theme")).toBe("dark");
  });

  it("offers light, dark and system", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Giao diện" }));
    const items = await screen.findAllByRole("menuitemradio");
    expect(items.map((i) => i.textContent?.trim())).toEqual(["Sáng", "Tối", "Hệ thống"]);
  });
});
