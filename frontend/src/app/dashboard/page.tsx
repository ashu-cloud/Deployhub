"use client";

import React, { useState } from "react";
import Link from "next/link";
import { DeployHubLogo, SketchRocket, SketchTerminalIcon, SketchLockIcon, SketchSparkle } from "@/components/SketchIcons";

interface ProjectItem {
  id: string;
  name: string;
  desc: string;
  env: "Prod" | "Staging" | "Dev";
  status: "Healthy" | "Building" | "Idle" | "Failed";
  time: string;
  branch: string;
  subdomain: string;
  framework: string;
}

const INITIAL_PROJECTS: ProjectItem[] = [
  {
    id: "1",
    name: "api-gateway-core",
    desc: "Main routing cluster & reverse proxy for V2 endpoints.",
    env: "Prod",
    status: "Healthy",
    time: "2m ago",
    branch: "main",
    subdomain: "api.deployhub.local",
    framework: "FastAPI",
  },
  {
    id: "2",
    name: "frontend-dashboard",
    desc: "Next.js 15 App Router SPA with sketchbook tokens.",
    env: "Staging",
    status: "Building",
    time: "Just now",
    branch: "feat/doodle-ui",
    subdomain: "dash-preview.deployhub.local",
    framework: "Next.js",
  },
  {
    id: "3",
    name: "auth-service",
    desc: "OAuth2 GitHub implementation and encrypted token vault.",
    env: "Prod",
    status: "Healthy",
    time: "1h ago",
    branch: "main",
    subdomain: "auth.deployhub.local",
    framework: "Python",
  },
  {
    id: "4",
    name: "build-orchestrator",
    desc: "aiodocker worker runner with Kafka consumer group.",
    env: "Prod",
    status: "Healthy",
    time: "3h ago",
    branch: "main",
    subdomain: "orchestrator.deployhub.local",
    framework: "Docker",
  },
  {
    id: "5",
    name: "docs-portal",
    desc: "Static documentation site generated with Astro.",
    env: "Dev",
    status: "Idle",
    time: "1d ago",
    branch: "docs-v2",
    subdomain: "docs.deployhub.local",
    framework: "Astro",
  },
];

export default function DashboardPage() {
  const [projects, setProjects] = useState<ProjectItem[]>(INITIAL_PROJECTS);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newRepoUrl, setNewRepoUrl] = useState("");

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.framework.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    const newProj: ProjectItem = {
      id: Date.now().toString(),
      name: newProjectName.toLowerCase().replace(/\s+/g, "-"),
      desc: newRepoUrl ? `Connected to ${newRepoUrl}` : "New cloud deployment project.",
      env: "Staging",
      status: "Building",
      time: "Just now",
      branch: "main",
      subdomain: `${newProjectName.toLowerCase().replace(/\s+/g, "-")}.deployhub.local`,
      framework: "Next.js",
    };

    setProjects([newProj, ...projects]);
    setNewProjectName("");
    setNewRepoUrl("");
    setShowNewProjectModal(false);
  };

  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen flex flex-col md:flex-row relative overflow-x-hidden paper-texture">
      {/* ========================================================================= */}
      {/* MOBILE TOPBAR */}
      {/* ========================================================================= */}
      <header className="md:hidden flex justify-between items-center w-full px-6 h-16 z-50 bg-background border-b-2 border-outline-variant">
        <Link href="/" className="h-8 wiggle">
          <DeployHubLogo className="h-8" />
        </Link>
        <button
          onClick={() => setShowNewProjectModal(true)}
          className="doodle-btn bg-primary text-surface font-mono font-bold text-xs px-3 py-1.5"
        >
          + Deploy
        </button>
      </header>

      {/* ========================================================================= */}
      {/* SIDEBAR NAVIGATION (Desktop) */}
      {/* ========================================================================= */}
      <aside className="hidden md:flex flex-col h-screen w-64 bg-surface-container-low border-r-2 border-outline-variant p-6 sticky top-0 shrink-0 z-40 relative">
        {/* Doodle: Paperclip */}
        <svg
          className="absolute top-4 -right-4 w-10 h-10 text-outline-variant rotate-12 opacity-60 z-50 pointer-events-none"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            d="M14 7v9.5a4.5 4.5 0 0 1-9 0V7a3 3 0 0 1 6 0v8.5a1.5 1.5 0 0 1-3 0V7"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
        </svg>

        {/* Brand Logo */}
        <div className="mb-6">
          <Link href="/" className="inline-block wiggle">
            <DeployHubLogo className="h-9" />
          </Link>
        </div>

        {/* User Workspace Profile Card */}
        <div className="flex items-center gap-3 mb-6 doodle-border p-3 bg-surface rotate-1 shadow-sm">
          <div className="w-9 h-9 rounded-full bg-primary/20 border-2 border-primary text-primary flex items-center justify-center font-mono font-bold text-sm shrink-0">
            AP
          </div>
          <div className="overflow-hidden">
            <h2 className="text-xs font-mono font-bold text-sketch-white truncate">
              Ashu Panchal
            </h2>
            <p className="text-[10px] font-mono text-outline truncate">
              github: @ashupanchal
            </p>
          </div>
        </div>

        {/* New Deployment Button */}
        <button
          onClick={() => setShowNewProjectModal(true)}
          className="w-full doodle-btn bg-primary text-surface font-mono font-bold text-xs py-2.5 flex items-center justify-center gap-2 paper-shadow hover:bg-primary-fixed transition-all -rotate-1 hover:rotate-0 mb-6 cursor-pointer"
        >
          <span className="text-base">+</span>
          <span>Deploy Project</span>
        </button>

        {/* Nav Links */}
        <ul className="flex flex-col gap-2 flex-grow font-mono text-xs">
          {[
            { name: "Dashboard", icon: "⊞" },
            { name: "Deployments", icon: "🚀" },
            { name: "Logs Stream", icon: "⚡" },
            { name: "Kafka Events", icon: "☊" },
            { name: "Secrets Vault", icon: "🔒" },
          ].map((item) => {
            const isActive = activeTab === item.name;
            return (
              <li key={item.name} className={isActive ? "rotate-0.5" : ""}>
                <button
                  onClick={() => setActiveTab(item.name)}
                  className={`w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 transition-all cursor-pointer ${
                    isActive
                      ? "bg-surface-container-high text-primary font-bold doodle-border paper-shadow"
                      : "text-on-surface-variant hover:text-sketch-white hover:bg-surface-container"
                  }`}
                >
                  <span className="text-sm">{item.icon}</span>
                  <span>{item.name}</span>
                </button>
              </li>
            );
          })}
        </ul>

        {/* Bottom Sidebar Utility Links */}
        <div className="mt-auto border-t-2 border-outline-variant border-dashed pt-4 font-mono text-xs text-outline space-y-2">
          <Link
            href="/"
            className="flex items-center gap-2 hover:text-primary transition-colors"
          >
            <span>←</span>
            <span>Back to Landing Page</span>
          </Link>
          <div className="text-[10px] text-outline/80 pt-1">
            Cluster: <strong className="text-primary">Kafka KRaft Live</strong>
          </div>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MAIN CONTENT AREA */}
      {/* ========================================================================= */}
      <main className="flex-grow p-6 md:p-12 max-w-7xl mx-auto w-full relative">
        {/* Doodle: Coffee Stain */}
        <div className="absolute top-16 right-12 w-20 h-20 opacity-15 hidden lg:block rounded-full border-4 border-dashed border-[#ffb688] transform -rotate-12 pointer-events-none"></div>

        {/* Header & Search Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-10 gap-6 relative">
          <div className="transform -rotate-1">
            <h1
              className="text-4xl md:text-5xl font-extrabold text-sketch-white font-serif tracking-tight"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Workspace <span className="text-primary sketch-underline">Overview</span>
            </h1>
            <p className="text-on-surface-variant font-mono text-xs mt-2">
              Autonomous container builds & sub-second dynamic routing.
            </p>
          </div>

          {/* Search Input */}
          <div className="relative w-full md:w-80 group">
            <span className="absolute left-3 top-2.5 text-outline text-sm">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Find a project or repo..."
              className="w-full bg-surface-container doodle-border pl-9 pr-4 py-2 text-xs font-mono text-sketch-white placeholder-outline focus:outline-none focus:border-primary paper-shadow"
            />
          </div>
        </div>

        {/* ========================================================================= */}
        {/* ACTIVE PROJECTS GRID */}
        {/* ========================================================================= */}
        <section className="mb-12 relative">
          <div className="flex justify-between items-center mb-6">
            <h2
              className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              <span>📁 Active Projects</span>
              <span className="text-xs font-mono font-normal text-outline">
                ({filteredProjects.length} total)
              </span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project, idx) => {
              const rotation = idx % 2 === 0 ? "transform -rotate-1 hover:rotate-0" : "transform rotate-1 hover:rotate-0";
              const isHealthy = project.status === "Healthy";
              const isBuilding = project.status === "Building";

              return (
                <div
                  key={project.id}
                  className={`doodle-border bg-surface-container p-6 relative hover:-translate-y-1.5 transition-all cursor-pointer paper-shadow flex flex-col justify-between ${rotation}`}
                >
                  {/* Washi-Tape Badge */}
                  <div
                    className={`absolute -top-3 -right-2 text-[10px] font-mono font-bold px-2.5 py-0.5 border border-outline transform rotate-3 rounded ${
                      project.env === "Prod"
                        ? "bg-primary text-surface"
                        : "bg-tertiary text-surface"
                    }`}
                  >
                    {project.env}
                  </div>

                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-lg font-bold text-sketch-white font-serif flex items-center gap-2">
                        <span>{project.name}</span>
                      </h3>
                      <span className="text-xs font-mono text-outline">
                        {project.framework}
                      </span>
                    </div>

                    <p className="text-xs font-mono text-on-surface-variant mb-6 leading-relaxed">
                      {project.desc}
                    </p>
                  </div>

                  {/* Subdomain & Status Row */}
                  <div className="border-t border-outline-variant/40 pt-4 space-y-2 font-mono text-xs">
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-outline">Live Subdomain:</span>
                      <a
                        href={`https://${project.subdomain}`}
                        onClick={(e) => e.stopPropagation()}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline font-bold flex items-center gap-1"
                      >
                        <span>{project.subdomain}</span>
                        <span className="text-[10px]">↗</span>
                      </a>
                    </div>

                    <div className="flex justify-between items-center pt-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2.5 h-2.5 rounded-full inline-block ${
                            isHealthy
                              ? "bg-primary animate-pulse"
                              : isBuilding
                              ? "bg-tertiary animate-spin"
                              : "bg-outline"
                          }`}
                        ></span>
                        <span
                          className={`text-[11px] font-bold ${
                            isHealthy
                              ? "text-primary"
                              : isBuilding
                              ? "text-tertiary"
                              : "text-outline"
                          }`}
                        >
                          {project.status}
                        </span>
                      </div>
                      <span className="text-[11px] text-outline">{project.time}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      {/* ========================================================================= */}
      {/* NEW PROJECT MODAL */}
      {/* ========================================================================= */}
      {showNewProjectModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-high doodle-border-emerald p-6 md:p-8 max-w-md w-full paper-shadow-lg relative animate-fade-up">
            <div className="washi-tape-1 bg-primary"></div>
            <button
              onClick={() => setShowNewProjectModal(false)}
              className="absolute top-4 right-4 text-outline hover:text-sketch-white text-lg font-mono"
            >
              ✕
            </button>

            <h3
              className="text-2xl font-bold text-sketch-white font-serif mb-2"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Create New Deployment
            </h3>
            <p className="text-xs font-mono text-on-surface-variant mb-6">
              Connect a Git repository. DeployHub will auto-configure webhooks and isolated Docker runners.
            </p>

            <form onSubmit={handleCreateProject} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-outline font-bold mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. awesome-saas"
                  className="w-full bg-surface doodle-border p-2.5 text-sketch-white placeholder-outline focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-outline font-bold mb-1">GitHub Repo URL</label>
                <input
                  type="text"
                  value={newRepoUrl}
                  onChange={(e) => setNewRepoUrl(e.target.value)}
                  placeholder="github.com/username/repository"
                  className="w-full bg-surface doodle-border p-2.5 text-sketch-white placeholder-outline focus:outline-none focus:border-primary"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowNewProjectModal(false)}
                  className="px-4 py-2 doodle-btn bg-surface text-outline hover:text-sketch-white font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-primary text-surface font-bold doodle-border-emerald paper-shadow-emerald hover:bg-primary-fixed"
                >
                  Deploy Now ⚡
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
