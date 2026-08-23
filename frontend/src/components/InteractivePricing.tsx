"use client";

import React, { useState } from "react";
import { SketchCheckIcon, SketchBoltIcon } from "./SketchIcons";

export function InteractivePricing() {
  const [isAnnual, setIsAnnual] = useState(true);

  return (
    <section id="pricing" className="w-full max-w-6xl mx-auto my-24 px-4 relative">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container border border-outline-variant/60 rounded-full font-mono text-xs text-tertiary mb-3">
          <SketchBoltIcon className="w-4 h-4 text-tertiary" />
          <span>Simple, Developer-First Pricing</span>
        </div>
        <h2
          className="text-4xl md:text-5xl font-bold text-sketch-white tracking-tight font-serif"
          style={{ fontFamily: "var(--font-bricolage)" }}
        >
          Predictable Pricing for <span className="text-primary sketch-underline">Builders</span>
        </h2>
        <p className="text-on-surface-variant font-body-md text-lg max-w-2xl mx-auto mt-4">
          Deploy unlimited personal projects free forever. Upgrade when you need team concurrency and dedicated cloud runners.
        </p>

        {/* Billing Cycle Switcher with Hand-drawn Doodle Badge */}
        <div className="inline-flex items-center gap-4 bg-surface-container p-2 rounded-full doodle-border mt-8 relative">
          <button
            onClick={() => setIsAnnual(false)}
            className={`font-mono text-xs px-4 py-1.5 rounded-full transition-all cursor-pointer ${
              !isAnnual ? "bg-primary text-surface font-bold" : "text-on-surface-variant hover:text-sketch-white"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setIsAnnual(true)}
            className={`font-mono text-xs px-4 py-1.5 rounded-full transition-all cursor-pointer ${
              isAnnual ? "bg-primary text-surface font-bold" : "text-on-surface-variant hover:text-sketch-white"
            }`}
          >
            Annual Billing
          </button>

          {/* Doodle discount sticker */}
          <div className="absolute -right-20 -top-6 bg-tertiary text-surface font-mono font-bold text-[11px] px-2.5 py-1 rounded-md transform rotate-6 doodle-border paper-shadow shadow-sm hidden sm:block">
            Save 20%! 🏷️
          </div>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Tier 1: Hobby */}
        <div className="bg-surface-container p-8 doodle-border paper-shadow flex flex-col justify-between relative transform -rotate-1 hover:rotate-0 transition-transform">
          <div>
            <span className="font-mono text-xs text-outline font-bold uppercase tracking-wider block mb-2">
              Hobbyist
            </span>
            <h3 className="text-3xl font-bold text-sketch-white mb-2 font-serif">
              Free Forever
            </h3>
            <div className="font-mono text-4xl font-extrabold text-sketch-white my-4">
              $0
              <span className="text-xs font-normal text-outline"> / month</span>
            </div>
            <p className="text-on-surface-variant text-sm mb-6">
              Ideal for personal projects, hackathons, and open source experiments.
            </p>

            <div className="space-y-3 font-mono text-xs border-t border-outline-variant/40 pt-6">
              {[
                "Unlimited public repositories",
                "3 concurrent builds",
                "Automatic SSL & custom domains",
                "Instant atomic rollbacks",
                "10GB MinIO artifact storage",
                "Community & GitHub Discussions support",
              ].map((feat, idx) => (
                <div key={idx} className="flex items-center gap-2.5 text-on-surface-variant">
                  <SketchCheckIcon className="w-4 h-4 text-primary shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>
          </div>

          <button className="mt-8 w-full doodle-btn bg-surface font-mono font-bold text-sm py-3 text-sketch-white hover:bg-surface-variant transition-colors paper-shadow">
            Start Free
          </button>
        </div>

        {/* Tier 2: Pro Hacker (Featured) */}
        <div className="bg-surface-container-high p-8 doodle-border-emerald paper-shadow-emerald flex flex-col justify-between relative transform md:-translate-y-4 md:rotate-1 hover:rotate-0 transition-transform">
          <div className="washi-tape-1 bg-primary"></div>
          <div className="absolute -top-3 right-6 bg-primary text-surface font-mono font-bold text-[10px] uppercase px-3 py-0.5 rounded-full">
            MOST POPULAR
          </div>

          <div>
            <span className="font-mono text-xs text-primary font-bold uppercase tracking-wider block mb-2">
              Pro Developer
            </span>
            <h3 className="text-3xl font-bold text-sketch-white mb-2 font-serif">
              Fast & Furious
            </h3>
            <div className="font-mono text-4xl font-extrabold text-primary my-4">
              ${isAnnual ? "15" : "19"}
              <span className="text-xs font-normal text-outline"> / month</span>
            </div>
            <p className="text-on-surface-variant text-sm mb-6">
              For indie hackers and growing applications needing fast isolated runners.
            </p>

            <div className="space-y-3 font-mono text-xs border-t border-outline-variant/40 pt-6">
              {[
                "Everything in Hobbyist",
                "12 concurrent high-speed builds",
                "Dedicated 4-core Docker runners",
                "AI Root-Cause Build Failure Diagnostics",
                "100GB MinIO artifact storage",
                "Encrypted environment variables vault",
                "Custom Slack & webhook alerts",
              ].map((feat, idx) => (
                <div key={idx} className="flex items-center gap-2.5 text-sketch-white">
                  <SketchCheckIcon className="w-4 h-4 text-primary shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>

          </div>

          <button className="mt-8 w-full bg-primary text-surface font-mono font-bold text-sm py-3 hover:bg-primary-fixed transition-colors doodle-border-emerald paper-shadow-emerald">
            Upgrade to Pro ⚡
          </button>
        </div>

        {/* Tier 3: Team Scale */}
        <div className="bg-surface-container p-8 doodle-border paper-shadow flex flex-col justify-between relative transform rotate-1 hover:rotate-0 transition-transform">
          <div>
            <span className="font-mono text-xs text-tertiary font-bold uppercase tracking-wider block mb-2">
              Team Scale
            </span>
            <h3 className="text-3xl font-bold text-sketch-white mb-2 font-serif">
              Enterprise Grade
            </h3>
            <div className="font-mono text-4xl font-extrabold text-sketch-white my-4">
              ${isAnnual ? "39" : "49"}
              <span className="text-xs font-normal text-outline"> / month</span>
            </div>
            <p className="text-on-surface-variant text-sm mb-6">
              For engineering teams running dozens of daily releases with strict SLAs.
            </p>

            <div className="space-y-3 font-mono text-xs border-t border-outline-variant/40 pt-6">
              {[
                "Everything in Pro",
                "Unlimited concurrent build pipelines",
                "Self-hosted runner integration",
                "Role-based access control (RBAC)",
                "Audit logs & compliance exports",
                "99.99% uptime SLA guarantee",
                "24/7 dedicated engineering support",
              ].map((feat, idx) => (
                <div key={idx} className="flex items-center gap-2.5 text-on-surface-variant">
                  <SketchCheckIcon className="w-4 h-4 text-tertiary shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>
          </div>

          <button className="mt-8 w-full doodle-btn bg-surface font-mono font-bold text-sm py-3 text-sketch-white hover:bg-surface-variant transition-colors paper-shadow">
            Contact Sales
          </button>
        </div>
      </div>
    </section>
  );
}
