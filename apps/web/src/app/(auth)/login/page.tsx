import { Card } from "@/components/ui";
import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="text-2xl font-semibold text-brand-700">Examind</div>
          <p className="text-sm text-gray-500">Ngân hàng câu hỏi và đề ôn luyện</p>
        </div>
        <Card>
          <LoginForm />
        </Card>
      </div>
    </main>
  );
}
