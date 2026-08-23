"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface DriftingDoodle {
  id: number;
  x: number;
  y: number;
  size: number;
  icon: string;
  speed: number;
  rotateSpeed: number;
  rotation: number;
  opacity: number;
}

export default function NotFound() {
  const [doodles, setDoodles] = useState<DriftingDoodle[]>([]);

  // Ambient Doodle Spawner
  useEffect(() => {
    const icons = ["⚡", "📦", "🚀", "🛠️", "🔒", "💡", "📡", "✨"];
    
    // Initial batch
    const initialBatch: DriftingDoodle[] = Array.from({ length: 5 }).map((_, i) => ({
      id: i + 1,
      x: 15 + i * 18,
      y: Math.random() * 80 + 10,
      size: Math.random() * 10 + 26,
      icon: icons[i % icons.length],
      speed: Math.random() * 0.6 + 0.4,
      rotateSpeed: (Math.random() - 0.5) * 1.5,
      rotation: Math.random() * 360,
      opacity: Math.random() * 0.4 + 0.6,
    }));
    setDoodles(initialBatch);

    const interval = setInterval(() => {
      setDoodles((prev) => {
        if (prev.length >= 8) return prev;
        const newDoodle: DriftingDoodle = {
          id: Date.now() + Math.random(),
          x: Math.random() * 80 + 10,
          y: -10,
          size: Math.random() * 12 + 24,
          icon: icons[Math.floor(Math.random() * icons.length)],
          speed: Math.random() * 0.7 + 0.5,
          rotateSpeed: (Math.random() - 0.5) * 2,
          rotation: 0,
          opacity: Math.random() * 0.4 + 0.6,
        };
        return [...prev, newDoodle];
      });
    }, 1200);

    return () => clearInterval(interval);
  }, []);

  // Smooth Drift Animation Loop
  useEffect(() => {
    const loop = setInterval(() => {
      setDoodles((prev) =>
        prev
          .map((d) => ({
            ...d,
            y: d.y + d.speed,
            rotation: d.rotation + d.rotateSpeed,
          }))
          .filter((d) => d.y < 115)
      );
    }, 30);

    return () => clearInterval(loop);
  }, []);

  return (
    <div className="bg-surface text-on-surface font-body-md min-h-screen dot-grid flex flex-col items-center justify-center p-6 md:p-16 overflow-x-hidden relative">
      {/* Decorative Doodles Background */}
      <div className="absolute top-10 left-10 text-primary opacity-30 transform -rotate-45 pointer-events-none">
        <svg fill="none" height="40" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" width="40">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
        </svg>
      </div>
      <div className="absolute bottom-20 right-20 text-tertiary-container opacity-30 transform rotate-15 pointer-events-none">
        <svg fill="none" height="60" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" width="60">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"></path>
        </svg>
      </div>

      <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 relative z-10 my-auto">
        {/* ========================================================================= */}
        {/* LEFT: EXACT STITCH HAND-DRAWN IMAGE & STICKY ANNOTATIONS */}
        {/* ========================================================================= */}
        <div className="relative flex flex-col items-center md:items-start justify-center rotate-[-1deg]">
          {/* Exact Stitch Illustration */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt="Hand-drawn 404 broken server"
            className="w-full max-w-md rounded-xl rough-border shadow-md opacity-90 transition-transform duration-300 hover:scale-[1.02]"
            src="/assets/404-broken-server.png"
            onError={(e) => {
              // Fallback to hosted Google CDN if local file fails
              (e.target as HTMLImageElement).src =
                "https://lh3.googleusercontent.com/aida-public/AB6AXuDBic720TGPbs_SWHlQXDP3u9h_xYri7lfwWyHaXOZyxLYedEJAT6xFd_EEjlUZMh7hqPYDAmdvxNLSyoDAD60T8IQX89FITn5DA9Xr1J4zINobKXCcdbsob4iMWv_OWCxfoHSJ5PjvOfAL0Klvcqx4Fh14gI3k-BmJriispuUemMPe3qsWI-ey8inZy-IIPv2ZMkpMZfIcr093htguMQyc-waMS1FWQVVQBardwrLego3KAIUUAVhD";
            }}
          />

          {/* Sticky Notes from Stitch Design */}
          <div className="absolute -top-8 -left-8 font-mono text-[12px] text-primary-container transform -rotate-12 bg-surface-container-high p-2 rough-border shadow-lg z-20">
            "Wait, this isn't where we parked the server..."
          </div>
          <div className="absolute -bottom-4 right-0 font-mono text-[12px] text-tertiary transform rotate-6 bg-surface-container p-3 rough-border shadow-md z-20 opacity-80">
            "Did we trip over a cable?"
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT: 404 HEADLINE & AMBIENT ANIMATED SKETCH CANVAS */}
        {/* ========================================================================= */}
        <div className="flex flex-col items-center md:items-start justify-center space-y-6 rotate-[1deg]">
          <div className="text-center md:text-left">
            <h1
              className="text-6xl md:text-7xl font-extrabold text-primary-container scribble-underline mb-4 font-serif tracking-tight"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              404
            </h1>
            <h2
              className="text-2xl md:text-3xl font-bold text-on-surface mb-2 font-serif"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Lost in the Sketchbook
            </h2>
            <p className="text-base text-on-surface-variant max-w-sm leading-relaxed">
              Looks like this route hasn&apos;t been deployed yet or got lost between draft sheets. Telemetry packets are drifting in the void while our builder stands by.
            </p>
          </div>

          {/* Animated Ambient Sketch Canvas */}
          <div className="w-full bg-surface-container-lowest p-4 rough-border shadow-md relative overflow-hidden h-[190px] select-none">
            {/* Status Pill Header */}
            <div className="absolute top-2.5 right-3 font-mono text-[11px] text-primary bg-surface-container-high/90 px-2.5 py-0.5 rough-border z-10 flex items-center gap-1.5 backdrop-blur-xs">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-primary"></span>
              </span>
              <span>Scanning Telemetry</span>
            </div>

            {/* Drifting Ambient Doodles */}
            {doodles.map((doodle) => (
              <div
                key={doodle.id}
                style={{
                  left: `${doodle.x}%`,
                  top: `${doodle.y}%`,
                  transform: `translate(-50%, -50%) rotate(${doodle.rotation}deg)`,
                  opacity: doodle.opacity,
                }}
                className="absolute select-none pointer-events-none text-2xl transition-transform duration-75 filter drop-shadow-[0_0_8px_rgba(78,222,163,0.15)]"
              >
                {doodle.icon}
              </div>
            ))}

            {/* Background Grid Pattern & Watermark */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none opacity-10">
              <div className="font-mono text-4xl text-outline tracking-widest">
                [ 4 0 4 ]
              </div>
              <div className="font-mono text-[10px] text-outline mt-1">
                -- SIGNAL LOST IN TRANSIT --
              </div>
            </div>
          </div>

          {/* Recovery Action */}
          <div className="relative mt-8">
            <div className="absolute -top-6 -right-12 font-mono text-xs text-primary transform rotate-12 opacity-80 pointer-events-none">
              back to safety -&gt;
            </div>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 bg-primary-container text-on-primary-container font-mono font-bold text-base py-3 px-6 rough-border hover:bg-primary-fixed hover:scale-[0.98] transition-all duration-200"
            >
              <span>⚡</span>
              <span>Return to Dashboard</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

