"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DeployHubLogo, SketchRocket, SketchLockIcon, SketchTerminalIcon } from "@/components/SketchIcons";

interface EnvVar {
  id: string;
  key: string;
  value: string;
  isSecret: boolean;
}

const REPOS = [
  { id: "1", name: "deployhub-web", desc: "Main marketing and Next.js 15 dashboard app", updated: "2 hours ago", framework: "Next.js", buildCmd: "npm run build", outDir: ".next" },
  { id: "2", name: "auth-service-api", desc: "FastAPI OAuth2 session and token service", updated: "Yesterday", framework: "FastAPI", buildCmd: "pip install -r requirements.txt", outDir: "app" },
  { id: "3", name: "portfolio-astro", desc: "Personal developer portfolio and blog", updated: "3 days ago", framework: "Astro", buildCmd: "npm run build", outDir: "dist" },
  { id: "4", name: "ecommerce-vite-react", desc: "Vite React storefront with Tailwind CSS", updated: "5 days ago", framework: "Vite", buildCmd: "npm run build", outDir: "dist" },
];

import { createProject } from "@/lib/api";

export default function CreateProjectPage() {
  const router = useRouter();
  const [selectedRepo, setSelectedRepo] = useState(REPOS[0]);
  const [searchRepo, setSearchRepo] = useState("");
  const [framework, setFramework] = useState(REPOS[0].framework);
  const [buildCommand, setBuildCommand] = useState(REPOS[0].buildCmd);
  const [outputDirectory, setOutputDirectory] = useState(REPOS[0].outDir);
  const [installCommand, setInstallCommand] = useState("npm install");
  const [isDeploying, setIsDeploying] = useState(false);

  const [envVars, setEnvVars] = useState<EnvVar[]>([
    { id: "1", key: "DATABASE_URL", value: "postgresql://deployhub:secret@localhost:5432/db", isSecret: true },
    { id: "2", key: "NODE_ENV", value: "production", isSecret: false },
  ]);
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [showValues, setShowValues] = useState<{ [id: string]: boolean }>({});

  const handleSelectRepo = (repo: typeof REPOS[0]) => {
    setSelectedRepo(repo);
    setFramework(repo.framework);
    setBuildCommand(repo.buildCmd);
    setOutputDirectory(repo.outDir);
  };

  const handleAddEnv = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim()) return;
    setEnvVars([
      ...envVars,
      { id: Date.now().toString(), key: newKey.toUpperCase().trim(), value: newValue.trim(), isSecret: true },
    ]);
    setNewKey("");
    setNewValue("");
  };

  const handleDeleteEnv = (id: string) => {
    setEnvVars(envVars.filter((v) => v.id !== id));
  };

  const toggleVisibility = (id: string) => {
    setShowValues((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleDeploy = async () => {
    setIsDeploying(true);
    const envMap: Record<string, string> = {};
    envVars.forEach((ev) => {
      envMap[ev.key] = ev.value;
    });

    const repoUrl = `https://github.com/deployhub/${selectedRepo.name}`;
    const project = await createProject({
      repo_name: selectedRepo.name,
      repo_url: repoUrl,
      framework,
      env_vars: envMap,
    });

    setIsDeploying(false);
    router.push(`/${project.id}`);
  };


  const filteredRepos = REPOS.filter((r) =>
    r.name.toLowerCase().includes(searchRepo.toLowerCase())
  );

  return (
    <div className="bg-background dot-grid text-on-background font-body-md min-h-screen flex flex-col md:flex-row overflow-x-hidden paper-texture">
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
          <span>Import Project</span>
        </Link>

        <ul className="flex flex-col gap-2 flex-grow font-mono text-xs">
          <li>
            <Link
              href="/dashboard"
              className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 text-on-surface-variant hover:text-sketch-white hover:bg-surface-container transition-all"
            >
              <span>⊞</span>
              <span>Dashboard</span>
            </Link>
          </li>
          <li>
            <Link
              href="/deployhub-web"
              className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 text-on-surface-variant hover:text-sketch-white hover:bg-surface-container transition-all"
            >
              <span>🚀</span>
              <span>Deployments</span>
            </Link>
          </li>
          <li>
            <Link
              href="/deployhub-web/deployments/dep-v142"
              className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 text-on-surface-variant hover:text-sketch-white hover:bg-surface-container transition-all"
            >
              <span>⚡</span>
              <span>Logs Stream</span>
            </Link>
          </li>
          <li>
            <div className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 bg-surface-container-high text-primary font-bold doodle-border paper-shadow">
              <span>🔒</span>
              <span>New Deployment</span>
            </div>
          </li>
        </ul>


        <div className="mt-auto border-t-2 border-outline-variant border-dashed pt-4 font-mono text-xs text-outline space-y-2">
          <Link href="/dashboard" className="flex items-center gap-2 hover:text-primary transition-colors">
            <span>←</span>
            <span>Back to Dashboard</span>
          </Link>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MAIN CONTENT CANVAS */}
      {/* ========================================================================= */}
      <main className="flex-1 p-6 md:p-12 max-w-5xl mx-auto w-full relative">
        {/* Header Section */}
        <div className="mb-12 relative">
          <div className="transform -rotate-1">
            <h1
              className="text-4xl md:text-6xl font-extrabold text-sketch-white font-serif tracking-tight"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Ship <span className="text-primary sketch-underline">It.</span>
            </h1>
            <p className="font-mono text-xs text-on-surface-variant max-w-xl mt-3 leading-relaxed">
              Import your repository, tweak the dials, and send it live. DeployHub automates isolated Docker runners, MinIO artifact bundling, and sub-second dynamic routing.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-10 relative">
          {/* ========================================================================= */}
          {/* STEP 1: REPOSITORY PICKER */}
          {/* ========================================================================= */}
          <section className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border relative transform -rotate-0.5 hover:rotate-0 transition-transform paper-shadow">
            <div className="washi-tape-1 -top-3 right-8 bg-tertiary">Step 1</div>

            <h2
              className="text-2xl font-bold text-sketch-white font-serif mb-4 flex items-center gap-2"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              <span>📁 Connect Repository</span>
            </h2>

            {/* Search Bar */}
            <div className="relative mb-6">
              <span className="absolute left-3 top-2.5 text-outline text-xs">🔍</span>
              <input
                type="text"
                value={searchRepo}
                onChange={(e) => setSearchRepo(e.target.value)}
                placeholder="Search GitHub repositories..."
                className="w-full bg-surface doodle-border pl-9 pr-4 py-2.5 text-xs font-mono text-sketch-white placeholder-outline focus:outline-none focus:border-primary"
              />
            </div>

            {/* Repository List */}
            <div className="space-y-3 font-mono text-xs">
              {filteredRepos.map((repo) => {
                const isSelected = selectedRepo.id === repo.id;
                return (
                  <div
                    key={repo.id}
                    onClick={() => handleSelectRepo(repo)}
                    className={`flex items-center justify-between p-4 rounded-xl doodle-border transition-all cursor-pointer ${
                      isSelected
                        ? "bg-surface-container-high border-primary paper-shadow-emerald"
                        : "bg-surface hover:bg-surface-container-high border-outline-variant/50"
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-9 h-9 rounded-lg bg-surface-container border border-outline-variant flex items-center justify-center font-bold text-primary shrink-0">
                        &lt;/&gt;
                      </div>
                      <div>
                        <div className="font-bold text-sketch-white flex items-center gap-2">
                          <span>{repo.name}</span>
                          {isSelected && (
                            <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.2 rounded border border-primary/40">
                              Selected
                            </span>
                          )}
                        </div>
                        <p className="text-outline text-[11px] mt-0.5">{repo.desc}</p>
                      </div>
                    </div>

                    <button
                      type="button"
                      className={`px-3 py-1.5 rounded font-bold transition-colors ${
                        isSelected
                          ? "bg-primary text-surface"
                          : "doodle-btn bg-surface text-outline hover:text-sketch-white"
                      }`}
                    >
                      {isSelected ? "Imported ✓" : "Import"}
                    </button>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ========================================================================= */}
          {/* STEP 2 & 3: FRAMEWORK & BUILD CONFIGURATION */}
          {/* ========================================================================= */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
            {/* Step 2: Framework Selection */}
            <section className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border paper-shadow flex flex-col justify-between transform rotate-0.5 hover:rotate-0 transition-transform">
              <div>
                <div className="washi-tape-2 -top-3 right-6 bg-primary">Step 2</div>
                <h2
                  className="text-2xl font-bold text-sketch-white font-serif mb-6 flex items-center gap-2"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  <span>⚡ Framework</span>
                </h2>

                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <div className="w-20 h-20 bg-surface rounded-full flex items-center justify-center border-2 border-primary shadow-sm mb-3">
                    <SketchTerminalIcon className="w-10 h-10 text-primary" />
                  </div>
                  <span className="font-mono text-[11px] text-tertiary bg-tertiary/10 border border-tertiary/30 px-2 py-0.5 rounded mb-2">
                    Auto-detected Preset
                  </span>
                  <h3 className="text-2xl font-bold text-primary font-serif">
                    {framework}
                  </h3>
                </div>
              </div>

              <div className="space-y-2 font-mono text-xs">
                <label className="block text-outline">Change Framework Preset:</label>
                <select
                  value={framework}
                  onChange={(e) => setFramework(e.target.value)}
                  className="w-full bg-surface doodle-border p-2.5 text-sketch-white focus:outline-none focus:border-primary"
                >
                  <option value="Next.js">Next.js 15 (App Router)</option>
                  <option value="Vite">Vite (React / Vue / Svelte)</option>
                  <option value="Astro">Astro SSG</option>
                  <option value="FastAPI">FastAPI (Python Service)</option>
                  <option value="Static HTML">Static HTML / JS</option>
                </select>
              </div>
            </section>

            {/* Step 3: Build Configuration */}
            <section className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border paper-shadow flex flex-col justify-between transform -rotate-0.5 hover:rotate-0 transition-transform">
              <div>
                <div className="washi-tape-1 -top-3 right-6 bg-tertiary">Step 3</div>
                <h2
                  className="text-2xl font-bold text-sketch-white font-serif mb-6 flex items-center gap-2"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  <span>⚙ Build Config</span>
                </h2>

                <div className="space-y-4 font-mono text-xs">
                  <div>
                    <label className="block text-outline font-bold mb-1">Build Command</label>
                    <input
                      type="text"
                      value={buildCommand}
                      onChange={(e) => setBuildCommand(e.target.value)}
                      className="w-full bg-surface doodle-border p-2.5 text-primary focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-outline font-bold mb-1">Output Directory</label>
                    <input
                      type="text"
                      value={outputDirectory}
                      onChange={(e) => setOutputDirectory(e.target.value)}
                      className="w-full bg-surface doodle-border p-2.5 text-primary focus:outline-none focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-outline font-bold mb-1">Install Command</label>
                    <input
                      type="text"
                      value={installCommand}
                      onChange={(e) => setInstallCommand(e.target.value)}
                      className="w-full bg-surface doodle-border p-2.5 text-primary focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* ========================================================================= */}
          {/* STEP 4: ENVIRONMENT VARIABLES VAULT */}
          {/* ========================================================================= */}
          <section className="p-6 md:p-8 bg-surface-container-high rounded-2xl doodle-border-emerald paper-shadow-lg relative">
            <div className="washi-tape-2 -top-3 right-8 bg-primary">Step 4</div>

            <div className="flex justify-between items-center mb-6">
              <div>
                <h2
                  className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  <SketchLockIcon className="w-5 h-5 text-primary" />
                  <span>Encrypted Secrets Vault</span>
                </h2>
                <p className="text-xs font-mono text-outline mt-1">
                  AES-256 encrypted at rest. Injected ephemerally into the isolated build container.
                </p>
              </div>
            </div>

            {/* Existing Env Vars List */}
            <div className="space-y-3 font-mono text-xs mb-6">
              {envVars.map((item) => {
                const isVisible = showValues[item.id];
                return (
                  <div
                    key={item.id}
                    className="grid grid-cols-[1fr_1.5fr_auto] gap-3 items-center bg-surface p-3 rounded-lg doodle-border"
                  >
                    <span className="text-primary font-bold truncate">{item.key}</span>

                    <div className="flex items-center gap-2 overflow-hidden">
                      <span className="text-on-surface-variant truncate">
                        {isVisible || !item.isSecret ? item.value : "••••••••••••••••••••••••"}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.isSecret && (
                        <button
                          type="button"
                          onClick={() => toggleVisibility(item.id)}
                          className="text-outline hover:text-sketch-white p-1"
                        >
                          {isVisible ? "👁️" : "🔒"}
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleDeleteEnv(item.id)}
                        className="text-error hover:text-red-400 p-1"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Add New Env Var Form */}
            <form onSubmit={handleAddEnv} className="grid grid-cols-1 sm:grid-cols-[1fr_1.5fr_auto] gap-3 font-mono text-xs pt-4 border-t border-outline-variant/40">
              <input
                type="text"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="VARIABLE_NAME"
                className="bg-surface doodle-border p-2.5 text-sketch-white placeholder-outline focus:outline-none focus:border-primary"
              />
              <input
                type="text"
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                placeholder="Value..."
                className="bg-surface doodle-border p-2.5 text-sketch-white placeholder-outline focus:outline-none focus:border-primary"
              />
              <button
                type="submit"
                className="doodle-btn bg-surface hover:bg-surface-variant text-sketch-white font-bold px-4 py-2.5"
              >
                + Add
              </button>
            </form>
          </section>

          {/* ========================================================================= */}
          {/* FINAL DEPLOY ACTION */}
          {/* ========================================================================= */}
          <div className="flex justify-end pt-6 border-t-2 border-outline-variant border-dashed">
            <button
              onClick={handleDeploy}
              disabled={isDeploying}
              className="px-8 py-4 bg-primary text-surface font-mono font-bold text-lg rounded-xl doodle-border-emerald paper-shadow-emerald hover:bg-primary-fixed transition-all transform -rotate-1 hover:rotate-0 flex items-center gap-3 cursor-pointer"
            >
              {isDeploying ? (
                <>
                  <span className="animate-spin">⚙</span>
                  <span>Triggering Pipeline...</span>
                </>
              ) : (
                <>
                  <SketchRocket className="w-6 h-6 text-surface" />
                  <span>Deploy Project ⚡</span>
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
