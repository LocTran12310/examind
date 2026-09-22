import { CopyButton } from "@/components/app/CopyButton";

/** A temporary password shown once, with a copy button for the whole sign-in. */
export function TempPassword({ username, password, orgCode }: { username: string; password: string; orgCode: string }) {
  return (
    <div className="grid gap-2">
      <p className="text-sm">Mật khẩu tạm (chỉ hiển thị một lần, người dùng phải đổi khi đăng nhập):</p>
      <div className="flex items-center justify-between gap-2 rounded-md bg-muted p-3 font-mono text-sm">
        <span data-testid="temp-cred">
          {orgCode} / {username} / {password}
        </span>
        <CopyButton text={`Tổ chức: ${orgCode}\nTên đăng nhập: ${username}\nMật khẩu: ${password}`} />
      </div>
    </div>
  );
}
