import React from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";

export interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="relative min-h-screen bg-[#F8FAFC] text-slate-900 selection:bg-[#F7931A] selection:text-white">
      {/* Ambient background illumination */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-[-8%] h-[420px] w-[420px] rounded-full bg-orange-200/20 blur-[130px]" />
        <div className="absolute right-[-10%] top-[15%] h-[440px] w-[440px] rounded-full bg-yellow-100/30 blur-[140px]" />
        <div
          className="absolute inset-0 opacity-40"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.07) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl space-y-8 px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
        <Header />

        <main className="space-y-8">
          {children}
        </main>

        <Footer />
      </div>
    </div>
  );
}
