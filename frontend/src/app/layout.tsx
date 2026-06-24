import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Document Search",
  description: "Semantic document embedding and search",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
