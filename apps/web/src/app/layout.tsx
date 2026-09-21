import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import "katex/dist/katex.min.css";
import "./globals.css";

const font = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
  variable: "--font-be-vietnam",
});

export const metadata: Metadata = {
  title: "Examind",
  description: "Ngân hàng câu hỏi và đề ôn luyện",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body className={`${font.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}
