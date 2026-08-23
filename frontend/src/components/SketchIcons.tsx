import React from "react";

export function DeployHubLogo({ className = "h-9", showText = true }: { className?: string; showText?: boolean }) {
  return (
    <div className={`inline-flex items-center select-none group cursor-pointer ${className}`}>
      <svg
        viewBox="0 0 354 84"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full w-auto overflow-visible transition-transform duration-200 group-hover:scale-105"
      >
        {/* Technical Blueprint Guide Lines */}
        <line x1="8" y1="2" x2="8" y2="82" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" opacity="0.35" />
        <line x1="2" y1="12" x2="352" y2="12" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" opacity="0.25" />
        <line x1="2" y1="72" x2="352" y2="72" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" opacity="0.25" />
        <line x1="202" y1="2" x2="202" y2="82" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" opacity="0.35" />
        <line x1="344" y1="2" x2="344" y2="82" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" opacity="0.35" />

        {/* Dimension Alignment Crosses */}
        <path d="M 8 6 L 8 18 M 2 12 L 14 12" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
        <path d="M 344 6 L 344 18 M 338 12 L 350 12" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />

        {/* LEFT PILL: DEPLOY (Filled Emerald) */}
        <g id="deploy-pill">
          {/* Shadow sketch */}
          <rect x="14" y="17" width="182" height="57" rx="14" fill="#022c22" opacity="0.4" />
          {/* Main filled pill */}
          <rect
            x="12"
            y="14"
            width="182"
            height="57"
            rx="14"
            fill="#059669"
            stroke="#10b981"
            strokeWidth="2.5"
            style={{ strokeLinejoin: "round" }}
          />
          {/* Organic sketch outline */}
          <path
            d="M 26 14 Q 100 13 180 14 Q 194 14 194 28 Q 194 57 194 57 Q 194 71 180 71 Q 100 72 26 71 Q 12 71 12 57 Q 12 28 12 28 Q 12 14 26 14 Z"
            stroke="#34d399"
            strokeWidth="1.2"
            fill="none"
            opacity="0.6"
          />
          {/* Corner cross-hatching */}
          <path d="M 168 16 L 192 40 M 176 16 L 194 34 M 184 16 L 194 26" stroke="#047857" strokeWidth="1.5" strokeLinecap="round" />

          {/* Inky Text "Deploy" */}
          <text
            x="103"
            y="54"
            textAnchor="middle"
            fill="#FFFFFF"
            fontFamily="'Bricolage Grotesque', 'Geist', sans-serif"
            fontWeight="800"
            fontSize="36"
            letterSpacing="-0.5px"
            style={{ filter: "drop-shadow(1px 2px 0px rgba(0,0,0,0.35))" }}
          >
            Deploy
          </text>
        </g>

        {/* RIGHT PILL: HUB (Sketched Double Outline) */}
        <g id="hub-pill">
          {/* Outer outline */}
          <rect
            x="204"
            y="14"
            width="134"
            height="57"
            rx="14"
            fill="transparent"
            stroke="#10b981"
            strokeWidth="2.5"
            style={{ strokeLinejoin: "round" }}
          />
          {/* Inner sketch outline */}
          <rect
            x="209"
            y="19"
            width="124"
            height="47"
            rx="10"
            fill="transparent"
            stroke="#34d399"
            strokeWidth="1.2"
            opacity="0.75"
          />
          {/* Corner hatch accent */}
          <path d="M 211 25 L 221 19 M 216 28 L 228 20" stroke="#10b981" strokeWidth="1.2" strokeLinecap="round" opacity="0.6" />

          {/* Inky Text "Hub" */}
          <text
            x="271"
            y="54"
            textAnchor="middle"
            fill="#FFFFFF"
            fontFamily="'Bricolage Grotesque', 'Geist', sans-serif"
            fontWeight="800"
            fontSize="36"
            letterSpacing="-0.5px"
            style={{ filter: "drop-shadow(1px 2px 0px rgba(0,0,0,0.45))" }}
          >
            Hub
          </text>
        </g>
      </svg>
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
