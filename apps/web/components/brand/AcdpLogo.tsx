import type { SVGProps } from "react";

interface LogoProps extends SVGProps<SVGSVGElement> {
  size?: number;
}

export function LogoMark({ size = 32, className, ...props }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="ACDP Logo Mark"
      className={className}
      {...props}
    >
      <rect x="2" y="2" width="28" height="28" rx="7" fill="#1E3A8A" />
      <rect x="7" y="18" width="4" height="6" rx="1.5" fill="#93C5FD" />
      <rect x="14" y="13" width="4" height="11" rx="1.5" fill="#FFFFFF" />
      <rect x="21" y="8" width="4" height="16" rx="1.5" fill="#C2410C" />
      <circle cx="23" cy="6.5" r="1.75" fill="#FBBF24" />
    </svg>
  );
}

export function LogoFull({ className = "h-9 w-auto" }: { className?: string }) {
  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      <LogoMark size={34} />
      <div className="flex flex-col leading-none">
        <span className="font-sans text-lg font-bold tracking-tight text-[var(--color-text-primary)]">
          ACDP<span className="text-[var(--color-brand-accent)]">.</span>
        </span>
        <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
          Cổng Cuộc thi · HCM-UTE
        </span>
      </div>
    </div>
  );
}

export function LogoMonochrome({ size = 28, className, ...props }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="ACDP Monochrome Logo"
      className={className}
      {...props}
    >
      <rect x="2.75" y="2.75" width="26.5" height="26.5" rx="6.25" stroke="currentColor" strokeWidth="1.5" />
      <rect x="7.5" y="18" width="3.75" height="6" rx="1.25" fill="currentColor" fillOpacity="0.45" />
      <rect x="14.125" y="13" width="3.75" height="11" rx="1.25" fill="currentColor" fillOpacity="0.75" />
      <rect x="20.75" y="8" width="3.75" height="16" rx="1.25" fill="currentColor" />
    </svg>
  );
}
