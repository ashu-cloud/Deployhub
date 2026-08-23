"use client";

import React, { useState, useEffect } from "react";
import { SketchTerminalIcon, SketchRocket, SketchCheckIcon } from "./SketchIcons";

const SAMPLE_LOGS = [
  { time: "0.0s", text: "[WEBHOOK] Received push event from github.com/octocat/web-app", level: "info" },
  { time: "0.2s", text: "[AUTH] Verified HMAC SHA-256 signature with secret key", level: "success" },
  { time: "0.4s", text: "[KAFKA] Published event `build.queued` (Partition 2, Offset 8192, Topic: build-events)", level: "accent" },
  { time: "0.7s", text: "[REDIS] Acquired distributed build lock: lock:build:proj-9821", level: "info" },
  { time: "1.1s", text: "[DOCKER] Spawning isolated runner with cgroups (2 CPU, 4GB RAM)", level: "warn" },
  { time: "1.8s", text: "[BUILD] Running `npm install && npm run build`...", level: "info" },
  { time: "2.5s", text: "[BUILD] Next.js v15.2.0 production build complete in 700ms", level: "success" },
  { time: "2.9s", text: "[MINIO] Storing immutable bundle `artifacts/v2.4.0.tar.gz` to S3", level: "accent" },
  { time: "3.2s", text: "[CADDY] Dynamic route registered: https://web-app.deployhub.local", level: "success" },
  { time: "3.4s", text: "🚀 DEPLOYMENT LIVE: Subdomain atomic switch completed in 240ms", level: "highlight" },
];

export function InteractiveHeroSandbox() {
  const [isBuilding, setIsBuilding] = useState(false);
  const [logs, setLogs] = useState(SAMPLE_LOGS.slice(0, 4));
  const [currentStep, setCurrentStep] = useState(1);
  const [repoUrl, setRepoUrl] = useState("github.com/octocat/nextjs-starter");

  const startSimulation = () => {
    if (isBuilding) return;
    setIsBuilding(true);
    setLogs([]);
    setCurrentStep(0);

    let stepIndex = 0;
    const interval = setInterval(() => {
      if (stepIndex < SAMPLE_LOGS.length) {
        const nextLog = SAMPLE_LOGS[stepIndex];
        setLogs((prev) => [...prev, nextLog]);
        
        if (stepIndex < 2) setCurrentStep(1); // Ingestion
        else if (stepIndex < 4) setCurrentStep(2); // Queue
        else if (stepIndex < 7) setCurrentStep(3); // Container Build
        else if (stepIndex < 8) setCurrentStep(4); // S3 Artifact
        else setCurrentStep(5); // Live

        stepIndex++;
      } else {
        clearInterval(interval);
        setIsBuilding(false);
      }
    }, 400);
  };

  return (
    <div className="w-full max-w-5xl mx-auto my-8 relative z-20">
      {/* Background sketch glow */}
      <div className="absolute -inset-1 bg-gradient-to-r from-primary/30 via-tertiary/20 to-accent-blue/30 rounded-2xl blur-xl opacity-50 -z-10"></div>

      {/* Main Sandbox Frame */}
      <div className="bg-surface border-2 border-outline-variant/70 rounded-xl paper-shadow-lg overflow-hidden flex flex-col">
        {/* Terminal Header Bar */}
        <div className="bg-surface-container-high px-4 py-3 border-b-2 border-outline-variant/50 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-error/80 border border-error"></div>
              <div className="w-3 h-3 rounded-full bg-tertiary/80 border border-tertiary"></div>
              <div className="w-3 h-3 rounded-full bg-primary/80 border border-primary"></div>
            </div>
            <span className="font-mono text-xs text-on-surface-variant font-bold flex items-center gap-1.5">
              <SketchTerminalIcon className="w-4 h-4 text-tertiary" />
              deployhub-orchestrator :: live-session
            </span>
          </div>

          {/* Quick repo input */}
          <div className="flex items-center gap-2 bg-surface px-3 py-1 rounded doodle-border text-xs font-mono">
            <span className="text-outline">repo:</span>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="bg-transparent text-sketch-white focus:outline-none w-48 text-xs font-mono"
            />
          </div>

          {/* Interactive Trigger Button */}
          <button
            onClick={startSimulation}
            disabled={isBuilding}
            className={`font-mono text-xs font-bold px-4 py-1.5 flex items-center gap-2 transition-all doodle-btn paper-shadow ${
              isBuilding
                ? "bg-surface-variant text-outline cursor-not-allowed"
                : "bg-primary text-surface hover:bg-primary-fixed cursor-pointer"
            }`}
          >
            {isBuilding ? (
              <>
                <span className="animate-spin">⚙</span>
                <span>Building Pipeline...</span>
              </>
            ) : (
              <>
                <SketchRocket className="w-4 h-4 text-surface" />
                <span>Simulate git push</span>
              </>
            )}
          </button>
        </div>

        {/* Pipeline Stage Visualizer */}
        <div className="bg-surface-container-low px-4 py-3 border-b border-outline-variant/30 grid grid-cols-2 md:grid-cols-5 gap-2 font-mono text-xs">
          {[
            { id: 1, label: "1. HMAC Webhook", desc: "Idempotent SHA256" },
            { id: 2, label: "2. Kafka Queue", desc: "Apache Kafka Event" },
            { id: 3, label: "3. Docker Worker", desc: "Isolated Sandbox" },
            { id: 4, label: "4. S3 Bundle", desc: "MinIO Immutable" },
            { id: 5, label: "5. Caddy Route", desc: "<350ms Atomic" },
          ].map((stage) => {
            const isActive = currentStep === stage.id;
            const isCompleted = currentStep > stage.id || (!isBuilding && currentStep === 5);
            return (
              <div
                key={stage.id}
                className={`p-2 rounded border transition-all ${
                  isActive
                    ? "border-primary bg-primary/10 text-primary"
                    : isCompleted
                    ? "border-outline-variant/60 bg-surface text-sketch-white"
                    : "border-transparent text-outline"
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold">
                  {isCompleted ? (
                    <span className="text-primary">✓</span>
                  ) : isActive ? (
                    <span className="animate-pulse text-tertiary">●</span>
                  ) : (
                    <span className="text-outline">○</span>
                  )}
                  <span>{stage.label}</span>
                </div>
                <div className="text-[10px] text-outline mt-0.5">{stage.desc}</div>
              </div>
            );
          })}
        </div>

        {/* Live Streaming Terminal Body */}
        <div className="p-4 bg-surface-dim font-mono text-xs min-h-[220px] max-h-[260px] overflow-y-auto terminal-scroll flex flex-col justify-end">
          <div className="space-y-1.5">
            {logs.map((log, index) => {
              let colorClass = "text-on-surface-variant";
              if (log.level === "success") colorClass = "text-primary font-bold";
              if (log.level === "accent") colorClass = "text-accent-blue";
              if (log.level === "warn") colorClass = "text-tertiary";
              if (log.level === "highlight") colorClass = "text-sketch-white bg-primary/20 p-1 rounded font-bold border border-primary/40";

              return (
                <div key={index} className="flex items-start gap-3 animate-fade-up">
                  <span className="text-outline select-none shrink-0 w-10">[{log.time}]</span>
                  <span className={colorClass}>{log.text}</span>
                </div>
              );
            })}
            {isBuilding && (
              <div className="flex items-center gap-2 text-primary font-mono animate-pulse pt-2">
                <span>&gt;</span>
                <span className="w-2 h-4 bg-primary inline-block"></span>
                <span>processing pipeline stage...</span>
              </div>
            )}
          </div>
        </div>

        {/* Live Subdomain Output Banner */}
        <div className="bg-surface-container px-4 py-2.5 border-t-2 border-outline-variant/40 flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
          <div className="flex items-center gap-2">
            <span className="text-outline">Live Subdomain:</span>
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              className="text-primary hover:underline font-bold flex items-center gap-1"
            >
              https://nextjs-starter.deployhub.local
              <span className="text-[10px] text-tertiary">↗</span>
            </a>
          </div>
          <div className="flex items-center gap-3 text-outline text-[11px]">
            <span>Build Time: <strong className="text-sketch-white">3.4s</strong></span>
            <span>Rollback Latency: <strong className="text-primary">&lt; 240ms</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
}
