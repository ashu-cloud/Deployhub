"use client";

import React, { useState } from "react";
import { SketchBoltIcon, SketchCheckIcon } from "./SketchIcons";

export function InteractiveRollbackDemo() {
  const [activeDeploy, setActiveDeploy] = useState<"v2" | "v1">("v2");
  const [isSwapping, setIsSwapping] = useState(false);

  const triggerSwap = (target: "v2" | "v1") => {
    if (target === activeDeploy || isSwapping) return;
    setIsSwapping(true);
    setTimeout(() => {
      setActiveDeploy(target);
      setIsSwapping(false);
    }, 280);
  };

  return (
    <div className="bg-surface-container p-6 md:p-8 doodle-border paper-shadow-lg relative my-16">
      <div className="washi-tape-1 bg-tertiary"></div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b-2 border-outline-variant/40 pb-6 mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-primary font-bold mb-1">
            <SketchBoltIcon className="w-4 h-4 text-tertiary" />
            <span>Interactive Sub-Second Rollback Demo</span>
          </div>
          <h3
            className="text-2xl md:text-3xl font-bold text-sketch-white font-serif"
            style={{ fontFamily: "var(--font-bricolage)" }}
          >
            Instant Atomic Rollbacks
          </h3>
          <p className="text-on-surface-variant text-sm mt-1">
            DeployHub swaps Caddy reverse proxy routes instantly without container rebuilding.
          </p>
        </div>

        {/* Live Active Status Pill */}
        <div className="bg-surface-dim px-4 py-2.5 rounded-lg doodle-border font-mono text-xs flex items-center gap-3 shrink-0">
          <span className="text-outline">Active Live Target:</span>
          <span className="px-2.5 py-0.5 rounded bg-primary/20 text-primary font-bold border border-primary/40 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse"></span>
            {activeDeploy === "v2" ? "v2.1.0 (Current)" : "v2.0.9 (Previous Stable)"}
          </span>
        </div>
      </div>

      {/* Deployment List Switcher */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        {/* Deployment 1 (v2.1.0) */}
        <div
          onClick={() => triggerSwap("v2")}
          className={`p-5 rounded-xl doodle-border cursor-pointer transition-all ${
            activeDeploy === "v2"
              ? "bg-surface-container-high border-primary paper-shadow-emerald"
              : "bg-surface hover:bg-surface-container-high border-outline-variant/50 opacity-70"
          }`}
        >
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sketch-white text-sm">Deployment #142</span>
              <span className="text-outline">commit c81f9a</span>
            </div>
            {activeDeploy === "v2" ? (
              <span className="px-2 py-0.5 bg-primary text-surface font-bold rounded text-[10px]">
                LIVE ROUTE
              </span>
            ) : (
              <span className="px-2 py-0.5 bg-surface-variant text-outline rounded text-[10px]">
                CLICK TO ROLLBACK
              </span>
            )}
          </div>
          <p className="text-on-surface-variant mb-3">
            fix(auth): update github oauth token refresh handler
          </p>
          <div className="flex justify-between text-[11px] text-outline pt-2 border-t border-outline-variant/30">
            <span>Branch: <strong>main</strong></span>
            <span>Built in: <strong>4.2s</strong></span>
          </div>
        </div>

        {/* Deployment 2 (v2.0.9) */}
        <div
          onClick={() => triggerSwap("v1")}
          className={`p-5 rounded-xl doodle-border cursor-pointer transition-all ${
            activeDeploy === "v1"
              ? "bg-surface-container-high border-primary paper-shadow-emerald"
              : "bg-surface hover:bg-surface-container-high border-outline-variant/50 opacity-70"
          }`}
        >
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sketch-white text-sm">Deployment #141</span>
              <span className="text-outline">commit a401bd</span>
            </div>
            {activeDeploy === "v1" ? (
              <span className="px-2 py-0.5 bg-primary text-surface font-bold rounded text-[10px]">
                LIVE ROUTE
              </span>
            ) : (
              <span className="px-2 py-0.5 bg-surface-variant text-outline rounded text-[10px]">
                CLICK TO ROLLBACK
              </span>
            )}
          </div>
          <p className="text-on-surface-variant mb-3">
            feat(dashboard): add dynamic real-time memory usage telemetry
          </p>
          <div className="flex justify-between text-[11px] text-outline pt-2 border-t border-outline-variant/30">
            <span>Branch: <strong>main</strong></span>
            <span>Built in: <strong>3.8s</strong></span>
          </div>
        </div>
      </div>

      {/* Rollback status ticker */}
      <div className="mt-6 bg-surface-dim p-3 rounded-lg border border-outline-variant/40 flex items-center justify-between font-mono text-xs text-on-surface-variant">
        <div className="flex items-center gap-2">
          {isSwapping ? (
            <>
              <span className="animate-spin text-tertiary">⚙</span>
              <span className="text-tertiary">Swapping Caddy Admin API route configuration...</span>
            </>
          ) : (
            <>
              <SketchCheckIcon className="w-4 h-4 text-primary" />
              <span>Caddy Upstream Subdomain synced in <strong className="text-primary">280ms</strong>. No downtime.</span>
            </>
          )}
        </div>
        <span className="text-outline hidden sm:inline">0 DNS Propagation Delay</span>
      </div>
    </div>
  );
}
