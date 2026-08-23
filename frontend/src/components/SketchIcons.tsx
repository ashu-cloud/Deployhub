import React from "react";

export function DeployHubLogo({ className = "h-8", showText = true }: { className?: string; showText?: boolean }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Hand-drawn Cloud / Container Rocket Icon */}
      <svg
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full aspect-square text-primary overflow-visible"
      >
        {/* Hand-drawn box background */}
        <rect
          x="4"
          y="6"
          width="40"
          height="36"
          rx="8"
          className="fill-surface stroke-outline-variant"
          strokeWidth="2.5"
          strokeDasharray="120"
          style={{ strokeLinejoin: "round" }}
        />
        {/* Sketchy accent shadow offset */}
        <path
          d="M7 43 L42 43 L45 39"
          className="stroke-primary"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Rocket / Arrow shooting up */}
        <path
          d="M24 12 L33 24 L27 24 L27 34 L21 34 L21 24 L15 24 Z"
          className="fill-primary stroke-sketch-white"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        {/* Mini flame / sparkle doodle */}
        <path
          d="M24 35 Q22 39 24 41 Q26 39 24 35"
          className="stroke-tertiary fill-tertiary"
          strokeWidth="1.5"
        />
        {/* Doodle stars around */}
        <circle cx="10" cy="14" r="1.5" className="fill-tertiary" />
        <circle cx="38" cy="16" r="1" className="fill-accent-blue" />
      </svg>
      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span
              className="text-2xl font-bold tracking-tight text-sketch-white font-serif"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Deploy<span className="text-primary italic">Hub</span>
            </span>
            <span className="text-[10px] px-1.5 py-0.5 font-mono font-bold bg-primary/20 text-primary border border-primary/40 rounded -rotate-2">
              v1.0
            </span>
          </div>
          <span className="text-[9px] uppercase tracking-widest text-outline -mt-1 font-mono">
            Autonomous Cloud
          </span>
        </div>
      )}
    </div>
  );
}

export function SketchRocket({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <path
        d="M16 3 C16 3 24 9 24 19 L20 22 L17 19 L15 19 L12 22 L8 19 C8 9 16 3 16 3 Z"
        className="fill-primary/20 stroke-primary"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <circle cx="16" cy="12" r="2.5" className="fill-sketch-white stroke-primary" strokeWidth="1.5" />
      <path d="M8 19 L4 23 L9 22" className="stroke-primary" strokeWidth="2" strokeLinecap="round" />
      <path d="M24 19 L28 23 L23 22" className="stroke-primary" strokeWidth="2" strokeLinecap="round" />
      <path d="M14 23 Q16 28 16 30 Q18 28 18 23" className="stroke-tertiary fill-tertiary" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function SketchTerminalIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <rect
        x="3"
        y="5"
        width="26"
        height="22"
        rx="4"
        className="fill-surface stroke-tertiary"
        strokeWidth="2"
      />
      <line x1="3" y1="11" x2="29" y2="11" className="stroke-outline-variant" strokeWidth="1.5" />
      <circle cx="7" cy="8" r="1" className="fill-error" />
      <circle cx="11" cy="8" r="1" className="fill-tertiary" />
      <circle cx="15" cy="8" r="1" className="fill-primary" />
      <path d="M7 16 L12 19 L7 22" className="stroke-primary" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="15" y1="22" x2="21" y2="22" className="stroke-sketch-white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function SketchUsersIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <circle cx="12" cy="11" r="4.5" className="fill-accent-blue/20 stroke-accent-blue" strokeWidth="2" />
      <path d="M5 24 C5 19 8 18 12 18 C16 18 19 19 19 24" className="stroke-accent-blue" strokeWidth="2" strokeLinecap="round" />
      <circle cx="21" cy="12" r="3.5" className="stroke-outline" strokeWidth="1.8" />
      <path d="M19 23 C19.5 20.5 21.5 19.5 24 19.5 C26.5 19.5 28 20.5 28 24" className="stroke-outline" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function SketchLockIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <rect x="6" y="13" width="20" height="15" rx="3" className="fill-tertiary/20 stroke-tertiary" strokeWidth="2" />
      <path d="M11 13 V9 C11 6.2 13.2 4 16 4 C18.8 4 21 6.2 21 9 V13" className="stroke-tertiary" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="20" r="2" className="fill-sketch-white" />
      <path d="M16 22 V24" className="stroke-surface" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function SketchGlobeIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <circle cx="16" cy="16" r="12" className="fill-primary/10 stroke-primary" strokeWidth="2" />
      <ellipse cx="16" cy="16" rx="6" ry="12" className="stroke-primary" strokeWidth="1.5" />
      <line x1="4" y1="16" x2="28" y2="16" className="stroke-primary" strokeWidth="1.5" />
    </svg>
  );
}

export function SketchDatabaseIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <ellipse cx="16" cy="8" rx="10" ry="4" className="fill-secondary/20 stroke-secondary" strokeWidth="2" />
      <path d="M6 8 V16 C6 18.2 10.5 20 16 20 C21.5 20 26 18.2 26 16 V8" className="stroke-secondary" strokeWidth="2" />
      <path d="M6 16 V24 C6 26.2 10.5 28 16 28 C21.5 28 26 26.2 26 24 V16" className="stroke-secondary" strokeWidth="2" />
    </svg>
  );
}

export function SketchBoltIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className}>
      <path
        d="M18 3 L6 17 L15 17 L13 29 L26 14 L17 14 Z"
        className="fill-tertiary stroke-tertiary"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SketchCheckIcon({ className = "w-5 h-5 text-primary" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className}>
      <path
        d="M4 12.5 L9 17.5 L20 6"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SketchSparkle({ className = "w-4 h-4 text-tertiary" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 0 Q12 12 0 12 Q12 12 12 24 Q12 12 24 12 Q12 12 12 0 Z" />
    </svg>
  );
}

export function SketchArrowCurved({ className = "w-16 h-16 text-tertiary" }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" className={className}>
      <path
        d="M15 80 Q 40 20, 85 30"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
      />
      <path
        d="M68 20 L86 31 L78 48"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
