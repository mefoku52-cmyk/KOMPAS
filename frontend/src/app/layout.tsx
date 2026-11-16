import type { ReactNode } from "react";

export const metadata = {
  title: "KOMPAS",
  description: "KOMPAS",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="sk">
      <body>{children}</body>
    </html>
  );
}
