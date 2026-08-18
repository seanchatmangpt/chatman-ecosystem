import type { Metadata } from "next";
import "./globals.css";
import CommandPalette from "@/components/CommandPalette";

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
        {/* Global Search / Command Palette (Cmd+K / Ctrl+K) -- mounted once
            here, not per-page, so it is available from every route. Renders
            unauthenticated too (e.g. on /login) but stays inert there since
            GET /api/search 401s without a session; no page currently needs
            to suppress it. */}
        <CommandPalette />
      </body>
    </html>
  );
}
