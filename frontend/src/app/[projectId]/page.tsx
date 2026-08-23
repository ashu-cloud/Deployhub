"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DeployHubLogo, SketchRocket, SketchLockIcon, SketchSparkle, SketchTerminalIcon } from "@/components/SketchIcons";

interface DeploymentItem {
  id: string;
  commitHash: string;
  commitMessage: string;
  branch: string;
  author: string;
  time: string;
  duration: string;
  status: "live" | "success" | "failed" | "building";
  errorMessage?: string;
}

export default function ProjectOverviewPage() {
  const params = useParams();
  const projectId = (params?.projectId as string) || "deployhub-web";

  const [activeTab, setActiveTab] = useState<"deployments" | "overview" | "infrastructure" | "settings">("deployments");
  const [isDeployingNow, setIsDeployingNow] = useState(false);
  const [rollbackSuccessMsg, setRollbackSuccessMsg] = useState<string | null>(null);

  const [deployments, setDeployments] = useState<DeploymentItem[]>([
    {
      id: "dep-9921",
      commitHash: "a1b2c3d",
      commitMessage: "feat: add reactive Kafka KRaft worker cluster with Redlock",
      branch: "main",
      author: "Ashu Panchal",
      time: "2 mins ago",
      duration: "42s",
      status: "live",
    },
    {
      id: "dep-9918",
      commitHash: "f9e8d7c",
      commitMessage: "refactor: optimize Next.js 15 bundle size and washi-tape tokens",
      branch: "main",
      author: "Ashu Panchal",
      time: "3 hours ago",
      duration: "38s",
      status: "success",
    },
    {
      id: "dep-9910",
      commitHash: "b4c5d6e",
      commitMessage: "fix: resolve memory leak in worker thread pool",
      branch: "fix/oom-worker",
      author: "Ashu Panchal",
      time: "Yesterday",
      duration: "18s",
      status: "failed",
      errorMessage: "Error: Process exited with code 137 (Out of Memory cgroup limit exceeded)",
    },
    {
      id: "dep-9892",
      commitHash: "8e7d6c5",
      commitMessage: "chore: initial production deployment with Caddy reverse proxy",
      branch: "main",
      author: "Ashu Panchal",
      time: "2 days ago",
      duration: "55s",
      status: "success",
    },
  ]);

  const handleRollback = (deployment: DeploymentItem) => {
    setRollbackSuccessMsg(`Rolling back live traffic to ${deployment.commitHash} via Caddy Admin API...`);
    setTimeout(() => {
      setDeployments((prev) =>
        prev.map((d) => {
          if (d.id === deployment.id) return { ...d, status: "live" };
          if (d.status === "live") return { ...d, status: "success" };
          return d;
        })
      );
      setRollbackSuccessMsg(`✓ Atomic Rollback complete (<290ms)! Subdomain traffic now routed to commit ${deployment.commitHash}.`);
      setTimeout(() => setRollbackSuccessMsg(null), 5000);
    }, 350);
  };

  const handleTriggerDeploy = () => {
    setIsDeployingNow(true);
    const newDep: DeploymentItem = {
      id: `dep-${Date.now().toString().slice(-4)}`,
      commitHash: Math.random().toString(16).substring(2, 9),
      commitMessage: "Manual trigger: rebuild latest main branch",
      branch: "main",
      author: "Ashu Panchal",
      time: "Just now",
      duration: "0s",
      status: "building",
    };
    setDeployments([newDep, ...deployments]);

    setTimeout(() => {
      setDeployments((prev) =>
        prev.map((d) => (d.id === newDep.id ? { ...d, status: "live", duration: "35s" } : d.status === "live" ? { ...d, status: "success" } : d))
      );
      setIsDeployingNow(false);
    }, 2500);
  };

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

        <Link
          href="/new"
          className="w-full doodle-btn bg-primary text-surface font-mono font-bold text-xs py-2.5 flex items-center justify-center gap-2 paper-shadow hover:bg-primary-fixed transition-all -rotate-1 hover:rotate-0 mb-6"
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
            <div className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 bg-surface-container-high text-primary font-bold doodle-border paper-shadow">
              <span>🚀</span>
              <span className="truncate">{projectId}</span>
            </div>
          </li>
        </ul>

        <div className="mt-auto border-t-2 border-outline-variant border-dashed pt-4 font-mono text-xs text-outline space-y-2">
          <Link href="/dashboard" className="flex items-center gap-2 hover:text-primary transition-colors">
            <span>←</span>
            <span>Back to Dashboard</span>
          </Link>
          <div className="text-[10px] text-outline/80 pt-1">
            Engine: <strong className="text-primary">Caddy Admin API Live</strong>
          </div>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MAIN CONTENT AREA */}
      {/* ========================================================================= */}
      <main className="flex-grow p-6 md:p-12 max-w-5xl mx-auto w-full relative">
        {/* Look ma doodle */}
        <div className="absolute top-10 right-12 font-mono text-xs text-primary italic hidden lg:block rotate-3">
          <span>← Sub-second atomic rollbacks active!</span>
        </div>

        {/* ========================================================================= */}
        {/* HEADER SECTION */}
        {/* ========================================================================= */}
        <header className="mb-10 relative">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-6">
            <div>
              <h1
                className="text-4xl md:text-5xl font-extrabold text-sketch-white font-serif tracking-tight transform -rotate-1 inline-block"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                {projectId}
              </h1>

              <div className="flex items-center gap-3 mt-3 flex-wrap">
                <span className="flex items-center gap-2 px-3 py-1 bg-surface-container-high doodle-border text-on-surface-variant font-mono text-xs">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse border border-black inline-block"></span>
                  <span>Live Production</span>
                </span>

                <a
                  href={`https://${projectId}.deployhub.dev`}
                  target="_blank"
                  rel="noreferrer"
                  className="washi-tape-1 text-xs font-mono font-bold flex items-center gap-1.5 hover:scale-105 transition-transform"
                >
                  <span>{projectId}.deployhub.dev</span>
                  <span className="text-[10px]">↗</span>
                </a>
              </div>
            </div>

            {/* Header Action Buttons */}
            <div className="flex items-center gap-3 font-mono text-xs">
              <Link
                href="/new"
                className="px-4 py-2.5 bg-surface text-on-surface-variant hover:text-sketch-white doodle-border font-bold flex items-center gap-2"
              >
                <span>⚙ Edit Config</span>
              </Link>
              <button
                onClick={handleTriggerDeploy}
                disabled={isDeployingNow}
                className="px-5 py-2.5 bg-primary text-surface font-bold doodle-border-emerald paper-shadow-emerald hover:bg-primary-fixed transition-all flex items-center gap-2 cursor-pointer transform rotate-1 hover:rotate-0"
              >
                {isDeployingNow ? (
                  <>
                    <span className="animate-spin">⚙</span>
                    <span>Building...</span>
                  </>
                ) : (
                  <>
                    <SketchRocket className="w-4 h-4 text-surface" />
                    <span>Deploy Now</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* TABBED INTERFACE */}
          {/* ========================================================================= */}
          <div className="flex gap-6 border-b-2 border-outline-variant border-dashed pb-2 font-mono text-sm">
            {[
              { id: "deployments", label: "Deployments" },
              { id: "overview", label: "Overview & Metrics" },
              { id: "infrastructure", label: "Infrastructure" },
              { id: "settings", label: "Environment & Settings" },
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`relative px-2 py-1 transition-colors cursor-pointer font-bold ${
                    isActive ? "text-primary" : "text-on-surface-variant hover:text-sketch-white"
                  }`}
                >
                  <span>{tab.label}</span>
                  {isActive && (
                    <span className="absolute bottom-[-10px] left-0 right-0 h-[3px] bg-primary rounded-full"></span>
                  )}
                </button>
              );
            })}
          </div>
        </header>

        {/* Rollback Alert Banner */}
        {rollbackSuccessMsg && (
          <div className="mb-8 p-4 bg-primary/10 border-2 border-primary rounded-xl font-mono text-xs text-primary paper-shadow-emerald animate-fade-up flex items-center justify-between">
            <span>{rollbackSuccessMsg}</span>
            <button onClick={() => setRollbackSuccessMsg(null)} className="text-primary font-bold">
              ✕
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 1: DEPLOYMENTS TIMELINE */}
        {/* ========================================================================= */}
        {activeTab === "deployments" && (
          <section className="relative">
            <h2
              className="text-2xl font-bold text-sketch-white font-serif mb-8 flex items-center gap-2"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              <span>⏱ Recent Deployment History</span>
            </h2>

            {/* Vertical Timeline */}
            <div className="relative pl-6 md:pl-10 space-y-8 before:content-[''] before:absolute before:left-3 md:before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-outline-variant before:border-l-2 before:border-dashed before:border-outline-variant">
              {deployments.map((dep) => {
                const isLive = dep.status === "live";
                const isFailed = dep.status === "failed";
                const isBuilding = dep.status === "building";

                return (
                  <div key={dep.id} className="relative group">
                    {/* Status Node */}
                    <div
                      className={`absolute -left-[30px] md:-left-[34px] top-4 w-6 h-6 rounded-full border-2 border-black flex items-center justify-center z-10 text-[10px] font-bold ${
                        isLive
                          ? "bg-primary text-surface animate-pulse"
                          : isFailed
                          ? "bg-error text-surface"
                          : isBuilding
                          ? "bg-tertiary text-surface animate-spin"
                          : "bg-surface-container-high text-outline"
                      }`}
                    >
                      {isLive ? "✓" : isFailed ? "✕" : isBuilding ? "⚙" : "•"}
                    </div>

                    {/* Deployment Card */}
                    <div
                      className={`p-6 rounded-xl doodle-border paper-shadow transition-all ${
                        isLive
                          ? "bg-surface-container border-primary paper-shadow-emerald"
                          : isFailed
                          ? "bg-surface-container-low border-error/50 opacity-80"
                          : "bg-surface-container-low hover:bg-surface-container"
                      }`}
                    >
                      {/* Washi-Tape Branch Tag */}
                      <div
                        className={`absolute -top-3 -right-2 text-[10px] font-mono font-bold px-2 py-0.5 border border-black rounded transform rotate-2 ${
                          isLive ? "bg-primary text-surface" : "bg-tertiary text-surface"
                        }`}
                      >
                        branch: {dep.branch}
                      </div>

                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
                        <div>
                          <h3 className="text-base font-bold text-sketch-white font-serif flex items-center gap-2">
                            <span>{dep.commitMessage}</span>
                          </h3>
                          <div className="font-mono text-xs text-on-surface-variant mt-1.5 flex items-center gap-4 flex-wrap">
                            <span className="text-primary font-bold">#{dep.commitHash}</span>
                            <span>{dep.time} by {dep.author}</span>
                            <span className="text-outline">Build time: {dep.duration}</span>
                          </div>
                        </div>

                        {/* Status Badge & Actions */}
                        <div className="flex items-center gap-3 shrink-0">
                          <Link
                            href={`/${projectId}/deployments/${dep.id}`}
                            className="px-3 py-1.5 bg-surface text-sketch-white hover:text-primary font-mono text-xs doodle-border flex items-center gap-1.5 transition-colors"
                          >
                            <SketchTerminalIcon className="w-3.5 h-3.5 text-primary" />
                            <span>View Logs</span>
                          </Link>

                          {isLive && (
                            <span className="px-3 py-1 bg-primary text-surface font-mono font-bold text-xs rounded border border-black transform -rotate-1">
                              CURRENT LIVE
                            </span>
                          )}

                          {!isLive && !isFailed && !isBuilding && (
                            <button
                              onClick={() => handleRollback(dep)}
                              className="px-3 py-1.5 bg-surface-variant text-on-surface hover:bg-error-container hover:text-on-error-container font-mono text-xs font-bold doodle-border transition-all flex items-center gap-1 cursor-pointer"
                              title="Instant rollback via Caddy (<350ms)"
                            >
                              <span>⏪ Rollback</span>
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Error snippet if failed */}
                      {isFailed && dep.errorMessage && (
                        <div className="mt-3 p-3 bg-error/10 border-l-2 border-error font-mono text-xs text-error">
                          {dep.errorMessage}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: OVERVIEW & METRICS */}
        {/* ========================================================================= */}
        {activeTab === "overview" && (
          <section className="space-y-6 font-mono text-xs animate-fade-up">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-surface-container p-6 doodle-border paper-shadow">
                <span className="text-outline">Avg Response Time</span>
                <div className="text-3xl font-bold text-primary mt-2">18ms</div>
                <p className="text-outline text-[11px] mt-1">Caddy direct S3 reverse proxy</p>
              </div>
              <div className="bg-surface-container p-6 doodle-border paper-shadow">
                <span className="text-outline">Build Success Rate</span>
                <div className="text-3xl font-bold text-sketch-white mt-2">98.4%</div>
                <p className="text-outline text-[11px] mt-1">Isolated Docker cgroups</p>
              </div>
              <div className="bg-surface-container p-6 doodle-border paper-shadow">
                <span className="text-outline">Rollback Speed</span>
                <div className="text-3xl font-bold text-tertiary mt-2">&lt; 290ms</div>
                <p className="text-outline text-[11px] mt-1">Zero container restart needed</p>
              </div>
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: INFRASTRUCTURE */}
        {/* ========================================================================= */}
        {activeTab === "infrastructure" && (
          <section className="bg-surface-container p-6 doodle-border paper-shadow font-mono text-xs space-y-4 animate-fade-up">
            <h3 className="text-lg font-bold text-sketch-white font-serif">Infrastructure Topology</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
              <div className="p-3 bg-surface rounded doodle-border">
                <div className="text-primary font-bold">Kafka KRaft</div>
                <div className="text-outline text-[10px] mt-1">Event Ingestion Topic</div>
              </div>
              <div className="p-3 bg-surface rounded doodle-border">
                <div className="text-primary font-bold">Redis Redlock</div>
                <div className="text-outline text-[10px] mt-1">Distributed Concurrency</div>
              </div>
              <div className="p-3 bg-surface rounded doodle-border">
                <div className="text-primary font-bold">MinIO S3</div>
                <div className="text-outline text-[10px] mt-1">Immutable Bundles</div>
              </div>
              <div className="p-3 bg-surface rounded doodle-border">
                <div className="text-primary font-bold">Caddy Admin</div>
                <div className="text-outline text-[10px] mt-1">Dynamic Subdomains</div>
              </div>
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: SETTINGS */}
        {/* ========================================================================= */}
        {activeTab === "settings" && (
          <section className="bg-surface-container p-6 doodle-border paper-shadow font-mono text-xs space-y-6 animate-fade-up">
            <h3 className="text-lg font-bold text-sketch-white font-serif">Project Settings</h3>
            <div className="space-y-4 max-w-md">
              <div>
                <label className="block text-outline mb-1">Project Identifier</label>
                <input
                  type="text"
                  readOnly
                  value={projectId}
                  className="w-full bg-surface doodle-border p-2.5 text-sketch-white"
                />
              </div>
              <div>
                <label className="block text-outline mb-1">Production Branch</label>
                <input
                  type="text"
                  defaultValue="main"
                  className="w-full bg-surface doodle-border p-2.5 text-sketch-white focus:outline-none focus:border-primary"
                />
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
