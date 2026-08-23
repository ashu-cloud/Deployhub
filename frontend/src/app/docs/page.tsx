"use client";

import React, { useState } from "react";
import Link from "next/link";
import { DeployHubLogo } from "@/components/SketchIcons";

interface PipelineStep {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  icon: string;
  badge?: string;
  details: {
    description: string;
    command?: string;
    tech: string;
    metrics: string;
    codeSnippet?: string;
  };
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "local",
    number: 1,
    title: "Local Code",
    subtitle: "Developer Workspace",
    icon: "terminal",
    details: {
      description: "You work in your favorite editor (Next.js, Vite, React, Astro, or Python). Initialize your project with the DeployHub CLI or connect via the web dashboard.",
      command: "$ dh init my-awesome-app",
      tech: "Git & DeployHub CLI (dh)",
      metrics: "< 1s initialization",
      codeSnippet: `# Initialize project configuration
$ dh init my-awesome-app
✓ Detected Next.js (App Router)
✓ Generated dh.yaml blueprint
✓ Linked to DeployHub workspace`,
    },
  },
  {
    id: "push",
    number: 2,
    title: "GitHub Push",
    subtitle: "Git Ref Emitted",
    icon: "cloud_upload",
    details: {
      description: "Pushing any commit to your monitored branch (e.g., main or staging) triggers GitHub's webhook events with full commit metadata and SHA signature.",
      command: "$ git push origin main",
      tech: "GitHub Webhooks v3 / OAuth",
      metrics: "~120ms payload delivery",
      codeSnippet: `# Git push triggers automated build
$ git add . && git commit -m "feat: new dashboard"
$ git push origin main
→ GitHub webhook dispatched to https://api.deployhub.dev/api/v1/webhooks/github`,
    },
  },
  {
    id: "hook",
    number: 3,
    title: "DeployHub Hook",
    subtitle: "Kafka Event Bus",
    icon: "webhook",
    badge: "We catch the webhook here!",
    details: {
      description: "DeployHub's stateless gateway receives the webhook, verifies the HMAC-SHA256 signature, acquires a Redis distributed lock, and publishes a build.queued event to Kafka partition 0.",
      command: "POST /api/v1/webhooks/github",
      tech: "FastAPI + Apache Kafka + Redis Lock",
      metrics: "< 15ms queue latency",
      codeSnippet: `// Kafka Event Payload (deployments.v1 topic)
{
  "event": "build.queued",
  "project_id": "deployhub-web",
  "deployment_id": "dep-v142",
  "git_commit": "a9f8b4c",
  "git_branch": "main",
  "timestamp": "2026-08-23T17:53:01Z"
}`,
    },
  },
  {
    id: "pipeline",
    number: 4,
    title: "Pipeline Runner",
    subtitle: "Docker & MinIO S3",
    icon: "account_tree",
    details: {
      description: "An isolated Docker builder container is spawned with strict cgroups. It clones your ref, executes optimized pnpm/npm builds, generates immutable static chunks, and streams the tarball bundle to MinIO S3 storage.",
      command: "docker run --cpus 2 --memory 4g ...",
      tech: "Docker Container + MinIO S3 Bucket",
      metrics: "3.2s optimized build",
      codeSnippet: `# Runner build execution log
[DOCKER] Spawning isolated runner container (2 CPU, 4GB RAM)
[GIT] Cloned ref 'main' (commit: a9f8b4c) in 1.4s
[BUILD] pnpm install && pnpm build (Next.js 16 compiler)
[UPLOAD] Streaming 48 chunks (14.2 MB) to MinIO bucket 'deployhub-artifacts'`,
    },
  },
  {
    id: "live",
    number: 5,
    title: "Live URL",
    subtitle: "Caddy Dynamic Proxy",
    icon: "language",
    details: {
      description: "Once assets are stored in MinIO, Caddy's dynamic JSON Admin API updates reverse proxy routing tables in memory. Subdomain traffic goes live instantly with automated SSL.",
      command: "POST http://caddy:2019/load",
      tech: "Caddy Server v2 Dynamic Admin API",
      metrics: "< 290ms atomic traffic shift",
      codeSnippet: `# Caddy Admin API route update payload
POST http://127.0.0.1:2019/load
{
  "match": [{ "host": ["deployhub-web.deployhub.dev"] }],
  "handle": [{ "handler": "reverse_proxy", "upstreams": [{ "dial": "minio:9000/artifacts/v142" }] }]
}
✓ Status: 200 OK — Atomic switch completed in 18ms`,
    },
  },
];

export default function DocsPage() {
  const [selectedStep, setSelectedStep] = useState<PipelineStep>(PIPELINE_STEPS[2]); // Default to hook step
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [activeSidebar, setActiveSidebar] = useState<string>("flow");
  const [searchQuery, setSearchQuery] = useState("");
  const [checklist, setChecklist] = useState({
    yaml: true,
    repo: true,
    env: true,
    output: false,
  });

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(id);
    setTimeout(() => setCopiedText(null), 2500);
  };

  const toggleChecklist = (key: keyof typeof checklist) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen dot-grid selection:bg-primary-container selection:text-on-primary-container">
      {/* ========================================================================= */}
      {/* TOP NAVIGATION BAR */}
      {/* ========================================================================= */}
      <nav className="bg-surface/85 backdrop-blur-xl w-full top-0 sticky border-b-2 border-outline-variant/30 flex justify-between items-center px-6 md:px-12 py-3.5 z-50 transition-colors">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center group wiggle">
            <DeployHubLogo className="h-9" />
          </Link>
        </div>

        {/* Center Links */}
        <div className="hidden md:flex gap-8 items-center font-mono text-sm">
          <Link
            href="/docs"
            className="text-primary font-bold border-b-2 border-primary pb-0.5 tracking-wide"
          >
            Docs
          </Link>
          <Link
            href="/#features"
            className="text-on-surface-variant hover:text-sketch-white transition-colors"
          >
            Features
          </Link>
          <Link
            href="/#architecture"
            className="text-on-surface-variant hover:text-sketch-white transition-colors"
          >
            Architecture
          </Link>
          <Link
            href="/#faq"
            className="text-on-surface-variant hover:text-sketch-white transition-colors"
          >
            FAQ
          </Link>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
          {/* Quick Search */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-surface-container-low doodle-border text-xs font-mono text-on-surface-variant">
            <span className="text-primary">🔍</span>
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none outline-hidden text-sketch-white text-xs w-28 md:w-36 placeholder:text-outline"
            />
            <kbd className="hidden lg:inline-block px-1.5 py-0.5 bg-surface-container-high text-[10px] text-outline rounded border border-outline-variant/50">
              ⌘K
            </kbd>
          </div>

          <Link
            href="/dashboard"
            className="bg-primary text-surface font-mono font-bold text-xs md:text-sm px-4 py-2 hover:bg-primary-fixed transition-transform transform -rotate-1 hover:rotate-0 doodle-border-emerald paper-shadow-emerald"
          >
            Open Dashboard ⚡
          </Link>
        </div>
      </nav>

      {/* ========================================================================= */}
      {/* MAIN LAYOUT: SIDEBAR + CONTENT CANVAS */}
      {/* ========================================================================= */}
      <div className="flex max-w-[1600px] mx-auto min-h-[calc(100vh-68px)]">
        {/* ========================================================================= */}
        {/* LEFT STICKY SIDEBAR */}
        {/* ========================================================================= */}
        <aside className="hidden md:flex flex-col gap-2 py-8 overflow-y-auto bg-surface-container-low h-[calc(100vh-68px)] sticky top-[68px] w-64 border-r-2 border-outline-variant/30 shrink-0 select-none">
          <div className="px-6 pb-4 border-b border-outline-variant/30">
            <h2 className="font-serif text-primary text-lg font-bold tracking-tight">
              Documentation
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-outline font-mono">Doodle Edition</span>
            </div>
          </div>


          <nav className="flex-1 space-y-1 px-3 pt-4 font-mono text-xs">
            <a
              href="#flow"
              onClick={() => setActiveSidebar("flow")}
              className={`flex items-center gap-3 py-2.5 px-3 rounded transition-all ${
                activeSidebar === "flow"
                  ? "text-primary font-bold bg-surface-container-high border-l-4 border-primary shadow-xs"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-sketch-white"
              }`}
            >
              <span>🗺️</span>
              <span>The Pipeline Map</span>
            </a>

            <a
              href="#step-1"
              onClick={() => setActiveSidebar("step-1")}
              className={`flex items-center gap-3 py-2.5 px-3 rounded transition-all ${
                activeSidebar === "step-1"
                  ? "text-primary font-bold bg-surface-container-high border-l-4 border-primary shadow-xs"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-sketch-white"
              }`}
            >
              <span>⚡</span>
              <span>1. Initialize Project</span>
            </a>

            <a
              href="#step-2"
              onClick={() => setActiveSidebar("step-2")}
              className={`flex items-center gap-3 py-2.5 px-3 rounded transition-all ${
                activeSidebar === "step-2"
                  ? "text-primary font-bold bg-surface-container-high border-l-4 border-primary shadow-xs"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-sketch-white"
              }`}
            >
              <span>📦</span>
              <span>2. Build &amp; Deploy</span>
            </a>

            <a
              href="#step-3"
              onClick={() => setActiveSidebar("step-3")}
              className={`flex items-center gap-3 py-2.5 px-3 rounded transition-all ${
                activeSidebar === "step-3"
                  ? "text-primary font-bold bg-surface-container-high border-l-4 border-primary shadow-xs"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-sketch-white"
              }`}
            >
              <span>⏱️</span>
              <span>3. Atomic Rollbacks</span>
            </a>

            <a
              href="#step-4"
              onClick={() => setActiveSidebar("step-4")}
              className={`flex items-center gap-3 py-2.5 px-3 rounded transition-all ${
                activeSidebar === "step-4"
                  ? "text-primary font-bold bg-surface-container-high border-l-4 border-primary shadow-xs"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-sketch-white"
              }`}
            >
              <span>🛡️</span>
              <span>4. Secrets &amp; Routing</span>
            </a>
          </nav>

          {/* Quick API Button */}
          <div className="px-4 py-3">
            <Link
              href="/dashboard"
              className="w-full doodle-btn bg-surface-container-high hover:bg-surface-bright text-sketch-white py-2 px-3 font-mono text-xs flex items-center justify-center gap-2 paper-shadow text-center"
            >
              <span>⚡</span> View Live Workspace
            </Link>
          </div>

          {/* Sidebar Footer */}
          <div className="mt-auto border-t-2 border-outline-variant/30 pt-4 px-4 space-y-1 font-mono text-xs text-outline">
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 py-1 px-2 hover:text-primary transition-colors"
            >
              <span>⭐</span> GitHub Repository
            </a>
            <Link
              href="/#faq"
              className="flex items-center gap-2 py-1 px-2 hover:text-primary transition-colors"
            >
              <span>💡</span> Community FAQ
            </Link>
          </div>
        </aside>

        {/* ========================================================================= */}
        {/* MAIN DOCUMENTATION CONTENT */}
        {/* ========================================================================= */}
        <main className="flex-1 px-4 md:px-12 py-10 relative overflow-hidden">
          {/* Header Banner */}
          <header className="mb-14 relative">
            <div className="inline-flex items-center gap-2 mb-4">
              <span className="bg-tertiary text-surface font-mono font-bold text-xs px-3.5 py-1.5 doodle-border paper-shadow transform -rotate-1 tracking-wider uppercase inline-block shadow-sm">
                📌 Core Concepts &amp; Architecture
              </span>
            </div>


            <h1
              className="text-4xl md:text-6xl font-extrabold text-primary mb-4 font-serif tracking-tight leading-tight"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Mastering the Flow: <br />
              <span className="text-sketch-white">From Code to Cloud</span>
            </h1>

            <p className="text-base md:text-lg text-on-surface-variant max-w-3xl leading-relaxed">
              Understanding the deployment pipeline isn&apos;t just about reading logs—it&apos;s about seeing the big picture. Let&apos;s trace how your code journeys from a local git commit to a globally routed, sub-second atomic deployment.
            </p>

            {/* Hand-drawn curly SVG Arrow Annotation */}
            <div className="hidden lg:block absolute right-8 top-4 text-primary opacity-60 pointer-events-none">
              <svg width="90" height="90" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M20 20 Q 70 20 70 70 M 55 60 L 70 75 L 85 60" />
              </svg>
              <span className="absolute -bottom-2 -left-12 font-mono text-[11px] text-tertiary transform rotate-6">
                Interactive map below ⚡
              </span>
            </div>
          </header>

          {/* ========================================================================= */}
          {/* INTERACTIVE FLOW DIAGRAM (THE PIPELINE MAP) */}
          {/* ========================================================================= */}
          <section id="flow" className="mb-20 relative z-10 scroll-mt-24">
            <div className="bg-surface-container-high/60 backdrop-blur-md doodle-border p-6 md:p-8 relative paper-shadow-lg">
              {/* Corner Pin Accent Dots */}
              <div className="absolute -top-2.5 -left-2.5 w-5 h-5 bg-secondary rounded-full border-2 border-sketch-white z-20"></div>
              <div className="absolute -bottom-2.5 -right-2.5 w-5 h-5 bg-primary rounded-full border-2 border-sketch-white z-20"></div>

              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-8 border-b-2 border-outline-variant/30 pb-3">
                <div>
                  <h3
                    className="font-serif text-2xl md:text-3xl font-bold text-sketch-white flex items-center gap-2.5"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    <span>The Pipeline Map</span>
                    <span className="text-xs font-mono font-normal text-primary px-2 py-0.5 bg-primary/10 border border-primary/30 rounded">
                      Interactive Visualizer
                    </span>
                  </h3>
                  <p className="text-xs font-mono text-on-surface-variant mt-1">
                    Click any node to inspect telemetry, queue events, and infrastructure stages.
                  </p>
                </div>
              </div>

              {/* 5-Step Pipeline Flow Strip */}
              <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-2 relative py-4">
                {/* Horizontal Dashed Connection Line */}
                <div className="hidden md:block absolute top-1/2 left-8 right-8 h-0.5 border-t-2 border-dashed border-outline-variant/60 -z-1 transform -translate-y-1/2"></div>

                {PIPELINE_STEPS.map((step, idx) => {
                  const isSelected = selectedStep.id === step.id;
                  return (
                    <React.Fragment key={step.id}>
                      <div
                        onClick={() => setSelectedStep(step)}
                        className="flex flex-col items-center group cursor-pointer relative z-10"
                      >
                        {/* Step Number Tag */}
                        <span className="font-mono text-[10px] text-outline mb-1 font-bold">
                          STEP 0{step.number}
                        </span>

                        {/* Node Card */}
                        <div
                          className={`w-20 h-20 md:w-22 md:h-22 doodle-border flex flex-col items-center justify-center transition-all duration-200 relative ${
                            isSelected
                              ? "bg-primary text-surface scale-110 paper-shadow-emerald ring-2 ring-primary ring-offset-2 ring-offset-surface"
                              : "bg-surface-container hover:bg-surface-bright text-sketch-white hover:scale-105"
                          }`}
                        >
                          <span className="text-2xl md:text-3xl mb-1">
                            {step.icon === "terminal" && "💻"}
                            {step.icon === "cloud_upload" && "☁️"}
                            {step.icon === "webhook" && "⚡"}
                            {step.icon === "account_tree" && "⚙️"}
                            {step.icon === "language" && "🌐"}
                          </span>
                          <span
                            className={`font-mono text-[11px] font-bold text-center leading-tight px-1 ${
                              isSelected ? "text-surface" : "text-sketch-white"
                            }`}
                          >
                            {step.title}
                          </span>
                        </div>

                        {/* Pro Tip Sticky Marginalia on Webhook Step */}
                        {step.badge && (
                          <div className="hidden lg:block absolute -top-12 -right-28 z-30 pointer-events-none">
                            <div className="bg-secondary text-surface text-[11px] font-mono font-bold py-1 px-3 doodle-border transform rotate-3 shadow-md whitespace-nowrap inline-block">
                              📌 {step.badge}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Arrow Divider */}
                      {idx < PIPELINE_STEPS.length - 1 && (
                        <div className="text-primary font-bold text-xl md:rotate-0 rotate-90 select-none opacity-70">
                          →
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>

              {/* ========================================================================= */}
              {/* SELECTED STEP DEEP DIVE INSPECTOR */}
              {/* ========================================================================= */}
              <div className="mt-8 bg-surface-container-lowest doodle-border p-6 relative border-l-4 border-l-primary animate-fade-in">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4 pb-3 border-b border-outline-variant/30">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-primary font-bold uppercase">
                        Stage 0{selectedStep.number}: {selectedStep.title}
                      </span>
                      <span className="text-xs text-outline font-mono">
                        ({selectedStep.subtitle})
                      </span>
                    </div>
                    <p className="text-sm text-on-surface-variant mt-1">
                      {selectedStep.details.description}
                    </p>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2 shrink-0">
                    <span className="font-mono text-[11px] px-2.5 py-1 bg-surface-container-high text-primary border border-outline-variant/40 rounded">
                      🛠️ {selectedStep.details.tech}
                    </span>
                    <span className="font-mono text-[11px] px-2.5 py-1 bg-primary/10 text-primary border border-primary/30 rounded font-bold">
                      ⚡ {selectedStep.details.metrics}
                    </span>
                  </div>
                </div>

                {/* Code Snippet Box */}
                {selectedStep.details.codeSnippet && (
                  <div className="bg-[#0c0c0c] doodle-border p-4 font-mono text-xs text-sketch-white relative overflow-x-auto">
                    <div className="flex justify-between items-center pb-2 mb-2 border-b border-outline-variant/20 text-outline text-[11px]">
                      <span>telemetry.log / inspector</span>
                      <button
                        onClick={() => handleCopy(selectedStep.details.codeSnippet!, selectedStep.id)}
                        className="hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
                      >
                        <span>{copiedText === selectedStep.id ? "✓ Copied!" : "📋 Copy"}</span>
                      </button>
                    </div>
                    <pre className="text-primary-fixed leading-relaxed">
                      {selectedStep.details.codeSnippet}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* STEP-BY-STEP WALKTHROUGH & ASIDE CHECKLIST */}
          {/* ========================================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-20">
            {/* Main Walkthrough Cards */}
            <div className="lg:col-span-8 space-y-8">
              <h2
                className="font-serif text-3xl font-bold text-sketch-white flex items-center gap-3"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                <span className="text-primary">📋</span> Step-by-Step Developer Guide
              </h2>

              {/* Step 1: Initialize Project */}
              <div id="step-1" className="bg-surface-container-high/50 doodle-border p-6 md:p-8 relative scroll-mt-24">
                <div className="absolute -left-3.5 top-6 w-8 h-8 bg-primary text-surface font-mono font-bold text-sm rounded-full border-2 border-sketch-white flex items-center justify-center">
                  1
                </div>

                <div className="pl-3 md:pl-5">
                  <h3
                    className="font-serif text-xl font-bold text-sketch-white mb-2"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    Initialize the Project &amp; Configure Blueprint
                  </h3>
                  <p className="text-sm text-on-surface-variant mb-4 leading-relaxed">
                    Link your local repository to DeployHub using the CLI or simply import via GitHub OAuth in the web dashboard. DeployHub automatically inspects your dependencies to detect Next.js, Vite, React, Astro, or Python backends.
                  </p>

                  {/* Terminal Command Block */}
                  <div className="bg-[#000] doodle-border p-4 font-mono text-xs text-primary flex justify-between items-center group">
                    <code>$ npm install -g deployhub &amp;&amp; dh init</code>
                    <button
                      onClick={() => handleCopy("npm install -g deployhub && dh init", "cmd-1")}
                      className="text-outline-variant hover:text-primary transition-colors p-1.5 cursor-pointer"
                      title="Copy command"
                    >
                      {copiedText === "cmd-1" ? "✓ Copied" : "📋"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Step 2: Build & Deploy */}
              <div id="step-2" className="bg-surface-container-high/50 doodle-border p-6 md:p-8 relative scroll-mt-24">
                <div className="absolute -left-3.5 top-6 w-8 h-8 bg-primary text-surface font-mono font-bold text-sm rounded-full border-2 border-sketch-white flex items-center justify-center">
                  2
                </div>

                <div className="pl-3 md:pl-5">
                  <h3
                    className="font-serif text-xl font-bold text-sketch-white mb-2"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    Trigger Deployment &amp; Stream Live Logs
                  </h3>
                  <p className="text-sm text-on-surface-variant mb-4 leading-relaxed">
                    Once pushed, DeployHub spins up an isolated Docker container with strict CPU/memory limits. Real-time build logs stream to your browser via WebSockets while Kafka coordinates async notifications.
                  </p>

                  {/* Terminal Command Block */}
                  <div className="bg-[#000] doodle-border p-4 font-mono text-xs text-primary flex justify-between items-center group">
                    <code>$ dh deploy --env production --follow-logs</code>
                    <button
                      onClick={() => handleCopy("dh deploy --env production --follow-logs", "cmd-2")}
                      className="text-outline-variant hover:text-primary transition-colors p-1.5 cursor-pointer"
                      title="Copy command"
                    >
                      {copiedText === "cmd-2" ? "✓ Copied" : "📋"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Step 3: Atomic Rollbacks */}
              <div id="step-3" className="bg-surface-container-high/50 doodle-border p-6 md:p-8 relative scroll-mt-24">
                <div className="absolute -left-3.5 top-6 w-8 h-8 bg-primary text-surface font-mono font-bold text-sm rounded-full border-2 border-sketch-white flex items-center justify-center">
                  3
                </div>

                <div className="pl-3 md:pl-5">
                  <h3
                    className="font-serif text-xl font-bold text-sketch-white mb-2"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    Instant Atomic Rollback (&lt; 290ms)
                  </h3>
                  <p className="text-sm text-on-surface-variant mb-4 leading-relaxed">
                    Every historical build artifact remains immutably stored in MinIO S3. If a regression occurs in production, you can instantly shift live reverse-proxy traffic to any previous deployment with zero container rebuilds.
                  </p>

                  {/* Terminal Command Block */}
                  <div className="bg-[#000] doodle-border p-4 font-mono text-xs text-primary flex justify-between items-center group">
                    <code>$ dh rollback --to dep-v141</code>
                    <button
                      onClick={() => handleCopy("dh rollback --to dep-v141", "cmd-3")}
                      className="text-outline-variant hover:text-primary transition-colors p-1.5 cursor-pointer"
                      title="Copy command"
                    >
                      {copiedText === "cmd-3" ? "✓ Copied" : "📋"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Step 4: Secrets & Custom Domains */}
              <div id="step-4" className="bg-surface-container-high/50 doodle-border p-6 md:p-8 relative scroll-mt-24">
                <div className="absolute -left-3.5 top-6 w-8 h-8 bg-primary text-surface font-mono font-bold text-sm rounded-full border-2 border-sketch-white flex items-center justify-center">
                  4
                </div>

                <div className="pl-3 md:pl-5">
                  <h3
                    className="font-serif text-xl font-bold text-sketch-white mb-2"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    AES-256 Secrets Vault &amp; Custom Subdomains
                  </h3>
                  <p className="text-sm text-on-surface-variant mb-4 leading-relaxed">
                    Environment variables are encrypted at rest with AES-256-GCM. Caddy Admin API automatically provisions wildcard SSL certificates for your custom subdomains (`*.deployhub.dev`).
                  </p>

                  {/* Terminal Command Block */}
                  <div className="bg-[#000] doodle-border p-4 font-mono text-xs text-primary flex justify-between items-center group">
                    <code>$ dh env set DATABASE_URL="postgresql://user:pass@host:5432/db"</code>
                    <button
                      onClick={() => handleCopy('dh env set DATABASE_URL="postgresql://user:pass@host:5432/db"', "cmd-4")}
                      className="text-outline-variant hover:text-primary transition-colors p-1.5 cursor-pointer"
                      title="Copy command"
                    >
                      {copiedText === "cmd-4" ? "✓ Copied" : "📋"}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* ========================================================================= */}
            {/* RIGHT ASIDE: CHECKLIST & DISCORD WIDGET */}
            {/* ========================================================================= */}
            <div className="lg:col-span-4 mt-8 lg:mt-0 relative">
              <div className="sticky top-28 space-y-6">
                {/* Quick Checklist Card */}
                <div className="bg-surface-container-high doodle-border p-6 transform rotate-1 paper-shadow-lg">
                  <h4
                    className="font-serif text-lg text-tertiary mb-4 flex items-center gap-2 font-bold"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    <span>💡</span> Quick Deployment Checklist
                  </h4>

                  <ul className="space-y-3 font-mono text-xs text-on-surface-variant">
                    <li
                      onClick={() => toggleChecklist("yaml")}
                      className="flex items-start gap-2.5 cursor-pointer hover:text-sketch-white transition-colors"
                    >
                      <span className={checklist.yaml ? "text-primary font-bold" : "text-outline"}>
                        {checklist.yaml ? "☑" : "☐"}
                      </span>
                      <span className={checklist.yaml ? "line-through opacity-80" : ""}>
                        Ensure `dh.yaml` or build script is configured
                      </span>
                    </li>

                    <li
                      onClick={() => toggleChecklist("repo")}
                      className="flex items-start gap-2.5 cursor-pointer hover:text-sketch-white transition-colors"
                    >
                      <span className={checklist.repo ? "text-primary font-bold" : "text-outline"}>
                        {checklist.repo ? "☑" : "☐"}
                      </span>
                      <span className={checklist.repo ? "line-through opacity-80" : ""}>
                        Connect GitHub repository via OAuth
                      </span>
                    </li>

                    <li
                      onClick={() => toggleChecklist("env")}
                      className="flex items-start gap-2.5 cursor-pointer hover:text-sketch-white transition-colors"
                    >
                      <span className={checklist.env ? "text-primary font-bold" : "text-outline"}>
                        {checklist.env ? "☑" : "☐"}
                      </span>
                      <span className={checklist.env ? "line-through opacity-80" : ""}>
                        Add production environment secrets
                      </span>
                    </li>

                    <li
                      onClick={() => toggleChecklist("output")}
                      className="flex items-start gap-2.5 cursor-pointer hover:text-sketch-white transition-colors"
                    >
                      <span className={checklist.output ? "text-primary font-bold" : "text-outline"}>
                        {checklist.output ? "☑" : "☐"}
                      </span>
                      <span className={checklist.output ? "line-through opacity-80" : ""}>
                        Verify output directory (`.next` / `dist`)
                      </span>
                    </li>
                  </ul>

                  {/* Need Help CTA */}
                  <div className="mt-6 border-t-2 border-dashed border-outline-variant/40 pt-4 text-center">
                    <span className="font-serif text-sm text-sketch-white block mb-2 font-bold">
                      Need Assistance?
                    </span>
                    <a
                      href="https://discord.com"
                      target="_blank"
                      rel="noreferrer"
                      className="inline-block bg-primary text-surface font-mono font-bold text-xs px-4 py-2 doodle-border-emerald hover:bg-primary-fixed transition-transform transform hover:scale-105"
                    >
                      Join Discord Community ⚡
                    </a>
                  </div>
                </div>

                {/* Architecture Reference Callout */}
                <div className="bg-surface-container-low doodle-border p-5 font-mono text-xs text-outline space-y-2">
                  <div className="text-primary font-bold flex items-center gap-1.5">
                    <span>⚙️</span> Distributed Engine:
                  </div>
                  <p className="text-[11px] text-on-surface-variant leading-relaxed">
                    Powered by FastAPI, Apache Kafka event queues, Redis distributed locks, MinIO S3 object storage, and Caddy dynamically configured reverse-proxy.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* ========================================================================= */}
      {/* FOOTER */}
      {/* ========================================================================= */}
      <footer className="bg-surface-container-lowest flex flex-col md:flex-row justify-between items-center px-6 md:px-12 py-6 w-full border-t-2 border-outline-variant/30 text-xs font-mono text-outline">
        <div className="flex items-center gap-3 mb-2 md:mb-0">
          <DeployHubLogo className="h-7" />
        </div>
        <div className="text-on-surface-variant mb-2 md:mb-0 text-center">
          © {new Date().getFullYear()} DeployHub — Crafted with Ink &amp; Code
        </div>
        <nav className="flex gap-4">
          <Link href="/dashboard" className="hover:text-primary transition-colors">
            Dashboard
          </Link>
          <Link href="/docs" className="hover:text-primary transition-colors text-primary font-bold">
            Docs
          </Link>
          <Link href="/#faq" className="hover:text-primary transition-colors">
            FAQ
          </Link>
        </nav>
      </footer>
    </div>
  );
}
