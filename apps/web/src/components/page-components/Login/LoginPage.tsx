import { ThemeToggle } from "@/components/layout/ThemeToggle/ThemeToggle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { APP_ICON } from "@/lib/common/nav";
import { LoginForm } from "./LoginForm/LoginForm";

export function LoginPage() {
  return (
    <main className="relative flex min-h-svh items-center justify-center bg-muted/40 p-4">
      <div className="absolute top-3 right-3">
        <ThemeToggle />
      </div>
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <APP_ICON className="size-5" />
          </div>
          <CardTitle className="text-xl">Examind</CardTitle>
          <CardDescription>Ngân hàng câu hỏi và đề ôn luyện</CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </main>
  );
}
