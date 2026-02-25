import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/shared/lib/providers";

export const metadata: Metadata = {
  title: {
    default: "Harmony",
    template: "%s | Harmony",
  },
  description:
    "Psychometric analytics platform for superyacht crew — matching, team harmony, and on-board performance.",
  keywords: ["yacht crew", "psychometric", "team analytics", "recruitment"],
  robots: { index: false, follow: false }, // private SaaS
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body className="bg-bg-primary text-text-primary antialiased min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
