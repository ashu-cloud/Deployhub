import type { Metadata } from "next";
import { Bricolage_Grotesque, Geist, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AuthSessionProvider } from "@/components/AuthSessionProvider";

const bricolage = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
});

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DeployHub - Structure that adapts to your thinking",
  description: "Deployments shouldn't be rigid. Build, ship, and iterate in a workspace that feels as natural as sketching on a whiteboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" data-scroll-behavior="smooth">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body
        className={`${geist.variable} ${bricolage.variable} ${jetbrainsMono.variable} antialiased bg-background text-on-surface paper-texture overflow-x-hidden min-h-screen flex flex-col relative`}
        style={{ fontFamily: "var(--font-geist)" }}
      >
        <AuthSessionProvider>{children}</AuthSessionProvider>
      </body>
    </html>
  );
}
