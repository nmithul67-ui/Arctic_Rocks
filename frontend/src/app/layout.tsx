import "./globals.css";

export const metadata = {
  title: "GuardPay Console – AI Agent Financial Firewall",
  description: "Deterministic Policy, Escrow, and HITL Gateway for AI Agents",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#090d16] text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
