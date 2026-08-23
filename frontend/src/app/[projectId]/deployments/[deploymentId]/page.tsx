"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import NotFound from "@/app/not-found";
import { DeployHubLogo, SketchRocket, SketchTerminalIcon, SketchLockIcon, SketchSparkle } from "@/components/SketchIcons";
import { getProject } from "@/lib/api";

interface LogEntry {
  time: string;
  text: string;
  type: "info" | "warn" | "error" | "success" | "accent";
}

const INITIAL_LOGS: LogEntry[] = [
  { time: "17:53:01", text: "[SYSTEM] Establishing secure WebSocket connection to builder node...", type: "info" },
  { time: "17:53:02", text: "[KAFKA] Acquired event `build.queued` from partition 0 (offset: 9812)", type: "accent" },
  { time: "17:53:03", text: "[REDIS] Acquired distributed project build lock: lock:build:deployhub-web", type: "info" },
  { time: "17:53:04", text: "[DOCKER] Spawning isolated runner container with cgroups (2 CPU, 4GB RAM)", type: "warn" },
  { time: "17:53:06", text: "[GIT] Cloned repository ref `main` (commit: a9f8b4c) in 1.4s", type: "info" },
  { time: "17:53:08", text: "[BUILD] Resolving dependencies via pnpm (lockfile up to date)...", type: "info" },
  { time: "17:53:11", text: "[BUILD] Next.js 16 compiler optimization finished in 3.1s", type: "success" },
  { time: "17:53:12", text: "[UPLOAD] Streaming static chunks & server bundle to MinIO S3 bucket `deployhub-artifacts`", type: "info" },
  { time: "17:53:14", text: "[UPLOAD] Uploaded 48 assets (14.2 MB) with SHA256 integrity check passed", type: "success" },
  { time: "17:53:15", text: "[CADDY] Registering dynamic subdomain route deployhub-web.deployhub.dev via Admin API", type: "accent" },
  { time: "17:53:16", text: "[SYSTEM] Deployment live! Sub-second healthcheck 200 OK in 18ms", type: "success" },
];

const STREAMING_LOGS = [
  { text: "[DOCKER] Building container image from Dockerfile (layer caching active)", type: "info" as const },
  { text: "[UPLOAD] Streaming build artifact bundle to MinIO S3 cluster bucket", type: "info" as const },
  { text: "[KAFKA] Emitted `deployment.uploaded` to topic `deployments.v1`", type: "accent" as const },
  { text: "[CADDY] Registering dynamic subdomain route deployhub-web.deployhub.dev via Admin API", type: "accent" as const },
  { text: "[SYSTEM] Deployment live! Sub-second healthcheck 200 OK in 18ms", type: "success" as const },
];

export default function DeploymentDetailPage() {
  const params = useParams();
  const projectId = (params?.projectId as string) || "deployhub-web";
  const deploymentId = (params?.deploymentId as string) || "dep-v142";

  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS);
  const [currentStage, setCurrentStage] = useState<"kafka" | "docker" | "minio" | "caddy">("docker");
  const [isLive, setIsLive] = useState(false);
  const [isNotFound, setIsNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeStageFilter, setActiveStageFilter] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const logContainerRef = useRef<HTMLDivElement>(null);

  // Validate project existence
  useEffect(() => {
    async function validate() {
      const proj = await getProject(projectId);
      if (!proj) {
        setIsNotFound(true);
        setLoading(false);
        return;
      }
      setLoading(false);
    }
    validate();
  }, [projectId]);

  if (isNotFound) {
    return <NotFound />;
  }

  if (loading) {
    return (
      <div className="bg-background min-h-screen flex items-center justify-center font-mono text-xs text-outline paper-texture">
        <span className="animate-spin text-primary text-base mr-2">⚡</span> Connecting to deployment stream...
      </div>
    );
  }

  // Connect to live WebSocket with fallback to simulated streaming
  useEffect(() => {
    let ws: WebSocket | null = null;
    let fallbackInterval: NodeJS.Timeout | null = null;

    try {
      const wsUrl = `ws://${window.location.hostname}:8006/deployments/ws/${deploymentId}`;
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const now = new Date();
          const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;

          if (data.line) {
            setLogs((prev) => [...prev, { time: timeStr, text: data.line, type: data.line.includes("[WARN]") ? "warn" : data.line.includes("[ERROR]") ? "error" : "info" }]);
          } else if (data.status === "live") {
            setIsLive(true);
            setCurrentStage("caddy");
          }
        } catch (e) {
          // ignore
        }
      };

      ws.onerror = () => {
        // Start simulated playback if backend WebSocket is offline
        startFallbackPlayback();
      };
    } catch (e) {
      startFallbackPlayback();
    }

    function startFallbackPlayback() {
      if (fallbackInterval) return;
      let index = 0;
      fallbackInterval = setInterval(() => {
        if (index < STREAMING_LOGS.length) {
          const item = STREAMING_LOGS[index];
          const now = new Date();
          const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;

          setLogs((prev) => [...prev, { time: timeStr, text: item.text, type: item.type }]);

          if (index === 1) setCurrentStage("minio");
          if (index === 3) setCurrentStage("caddy");
          if (index === 4) {
            setIsLive(true);
            if (fallbackInterval) clearInterval(fallbackInterval);
          }

          index++;
        }
      }, 1800);
    }

    return () => {
      if (ws) ws.close();
      if (fallbackInterval) clearInterval(fallbackInterval);
    };
  }, [deploymentId]);


  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen flex flex-col md:flex-row relative overflow-x-hidden paper-texture">
      {/* ========================================================================= */}
      {/* SIDEBAR NAVIGATION (Desktop) */}
      {/* ========================================================================= */}
      <aside className="hidden md:flex flex-col h-screen w-64 bg-surface-container-low border-r-2 border-outline-variant p-6 sticky top-0 shrink-0 z-40 relative">
        <div className="mb-6">
          <Link href="/" className="inline-block wiggle">
            <DeployHubLogo className="h-9" />
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6 doodle-border p-3 bg-surface rotate-1">
          <div className="w-9 h-9 rounded-full bg-primary/20 border-2 border-primary text-primary flex items-center justify-center font-mono font-bold text-sm shrink-0">
            AP
          </div>
          <div>
            <h2 className="text-xs font-mono font-bold text-sketch-white">Workspace</h2>
            <p className="text-[10px] font-mono text-outline">Production</p>
          </div>
        </div>

        {/* New Project Button */}
        <Link
          href="/new"
          className="w-full doodle-btn bg-primary text-surface font-mono font-bold text-xs py-2.5 flex items-center justify-center gap-2 paper-shadow hover:bg-primary-fixed transition-all -rotate-1 hover:rotate-0 mb-6 text-center"
        >
          <span className="text-base">+</span>
          <span>New Project</span>
        </Link>

        <ul className="flex flex-col gap-2 flex-grow font-mono text-xs">
          <li>
            <Link
              href="/dashboard"
              className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 text-on-surface-variant hover:text-sketch-white hover:bg-surface-container transition-all"
            >
              <span>⊞</span>
              <span>All Projects</span>
            </Link>
          </li>
          <li>
            <Link
              href={`/${projectId}`}
              className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 text-on-surface-variant hover:text-sketch-white hover:bg-surface-container transition-all"
            >
              <span>📁</span>
              <span className="truncate">{projectId}</span>
            </Link>
          </li>
          <li>
            <div className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 bg-surface-container-high text-primary font-bold doodle-border paper-shadow">
              <span>⚡</span>
              <span className="truncate">{deploymentId}</span>
            </div>
          </li>
          <li>
            <Link
              href="/new"
              className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 text-on-surface-variant hover:text-sketch-white hover:bg-surface-container transition-all"
            >
              <span>🔒</span>
              <span>Secrets Vault</span>
            </Link>
          </li>
        </ul>


        <div className="mt-auto border-t-2 border-outline-variant border-dashed pt-4 font-mono text-xs text-outline space-y-2">
          <Link href={`/${projectId}`} className="flex items-center gap-2 hover:text-primary transition-colors">
            <span>←</span>
            <span>Back to Project</span>
          </Link>
          <div className="text-[10px] text-outline/80 pt-1">
            Socket: <strong className="text-primary">Live WS Streaming</strong>
          </div>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MAIN CONTENT AREA */}
      {/* ========================================================================= */}
      <main className="flex-grow p-6 md:p-12 max-w-6xl mx-auto w-full relative flex flex-col gap-8">
        {/* Floating Doodle Note */}
        <div className="absolute top-8 right-12 font-mono text-xs text-tertiary hidden lg:flex items-center gap-1.5 rotate-3 opacity-90">
          <SketchSparkle className="w-4 h-4 text-tertiary" />
          <span>Building at the speed of thought!</span>
        </div>

        {/* Header Section */}
        <header className="border-b-2 border-outline-variant pb-6 border-dashed">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1
                  className="text-3xl md:text-4xl font-extrabold text-sketch-white font-serif tracking-tight"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  {deploymentId}
                </h1>

                <span
                  className={`px-3 py-0.5 rounded font-mono font-bold text-xs doodle-border transform -rotate-1 flex items-center gap-1.5 ${
                    isLive
                      ? "bg-primary text-surface paper-shadow-emerald"
                      : "bg-tertiary text-surface animate-pulse"
                  }`}
                >
                  <span>{isLive ? "✓ LIVE" : "⚙ IN PROGRESS"}</span>
                </span>
              </div>

              <div className="font-mono text-xs text-on-surface-variant mt-2 flex items-center gap-3 flex-wrap">
                <span>
                  Commit: <strong className="text-accent-blue bg-surface-container px-2 py-0.5 rounded doodle-border">a9f8b4c</strong>
                </span>
                <span className="text-outline">|</span>
                <span>Branch: <strong className="text-sketch-white">main</strong></span>
                <span className="text-outline">|</span>
                <span>Project: <strong className="text-primary">{projectId}</strong></span>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center gap-3 font-mono text-xs">
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`px-3 py-1.5 doodle-border transition-colors ${
                  autoScroll ? "bg-surface text-primary" : "bg-surface text-outline"
                }`}
              >
                Auto-scroll: {autoScroll ? "ON" : "OFF"}
              </button>

              <a
                href={`https://${projectId}.deployhub.dev`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 bg-primary text-surface font-bold doodle-border-emerald paper-shadow-emerald hover:bg-primary-fixed transition-all flex items-center gap-1.5"
              >
                <span>Visit Live URL</span>
                <span>↗</span>
              </a>
            </div>
          </div>
        </header>

        {/* ========================================================================= */}
        {/* PIPELINE STAGE VISUALIZER */}
        {/* ========================================================================= */}
        <section className="w-full">
          <h2 className="font-mono text-xs text-outline mb-3 uppercase tracking-wider flex items-center gap-2">
            <span>⚙ Pipeline Execution Stages</span>
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-surface-container-low p-5 doodle-border relative z-10 paper-shadow">
            {/* Stage 1: Kafka */}
            <div className="flex flex-col items-center text-center p-3 bg-surface rounded doodle-border">
              <div className="w-10 h-10 rounded-full bg-primary/10 border-2 border-primary flex items-center justify-center text-primary font-bold text-sm mb-2">
                ✓
              </div>
              <span className="font-mono text-xs font-bold text-sketch-white">1. Kafka Ingest</span>
              <span className="font-mono text-[10px] text-primary mt-1">Topic: build.queued</span>
            </div>

            {/* Stage 2: Docker Build */}
            <div
              className={`flex flex-col items-center text-center p-3 rounded doodle-border transition-all ${
                currentStage === "docker"
                  ? "bg-surface border-primary paper-shadow-emerald"
                  : "bg-surface"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm mb-2 ${
                  isLive || currentStage !== "docker"
                    ? "bg-primary/10 border-2 border-primary text-primary"
                    : "bg-tertiary/10 border-2 border-tertiary text-tertiary animate-spin"
                }`}
              >
                {isLive || currentStage !== "docker" ? "✓" : "⚙"}
              </div>
              <span className="font-mono text-xs font-bold text-sketch-white">2. Docker Runner</span>
              <span className="font-mono text-[10px] text-outline mt-1">Isolated Sandbox</span>
            </div>

            {/* Stage 3: MinIO S3 */}
            <div
              className={`flex flex-col items-center text-center p-3 rounded doodle-border transition-all ${
                currentStage === "minio"
                  ? "bg-surface border-primary paper-shadow-emerald"
                  : "bg-surface"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm mb-2 ${
                  isLive || currentStage === "caddy"
                    ? "bg-primary/10 border-2 border-primary text-primary"
                    : currentStage === "minio"
                    ? "bg-tertiary/10 border-2 border-tertiary text-tertiary animate-spin"
                    : "bg-surface-container-high border-2 border-outline-variant text-outline"
                }`}
              >
                {isLive || currentStage === "caddy" ? "✓" : currentStage === "minio" ? "⚙" : "•"}
              </div>
              <span className="font-mono text-xs font-bold text-sketch-white">3. S3 Artifacts</span>
              <span className="font-mono text-[10px] text-outline mt-1">MinIO Immutable</span>
            </div>

            {/* Stage 4: Caddy Routing */}
            <div
              className={`flex flex-col items-center text-center p-3 rounded doodle-border transition-all ${
                isLive
                  ? "bg-surface border-primary paper-shadow-emerald"
                  : "bg-surface"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm mb-2 ${
                  isLive
                    ? "bg-primary/10 border-2 border-primary text-primary"
                    : currentStage === "caddy"
                    ? "bg-tertiary/10 border-2 border-tertiary text-tertiary animate-spin"
                    : "bg-surface-container-high border-2 border-outline-variant text-outline"
                }`}
              >
                {isLive ? "✓" : currentStage === "caddy" ? "⚙" : "•"}
              </div>
              <span className="font-mono text-xs font-bold text-sketch-white">4. Caddy Route</span>
              <span className="font-mono text-[10px] text-outline mt-1">&lt; 350ms Atomic</span>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SPLIT SECTION: LIVE LOGS TERMINAL & AI DIAGNOSIS */}
        {/* ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
          {/* Terminal Console */}
          <div className="bg-[#0c0c0c] doodle-border p-0 overflow-hidden shadow-2xl relative">
            {/* Terminal Window Topbar */}
            <div className="bg-surface-container-high px-4 py-3 border-b border-outline-variant/40 flex justify-between items-center font-mono text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-error-container border border-error"></div>
                <div className="w-3 h-3 rounded-full bg-tertiary-container border border-tertiary"></div>
                <div className="w-3 h-3 rounded-full bg-primary-container border border-primary"></div>
                <span className="text-outline ml-2 font-bold">Stream: {deploymentId}.log</span>
              </div>
              <div className="flex items-center gap-3 text-outline text-[11px]">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-primary animate-ping"></span>
                  <span>LIVE</span>
                </span>
              </div>
            </div>

            {/* Log Stream Output */}
            <div
              ref={logContainerRef}
              className="p-5 font-mono text-xs text-on-surface-variant max-h-[460px] overflow-y-auto space-y-2 leading-relaxed"
            >
              {logs.map((log, index) => (
                <div key={index} className="flex items-start gap-3">
                  <span className="text-outline select-none shrink-0 font-mono text-[11px]">
                    {log.time}
                  </span>
                  <span
                    className={
                      log.type === "accent"
                        ? "text-tertiary font-bold"
                        : log.type === "warn"
                        ? "text-tertiary-fixed-dim"
                        : log.type === "success"
                        ? "text-primary font-bold"
                        : log.type === "error"
                        ? "text-error font-bold"
                        : "text-sketch-white"
                    }
                  >
                    {log.text}
                  </span>
                </div>
              ))}

              {!isLive && (
                <div className="flex items-center gap-2 text-primary pt-2">
                  <span className="animate-pulse">█</span>
                  <span className="text-outline text-[11px] italic">Awaiting builder stdout chunk...</span>
                </div>
              )}
            </div>
          </div>

          {/* AI Root-Cause Diagnosis Card */}
          <aside className="bg-paper-gray text-on-surface p-6 doodle-border shadow-xl rotate-1 relative">
            <div className="washi-tape-1 -top-3 left-6 bg-tertiary">AI Heuristics</div>

            <h3
              className="text-xl font-bold text-sketch-white font-serif mb-4 flex items-center gap-2 border-b-2 border-dashed border-outline-variant/40 pb-2"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              <SketchSparkle className="w-5 h-5 text-tertiary" />
              <span>Pipeline Analysis</span>
            </h3>

            <div className="font-mono text-xs space-y-4">
              <div className="p-3 bg-surface rounded doodle-border">
                <div className="text-primary font-bold mb-1">Status: Optimal</div>
                <p className="text-outline text-[11px] leading-relaxed">
                  Zero syntax warnings or memory threshold alerts. Container memory peaked at 480MB / 4096MB limit.
                </p>
              </div>

              <div className="p-3 bg-surface rounded doodle-border">
                <div className="text-outline font-bold mb-1">Bundle Size Check</div>
                <p className="text-outline text-[11px] leading-relaxed">
                  Next.js output bundle is 1.8MB gzip compressed. MinIO upload verified with SHA256 integrity hash.
                </p>
              </div>

              <button
                type="button"
                className="w-full py-2 bg-surface hover:bg-surface-variant text-sketch-white font-bold doodle-border transition-colors text-center cursor-pointer"
              >
                Inspect Build Manifest ↗
              </button>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
