import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Platform Console",
  description: "Internal platform status console",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // This console has one visual theme (dark) -- `dark` is applied directly
  // rather than left to prefers-color-scheme, since shadcn/ui's CSS
  // variables (app/globals.css) are only meant to be read through the
  // `.dark` scope here.
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
