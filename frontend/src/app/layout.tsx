import "./globals.css";
import { ReactNode } from "react";

export const metadata = {
  title: "Paper Hedge Fund Simulator",
  description: "Educational paper-trading platform with local AI analysis and deterministic rules.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
