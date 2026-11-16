import type { ReactNode } from "react";
import "./globals.css";
import sk from "@/locales/sk/common.json";

export const metadata = {
  title: sk.app.title,
  description: sk.app.title,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="sk">
      <body>{children}</body>
    </html>
  );
}
