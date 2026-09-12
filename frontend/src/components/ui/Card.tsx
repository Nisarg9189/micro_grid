import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_10px_30px_rgba(15,23,42,0.04)] transition-all duration-300 hover:border-slate-300 hover:shadow-[0_16px_36px_rgba(15,23,42,0.07)] ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
