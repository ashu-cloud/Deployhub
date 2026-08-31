"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DeployHubLogo, SketchRocket, SketchLockIcon, SketchTerminalIcon, SketchSparkle } from "@/components/SketchIcons";
import { createProject, getGithubRepos, bootstrapSession, logout } from "@/lib/api";

interface EnvVar {
  id: string;
  key: string;
  value: string;
  isSecret: boolean;
}

interface GithubRepo {
  id: string;
  name: string;
  full_name: string;
  desc: string;
  updated: string;
  language: string;
}

const FRAMEWORK_PRESETS = [
  {
    id: "Next.js",
    name: "Next.js 15",
    tagline: "App Router, Server Actions & Edge Rendering",
    icon: "▲",
    defaultBuild: "npm run build",
    defaultOut: ".next",
    defaultInstall: "npm install",
    languages: ["TypeScript", "JavaScript"],
  },
  {
    id: "Vite",
    name: "Vite SPA",
    tagline: "React, Vue, Svelte, or Solid modern bundler",
    icon: "⚡",
    defaultBuild: "npm run build",
    defaultOut: "dist",
    defaultInstall: "npm install",
    languages: ["Vue", "TypeScript", "JavaScript"],
  },
  {
    id: "Astro",
    name: "Astro",
    tagline: "Ultra-fast content-driven static & island sites",
    icon: "🚀",
    defaultBuild: "npm run build",
    defaultOut: "dist",
    defaultInstall: "npm install",
    languages: ["Astro", "TypeScript", "JavaScript"],
  },
  {
    id: "FastAPI",
    name: "FastAPI / Python",
    tagline: "High-performance async Python backend service",
    icon: "🐍",
    defaultBuild: "pip install -r requirements.txt",
    defaultOut: "app",
    defaultInstall: "pip install -r requirements.txt",
    languages: ["Python"],
  },
  {
    id: "Static HTML",
    name: "Static HTML / JS",
    tagline: "Raw client-side files served directly at edge",
    icon: "📄",
    defaultBuild: "",
    defaultOut: ".",
    defaultInstall: "",
    languages: ["HTML", "CSS"],
  },
  {
    id: "Node.js",
    name: "Node.js Server",
    tagline: "Express, NestJS, Fastify custom HTTP server",
    icon: "🟢",
    defaultBuild: "npm run build",
    defaultOut: "dist",
    defaultInstall: "npm install",
    languages: ["TypeScript", "JavaScript"],
  },
];

function guessFramework(language: string) {
  if (language === "Python") {
    return { framework: "FastAPI", buildCmd: "pip install -r requirements.txt", outDir: "app", installCmd: "pip install -r requirements.txt" };
  }
  if (language === "TypeScript" || language === "JavaScript") {
    return { framework: "Next.js", buildCmd: "npm run build", outDir: ".next", installCmd: "npm install" };
  }
  if (language === "Vue" || language === "Svelte") {
    return { framework: "Vite", buildCmd: "npm run build", outDir: "dist", installCmd: "npm install" };
  }
  if (language === "Astro") {
    return { framework: "Astro", buildCmd: "npm run build", outDir: "dist", installCmd: "npm install" };
  }
  return { framework: "Static HTML", buildCmd: "", outDir: ".", installCmd: "" };
}

export default function CreateProjectPage() {
  const router = useRouter();

  // Wizard Stage State: 1 | 2 | 3 | 4
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);

  // Repositories State
  const [repos, setRepos] = useState<GithubRepo[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [selectedRepo, setSelectedRepo] = useState<GithubRepo | null>(null);
  const [searchRepo, setSearchRepo] = useState("");

  // Configuration State
  const [framework, setFramework] = useState("Next.js");
  const [buildCommand, setBuildCommand] = useState("npm run build");
  const [outputDirectory, setOutputDirectory] = useState(".next");
  const [installCommand, setInstallCommand] = useState("npm install");
  const [rootDirectory, setRootDirectory] = useState("./");

  // Step Validation Errors
  const [stepError, setStepError] = useState<string | null>(null);

  // Deploy & Pipeline State
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployError, setDeployError] = useState<string | null>(null);

  // Environment Variables Vault
  const [envVars, setEnvVars] = useState<EnvVar[]>([
    { id: "1", key: "NODE_ENV", value: "production", isSecret: false },
  ]);
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [showValues, setShowValues] = useState<{ [id: string]: boolean }>({});

  // Initial Data Fetch
  const fetchRepos = async () => {
    setLoadingRepos(true);
    setStepError(null);
    try {
      const sessionOk = await bootstrapSession();
      console.log("[fetchRepos] bootstrapSession result:", sessionOk);
      if (!sessionOk) {
        setStepError("Session expired. Please log in again.");
        router.push("/login");
        return;
      }
      const data = await getGithubRepos();
      setRepos(data || []);
      if (data && data.length > 0 && !selectedRepo) {
        const first = data[0];
        setSelectedRepo(first);
        const guessed = guessFramework(first.language);
        setFramework(guessed.framework);
        setBuildCommand(guessed.buildCmd);
        setOutputDirectory(guessed.outDir);
        setInstallCommand(guessed.installCmd);
      }
    } catch (err) {
      console.error("Failed to load repos:", err);
    } finally {
      setLoadingRepos(false);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  const handleSelectRepo = (repo: GithubRepo) => {
    setSelectedRepo(repo);
    setStepError(null);
    const guessed = guessFramework(repo.language);
    setFramework(guessed.framework);
    setBuildCommand(guessed.buildCmd);
    setOutputDirectory(guessed.outDir);
    setInstallCommand(guessed.installCmd);
  };

  const handleSelectFrameworkPreset = (preset: typeof FRAMEWORK_PRESETS[0]) => {
    setFramework(preset.id);
    setBuildCommand(preset.defaultBuild);
    setOutputDirectory(preset.defaultOut);
    setInstallCommand(preset.defaultInstall);
    setStepError(null);
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

  // Step Validation & Navigation
  const goToNextStep = () => {
    setStepError(null);

    if (currentStep === 1) {
      if (!selectedRepo) {
        setStepError("Please select a GitHub repository from the list before proceeding.");
        return;
      }
      setCurrentStep(2);
    } else if (currentStep === 2) {
      if (!framework.trim()) {
        setStepError("Please select or specify a framework preset.");
        return;
      }
      setCurrentStep(3);
    } else if (currentStep === 3) {
      if (!buildCommand.trim() && framework !== "Static HTML") {
        setStepError("Build Command is required. For static apps with no build step, select the 'Static HTML' preset.");
        return;
      }
      if (!outputDirectory.trim()) {
        setStepError("Output Directory is required (e.g. '.next', 'dist', 'public', or '.').");
        return;
      }
      setCurrentStep(4);
    }
  };

  const goToPrevStep = () => {
    setStepError(null);
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as 1 | 2 | 3 | 4);
    }
  };

  const handleDeploy = async () => {
    if (!selectedRepo) {
      setStepError("No repository selected.");
      setCurrentStep(1);
      return;
    }

    setIsDeploying(true);
    setDeployError(null);

    // Always refresh the session token right before deploying
    console.log("[handleDeploy] Refreshing session before deploy...");
    const sessionOk = await bootstrapSession();
    console.log("[handleDeploy] Session bootstrap result:", sessionOk);
    
    // Log the current in-memory token state (first 20 chars only for security)
    const { getAuthToken } = await import("@/lib/api");
    const token = getAuthToken();
    console.log("[handleDeploy] inMemoryAuthToken exists:", !!token);
    console.log("[handleDeploy] token preview:", token ? token.substring(0, 20) + "..." : "NULL");

    if (!sessionOk || !token) {
      setDeployError("Your session expired. Please log in again.");
      setIsDeploying(false);
      setTimeout(() => router.push("/login"), 2000);
      return;
    }

    const envMap: Record<string, string> = {};
    envVars.forEach((ev) => {
      if (ev.key.trim()) {
        envMap[ev.key.trim()] = ev.value;
      }
    });

    const repoUrl = selectedRepo.full_name
      ? `https://github.com/${selectedRepo.full_name}`
      : `https://github.com/deployhub/${selectedRepo.name}`;

    console.log("[handleDeploy] Calling createProject with:", {
      repo_name: selectedRepo.name,
      repo_url: repoUrl,
      framework,
    });

    try {
      const project = await createProject({
        repo_name: selectedRepo.name,
        repo_url: repoUrl,
        framework,
        env_vars: envMap,
      });
      console.log("[handleDeploy] Project created successfully:", project);
      router.push(`/${project.id}`);
    } catch (err) {
      console.error("[handleDeploy] createProject failed:", err);
      setDeployError(err instanceof Error ? err.message : "Could not create project");
      setIsDeploying(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  const filteredRepos = repos.filter((r) =>
    r.name.toLowerCase().includes(searchRepo.toLowerCase()) ||
    (r.desc && r.desc.toLowerCase().includes(searchRepo.toLowerCase())) ||
    (r.language && r.language.toLowerCase().includes(searchRepo.toLowerCase()))
  );

  const stepsMeta = [
    { num: 1, label: "Repository", icon: "📁" },
    { num: 2, label: "Framework", icon: "⚡" },
    { num: 3, label: "Build Config", icon: "⚙️" },
    { num: 4, label: "Review & Deploy", icon: "🚀" },
  ];

  return (
    <div className="bg-background dot-grid text-on-background font-body-md min-h-screen flex flex-col md:flex-row overflow-x-hidden paper-texture">
      {/* ========================================================================= */}
      {/* SIDEBAR NAVIGATION (Desktop) */}
      {/* ========================================================================= */}
      <aside className="hidden md:flex flex-col min-h-screen self-stretch w-64 bg-surface-container-low border-r-2 border-outline-variant p-6 sticky top-0 shrink-0 z-40 relative">
        <div className="mb-6">
          <Link href="/" className="inline-block wiggle">
            <DeployHubLogo className="h-9" />
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6 doodle-border p-3 bg-surface rotate-1">
          <div className="w-9 h-9 rounded-full bg-primary/20 border-2 border-primary text-primary flex items-center justify-center font-mono font-bold text-sm shrink-0">
            AP
          </div>
          <div className="overflow-hidden">
            <h2 className="text-xs font-mono font-bold text-sketch-white truncate">DeployHub Account</h2>
            <p className="text-[10px] font-mono text-outline truncate">Connected to GitHub</p>
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
            <div className="w-full text-left px-3.5 py-2 rounded-lg flex items-center gap-3 bg-surface-container-high text-primary font-bold doodle-border paper-shadow">
              <span>🚀</span>
              <span>New Deployment (Step {currentStep}/4)</span>
            </div>
          </li>
        </ul>

        <div className="mt-auto border-t-2 border-outline-variant border-dashed pt-4 font-mono text-xs text-outline space-y-3">
          <Link href="/dashboard" className="flex items-center gap-2 hover:text-primary transition-colors">
            <span>←</span>
            <span>Back to Dashboard</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full doodle-btn bg-surface hover:bg-surface-container-high text-yellow-400 font-mono font-bold text-xs py-2 px-3 flex items-center justify-center gap-2 paper-shadow transition-all text-center border-yellow-400/40 hover:border-yellow-400 cursor-pointer"
          >
            <span>🚪</span>
            <span>Log Out</span>
          </button>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MAIN CONTENT CANVAS */}
      {/* ========================================================================= */}
      <main className="flex-1 p-6 md:p-12 max-w-5xl mx-auto w-full relative">
        {/* Header Title */}
        <div className="mb-8 relative">
          <div className="transform -rotate-1 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1
                className="text-4xl md:text-5xl font-extrabold text-sketch-white font-serif tracking-tight"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                Import <span className="text-primary sketch-underline">Project.</span>
              </h1>
              <p className="font-mono text-xs text-on-surface-variant max-w-xl mt-2 leading-relaxed">
                Connect your repository, configure build runners, and launch live edge deployments.
              </p>
            </div>

            {/* Step Counter Badge */}
            <div className="inline-flex items-center gap-2 bg-surface-container doodle-border px-3.5 py-1.5 font-mono text-xs text-sketch-white">
              <span className="text-primary font-bold">Step {currentStep} of 4:</span>
              <span>{stepsMeta[currentStep - 1].label}</span>
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* MULTI-STEP PROGRESS STEPPER */}
        {/* ========================================================================= */}
        <div className="mb-10 bg-surface-container-low doodle-border p-4 rounded-xl paper-shadow">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            {stepsMeta.map((s) => {
              const isActive = s.num === currentStep;
              const isPassed = s.num < currentStep;
              return (
                <button
                  key={s.num}
                  type="button"
                  onClick={() => {
                    if (isPassed) {
                      setStepError(null);
                      setCurrentStep(s.num as 1 | 2 | 3 | 4);
                    }
                  }}
                  disabled={!isPassed && !isActive}
                  className={`flex items-center gap-2.5 p-2.5 rounded-lg border transition-all text-left ${
                    isActive
                      ? "bg-primary/20 border-primary text-sketch-white font-bold paper-shadow-emerald"
                      : isPassed
                      ? "bg-surface border-primary/40 text-primary cursor-pointer hover:bg-surface-container"
                      : "bg-surface/50 border-outline-variant/30 text-outline cursor-not-allowed opacity-60"
                  }`}
                >
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                      isActive
                        ? "bg-primary text-surface"
                        : isPassed
                        ? "bg-primary/20 text-primary border border-primary"
                        : "bg-surface-container text-outline border border-outline-variant"
                    }`}
                  >
                    {isPassed ? "✓" : s.num}
                  </span>
                  <span className="truncate">{s.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* INLINE VALIDATION ERROR ALERT */}
        {/* ========================================================================= */}
        {stepError && (
          <div className="mb-6 p-4 bg-error/15 doodle-border-error rounded-xl text-error font-mono text-xs flex items-center gap-3 animate-bounce">
            <span className="text-base">⚠️</span>
            <span>{stepError}</span>
          </div>
        )}

        {deployError && (
          <div className="mb-6 p-4 bg-error/15 doodle-border-error rounded-xl text-error font-mono text-xs flex items-center gap-3">
            <span className="text-base">❌</span>
            <span>{deployError}</span>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STAGE 1: REPOSITORY PICKER */}
        {/* ========================================================================= */}
        {currentStep === 1 && (
          <section className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border relative paper-shadow animate-fadeIn">
            <div className="washi-tape-1 -top-3 right-8 bg-tertiary">Step 1</div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2
                  className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  <span>📁 Connect Repository</span>
                </h2>
                <p className="text-xs font-mono text-outline mt-1">
                  Select a repository from your connected GitHub account to import.
                </p>
              </div>

              <button
                type="button"
                onClick={fetchRepos}
                className="doodle-btn bg-surface hover:bg-surface-container-high text-sketch-white font-mono text-xs px-3.5 py-2 flex items-center gap-2 self-start cursor-pointer"
              >
                <span>🔄</span>
                <span>Refresh Repos</span>
              </button>
            </div>

            {/* Search Bar */}
            <div className="relative mb-6">
              <span className="absolute left-3 top-2.5 text-outline text-xs">🔍</span>
              <input
                type="text"
                value={searchRepo}
                onChange={(e) => setSearchRepo(e.target.value)}
                placeholder="Search your GitHub repositories..."
                className="w-full bg-surface doodle-border pl-9 pr-4 py-2.5 text-xs font-mono text-sketch-white placeholder-outline focus:outline-none focus:border-primary"
              />
            </div>

            {/* Repository List */}
            <div className="space-y-3 font-mono text-xs max-h-96 overflow-y-auto terminal-scroll pr-2">
              {loadingRepos ? (
                <div className="space-y-3 py-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="p-4 rounded-xl doodle-border bg-surface animate-pulse flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="h-4 w-48 bg-outline-variant/30 rounded"></div>
                        <div className="h-3 w-64 bg-outline-variant/20 rounded"></div>
                      </div>
                      <div className="h-8 w-20 bg-outline-variant/30 rounded"></div>
                    </div>
                  ))}
                  <p className="text-center py-2 text-outline text-xs animate-pulse">
                    Connecting to GitHub API & retrieving your repositories...
                  </p>
                </div>
              ) : filteredRepos.length === 0 ? (
                <div className="text-center py-12 px-6 bg-surface rounded-xl doodle-border border-dashed space-y-3">
                  <span className="text-3xl">📂</span>
                  <h3 className="text-sm font-bold text-sketch-white">No Repositories Found</h3>
                  <p className="text-outline text-xs max-w-md mx-auto">
                    {searchRepo
                      ? `No repositories match "${searchRepo}". Try clearing the search.`
                      : "We couldn't find any repositories on this GitHub account. Please ensure you granted repository permissions when logging in."}
                  </p>
                  <div className="pt-2">
                    <a
                      href="/api/v1/auth/github"
                      className="doodle-btn bg-primary text-surface font-bold px-4 py-2 text-xs inline-flex items-center gap-2"
                    >
                      <span>🔑</span>
                      <span>Re-Authenticate with GitHub</span>
                    </a>
                  </div>
                </div>
              ) : (
                filteredRepos.map((repo) => {
                  const isSelected = selectedRepo?.id === repo.id;
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
                      <div className="flex items-center gap-3.5 overflow-hidden pr-3">
                        <div className="w-9 h-9 rounded-lg bg-surface-container border border-outline-variant flex items-center justify-center font-bold text-primary shrink-0">
                          &lt;/&gt;
                        </div>
                        <div className="overflow-hidden">
                          <div className="font-bold text-sketch-white flex items-center gap-2 truncate">
                            <span className="truncate">{repo.full_name || repo.name}</span>
                            {isSelected && (
                              <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.2 rounded border border-primary/40 shrink-0">
                                Selected ✓
                              </span>
                            )}
                          </div>
                          <p className="text-outline text-[11px] mt-0.5 truncate">
                            {repo.desc || "No description provided"}
                          </p>
                          <div className="flex items-center gap-3 text-outline text-[9px] mt-1 opacity-80">
                            {repo.language && <span className="text-primary font-bold">{repo.language}</span>}
                            {repo.updated && <span>Updated {new Date(repo.updated).toLocaleDateString()}</span>}
                          </div>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectRepo(repo);
                        }}
                        className={`px-3 py-1.5 rounded font-bold transition-colors shrink-0 ${
                          isSelected
                            ? "bg-primary text-surface"
                            : "doodle-btn bg-surface text-outline hover:text-sketch-white"
                        }`}
                      >
                        {isSelected ? "Selected ✓" : "Select"}
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            {/* Selected Repo Preview Note */}
            {selectedRepo && (
              <div className="mt-6 p-3 bg-surface rounded-lg border border-primary/40 flex items-center justify-between font-mono text-xs">
                <div className="flex items-center gap-2 text-sketch-white">
                  <span className="text-primary">✓</span>
                  <span>Ready to import: <strong>{selectedRepo.full_name || selectedRepo.name}</strong></span>
                </div>
                <span className="text-outline text-[10px]">Detected: {selectedRepo.language || "Unknown"}</span>
              </div>
            )}

            {/* Step 1 Navigation */}
            <div className="flex justify-between items-center pt-8 mt-6 border-t-2 border-outline-variant border-dashed">
              <Link
                href="/dashboard"
                className="doodle-btn bg-surface hover:bg-surface-container-high text-outline hover:text-sketch-white font-mono text-xs px-4 py-2.5"
              >
                ← Cancel
              </Link>
              <button
                type="button"
                onClick={goToNextStep}
                disabled={!selectedRepo}
                className="doodle-btn bg-primary text-surface font-mono font-bold text-xs px-6 py-2.5 flex items-center gap-2 paper-shadow hover:bg-primary-fixed disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <span>Next: Framework</span>
                <span>→</span>
              </button>
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* STAGE 2: FRAMEWORK SELECTION */}
        {/* ========================================================================= */}
        {currentStep === 2 && (
          <section className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border relative paper-shadow animate-fadeIn">
            <div className="washi-tape-2 -top-3 right-8 bg-primary">Step 2</div>

            <div className="mb-6">
              <h2
                className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                <span>⚡ Framework Preset</span>
              </h2>
              <p className="text-xs font-mono text-outline mt-1">
                DeployHub configures optimized container builders and artifact bundlers based on the framework.
              </p>
            </div>

            {/* Selected Repository Card */}
            {selectedRepo && (
              <div className="mb-6 p-4 bg-surface rounded-xl doodle-border flex items-center justify-between font-mono text-xs">
                <div className="flex items-center gap-3">
                  <span className="text-primary text-lg">📁</span>
                  <div>
                    <div className="font-bold text-sketch-white">{selectedRepo.full_name || selectedRepo.name}</div>
                    <div className="text-outline text-[11px]">Primary Codebase: {selectedRepo.language || "Unknown"}</div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="text-primary hover:underline text-xs cursor-pointer"
                >
                  Change Repo
                </button>
              </div>
            )}

            {/* Framework Preset Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {FRAMEWORK_PRESETS.map((preset) => {
                const isSelected = framework === preset.id;
                const isDetected = selectedRepo?.language && preset.languages.includes(selectedRepo.language);
                return (
                  <div
                    key={preset.id}
                    onClick={() => handleSelectFrameworkPreset(preset)}
                    className={`p-5 rounded-xl doodle-border transition-all cursor-pointer flex flex-col justify-between ${
                      isSelected
                        ? "bg-surface-container-high border-primary paper-shadow-emerald -translate-y-1"
                        : "bg-surface hover:bg-surface-container-high border-outline-variant/50"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-2xl">{preset.icon}</span>
                        {isDetected && (
                          <span className="text-[10px] bg-tertiary/15 text-tertiary border border-tertiary/40 px-2 py-0.5 rounded font-mono">
                            Auto-Detected
                          </span>
                        )}
                      </div>
                      <h3 className="font-bold text-sketch-white font-mono text-sm mb-1">{preset.name}</h3>
                      <p className="text-outline text-xs leading-relaxed">{preset.tagline}</p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-center justify-between font-mono text-[10px] text-outline">
                      <span>Out: <code className="text-primary">{preset.defaultOut || "./"}</code></span>
                      <span className={isSelected ? "text-primary font-bold" : ""}>
                        {isSelected ? "Selected ✓" : "Choose"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Custom Dropdown Option */}
            <div className="p-4 bg-surface rounded-xl doodle-border font-mono text-xs space-y-2">
              <label className="block text-outline">Or customize framework manually:</label>
              <input
                type="text"
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                placeholder="e.g. Next.js, Vite, Nuxt, Remix, Django..."
                className="w-full bg-surface-container doodle-border p-2.5 text-sketch-white focus:outline-none focus:border-primary"
              />
            </div>

            {/* Step 2 Navigation */}
            <div className="flex justify-between items-center pt-8 mt-6 border-t-2 border-outline-variant border-dashed">
              <button
                type="button"
                onClick={goToPrevStep}
                className="doodle-btn bg-surface hover:bg-surface-container-high text-outline hover:text-sketch-white font-mono text-xs px-4 py-2.5 flex items-center gap-2 cursor-pointer"
              >
                <span>←</span>
                <span>Back: Repository</span>
              </button>
              <button
                type="button"
                onClick={goToNextStep}
                className="doodle-btn bg-primary text-surface font-mono font-bold text-xs px-6 py-2.5 flex items-center gap-2 paper-shadow hover:bg-primary-fixed cursor-pointer"
              >
                <span>Next: Build Settings</span>
                <span>→</span>
              </button>
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* STAGE 3: BUILD & OUTPUT CONFIGURATION */}
        {/* ========================================================================= */}
        {currentStep === 3 && (
          <section className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border relative paper-shadow animate-fadeIn">
            <div className="washi-tape-1 -top-3 right-8 bg-tertiary">Step 3</div>

            <div className="mb-6">
              <h2
                className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                <span>⚙️ Build & Output Settings</span>
              </h2>
              <p className="text-xs font-mono text-outline mt-1">
                Specify the build commands and output folder where your artifacts will be compiled.
              </p>
            </div>

            {/* Framework & Repo Reminder */}
            <div className="mb-6 p-4 bg-surface rounded-xl doodle-border flex items-center justify-between font-mono text-xs">
              <div>
                <span className="text-outline">Preset: </span>
                <span className="text-primary font-bold">{framework}</span>
                <span className="text-outline mx-2">•</span>
                <span className="text-outline">Repo: </span>
                <span className="text-sketch-white font-bold">{selectedRepo?.name}</span>
              </div>
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="text-primary hover:underline text-xs cursor-pointer"
              >
                Change Framework
              </button>
            </div>

            {/* Inputs Form */}
            <div className="space-y-5 font-mono text-xs">
              <div>
                <label className="block text-sketch-white font-bold mb-1.5 flex items-center justify-between">
                  <span>Build Command <span className="text-primary">*</span></span>
                  <span className="text-outline font-normal text-[11px]">Command executed in Docker runner</span>
                </label>
                <input
                  type="text"
                  value={buildCommand}
                  onChange={(e) => {
                    setBuildCommand(e.target.value);
                    setStepError(null);
                  }}
                  placeholder="e.g. npm run build, yarn build, cargo build"
                  className="w-full bg-surface doodle-border p-3 text-primary focus:outline-none focus:border-primary placeholder-outline"
                />
              </div>

              <div>
                <label className="block text-sketch-white font-bold mb-1.5 flex items-center justify-between">
                  <span>Output Directory <span className="text-primary">*</span></span>
                  <span className="text-outline font-normal text-[11px]">Directory containing compiled bundle to serve</span>
                </label>
                <input
                  type="text"
                  value={outputDirectory}
                  onChange={(e) => {
                    setOutputDirectory(e.target.value);
                    setStepError(null);
                  }}
                  placeholder="e.g. .next, dist, build, public, or ."
                  className="w-full bg-surface doodle-border p-3 text-primary focus:outline-none focus:border-primary placeholder-outline"
                />
              </div>

              <div>
                <label className="block text-sketch-white font-bold mb-1.5 flex items-center justify-between">
                  <span>Install Command</span>
                  <span className="text-outline font-normal text-[11px]">Dependency resolution step</span>
                </label>
                <input
                  type="text"
                  value={installCommand}
                  onChange={(e) => setInstallCommand(e.target.value)}
                  placeholder="e.g. npm install, pnpm install, yarn"
                  className="w-full bg-surface doodle-border p-3 text-sketch-white focus:outline-none focus:border-primary placeholder-outline"
                />
              </div>

              <div>
                <label className="block text-sketch-white font-bold mb-1.5 flex items-center justify-between">
                  <span>Root Directory</span>
                  <span className="text-outline font-normal text-[11px]">Base folder in repo</span>
                </label>
                <input
                  type="text"
                  value={rootDirectory}
                  onChange={(e) => setRootDirectory(e.target.value)}
                  placeholder="./"
                  className="w-full bg-surface doodle-border p-3 text-sketch-white focus:outline-none focus:border-primary placeholder-outline"
                />
              </div>
            </div>

            {/* Step 3 Navigation */}
            <div className="flex justify-between items-center pt-8 mt-6 border-t-2 border-outline-variant border-dashed">
              <button
                type="button"
                onClick={goToPrevStep}
                className="doodle-btn bg-surface hover:bg-surface-container-high text-outline hover:text-sketch-white font-mono text-xs px-4 py-2.5 flex items-center gap-2 cursor-pointer"
              >
                <span>←</span>
                <span>Back: Framework</span>
              </button>
              <button
                type="button"
                onClick={goToNextStep}
                className="doodle-btn bg-primary text-surface font-mono font-bold text-xs px-6 py-2.5 flex items-center gap-2 paper-shadow hover:bg-primary-fixed cursor-pointer"
              >
                <span>Next: Review & Deploy</span>
                <span>→</span>
              </button>
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* STAGE 4: SECRETS VAULT & FINAL REVIEW */}
        {/* ========================================================================= */}
        {currentStep === 4 && (
          <section className="space-y-8 animate-fadeIn">
            {/* Review Summary Card */}
            <div className="p-6 md:p-8 bg-surface-container rounded-2xl doodle-border relative paper-shadow">
              <div className="washi-tape-2 -top-3 right-8 bg-primary">Step 4</div>

              <div className="mb-6">
                <h2
                  className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  <span>📋 Review Deployment Specification</span>
                </h2>
                <p className="text-xs font-mono text-outline mt-1">
                  Double check all build settings before pushing to the automated Kafka orchestration queue.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
                <div className="p-4 bg-surface rounded-xl doodle-border">
                  <span className="text-outline block text-[10px] uppercase tracking-wider mb-1">Target Repository</span>
                  <span className="font-bold text-sketch-white truncate block">{selectedRepo?.name}</span>
                  <span className="text-[10px] text-outline truncate block">{selectedRepo?.full_name}</span>
                </div>

                <div className="p-4 bg-surface rounded-xl doodle-border">
                  <span className="text-outline block text-[10px] uppercase tracking-wider mb-1">Framework</span>
                  <span className="font-bold text-primary block">{framework}</span>
                  <span className="text-[10px] text-outline block">Auto-optimized build</span>
                </div>

                <div className="p-4 bg-surface rounded-xl doodle-border">
                  <span className="text-outline block text-[10px] uppercase tracking-wider mb-1">Build Command</span>
                  <code className="font-bold text-primary block truncate">{buildCommand || "None"}</code>
                  <span className="text-[10px] text-outline block">Output: {outputDirectory}</span>
                </div>

                <div className="p-4 bg-surface rounded-xl doodle-border">
                  <span className="text-outline block text-[10px] uppercase tracking-wider mb-1">Target Branch</span>
                  <span className="font-bold text-sketch-white block">main</span>
                  <span className="text-[10px] text-tertiary block">Continuous Deploy Active</span>
                </div>
              </div>
            </div>

            {/* Encrypted Secrets Vault Section */}
            <div className="p-6 md:p-8 bg-surface-container-high rounded-2xl doodle-border-emerald paper-shadow-lg relative">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3
                    className="text-2xl font-bold text-sketch-white font-serif flex items-center gap-2"
                    style={{ fontFamily: "var(--font-bricolage)" }}
                  >
                    <SketchLockIcon className="w-5 h-5 text-primary" />
                    <span>Encrypted Environment Secrets</span>
                  </h3>
                  <p className="text-xs font-mono text-outline mt-1">
                    AES-256 encrypted at rest. Injected ephemerally into isolated Docker containers during build & execution.
                  </p>
                </div>
              </div>

              {/* Existing Env Vars List */}
              <div className="space-y-3 font-mono text-xs mb-6">
                {envVars.length === 0 ? (
                  <div className="p-4 bg-surface rounded-lg doodle-border text-center text-outline">
                    No custom environment variables added yet. Add one below if required.
                  </div>
                ) : (
                  envVars.map((item) => {
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
                              className="text-outline hover:text-sketch-white p-1 cursor-pointer"
                              title={isVisible ? "Hide secret" : "Reveal secret"}
                            >
                              {isVisible ? "👁️" : "🔒"}
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleDeleteEnv(item.id)}
                            className="text-error hover:text-red-400 p-1 cursor-pointer"
                            title="Delete variable"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Add New Env Var Form */}
              <form onSubmit={handleAddEnv} className="grid grid-cols-1 sm:grid-cols-[1fr_1.5fr_auto] gap-3 font-mono text-xs pt-4 border-t border-outline-variant/40">
                <input
                  type="text"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="VARIABLE_NAME"
                  className="bg-surface doodle-border p-2.5 text-sketch-white placeholder-outline focus:outline-none focus:border-primary uppercase"
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
                  className="doodle-btn bg-surface hover:bg-surface-variant text-sketch-white font-bold px-4 py-2.5 cursor-pointer"
                >
                  + Add Secret
                </button>
              </form>
            </div>

            {/* Final Action Navigation */}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t-2 border-outline-variant border-dashed">
              <button
                type="button"
                onClick={goToPrevStep}
                disabled={isDeploying}
                className="doodle-btn bg-surface hover:bg-surface-container-high text-outline hover:text-sketch-white font-mono text-xs px-5 py-3.5 flex items-center gap-2 cursor-pointer"
              >
                <span>←</span>
                <span>Back: Build Config</span>
              </button>

              <button
                type="button"
                onClick={handleDeploy}
                disabled={isDeploying}
                className="w-full sm:w-auto px-8 py-4 bg-primary text-surface font-mono font-bold text-lg rounded-xl doodle-border-emerald paper-shadow-emerald hover:bg-primary-fixed transition-all transform -rotate-1 hover:rotate-0 flex items-center justify-center gap-3 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDeploying ? (
                  <>
                    <span className="animate-spin text-xl">⚙</span>
                    <span>Triggering Kafka Pipeline...</span>
                  </>
                ) : (
                  <>
                    <SketchRocket className="w-6 h-6 text-surface" />
                    <span>Deploy Project ⚡</span>
                  </>
                )}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
