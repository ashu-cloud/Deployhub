"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DeployHubLogo } from "./SketchIcons";

const NAV_ITEMS = [
  { id: "demo", label: "Live Demo", href: "/#demo" },
  { id: "benchmarks", label: "Benchmarks", href: "/#benchmarks" },
  { id: "features", label: "Features", href: "/#features" },
  { id: "how-it-works", label: "How It Works", href: "/docs" },
  { id: "faq", label: "FAQ", href: "/#faq" },
];



export default function Navbar() {
  const [activeSection, setActiveSection] = useState<string>("demo");

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 140; // Offset for navbar height

      for (let i = NAV_ITEMS.length - 1; i >= 0; i--) {
        const item = NAV_ITEMS[i];
        const element = document.getElementById(item.id);
        if (element) {
          const top = element.offsetTop;
          if (scrollPosition >= top) {
            setActiveSection(item.id);
            return;
          }
        }
      }

      // Default to demo if at the top
      if (window.scrollY < 300) {
        setActiveSection("demo");
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll(); // Initial check on mount

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleNavClick = (id: string) => {
    setActiveSection(id);
  };

  return (
    <nav className="bg-surface/75 backdrop-blur-xl flex justify-between items-center w-full px-6 md:px-12 h-20 z-50 sticky top-0 border-b-2 border-outline-variant/30 transition-colors">
      <div className="flex items-center gap-8 animate-fade-up stagger-1">
        <Link href="/" className="flex items-center wiggle group">
          <DeployHubLogo className="h-10" />
        </Link>

        {/* Desktop Navigation Links with Zig-Zag Wavy Underline Highlight */}
        <div className="hidden lg:flex gap-2 items-center font-mono text-sm">
          {NAV_ITEMS.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <Link
                key={item.id}
                href={item.href}
                onClick={() => handleNavClick(item.id)}
                className={`px-3 py-1.5 transition-all duration-150 relative ${
                  isActive
                    ? "text-primary font-bold sketch-underline"
                    : "text-on-surface-variant hover:text-sketch-white"
                }`}
              >
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

      </div>

      <div className="flex items-center gap-4 animate-fade-up stagger-1">
        {/* GitHub Star button */}
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="hidden md:flex items-center gap-2 text-xs font-mono font-bold px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-sketch-white doodle-border transition-colors"
        >
          <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          <span>Star</span>
        </a>


        {/* Login CTA */}
        <Link
          href="/login"
          className="doodle-btn bg-background text-sketch-white font-bold text-sm px-4 py-2 hover:bg-surface-variant transition-colors paper-shadow"
        >
          Sign In
        </Link>

        {/* Primary Deploy App Button (Commented Out) */}
        {/* <Link
          href="/dashboard"
          className="bg-primary text-surface font-mono font-bold text-sm px-4 py-2 hover:bg-primary-fixed transition-transform transform -rotate-1 hover:rotate-0 doodle-border-emerald paper-shadow-emerald"
        >
          Deploy App ⚡
        </Link> */}
      </div>

    </nav>
  );
}
