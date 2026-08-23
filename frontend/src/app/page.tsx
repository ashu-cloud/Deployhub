import WebGLBackground from "@/components/WebGLBackground";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  DeployHubLogo,
  SketchRocket,
  SketchTerminalIcon,
  SketchUsersIcon,
  SketchLockIcon,
  SketchGlobeIcon,
  SketchBoltIcon,
  SketchSparkle,
  SketchArrowCurved,
} from "@/components/SketchIcons";
import { InteractiveHeroSandbox } from "@/components/InteractiveHeroSandbox";
// import { ArchitectureMap } from "@/components/ArchitectureMap";
import { InteractiveRollbackDemo } from "@/components/InteractiveRollbackDemo";
import { InteractiveFAQ } from "@/components/InteractiveFAQ";

export default function Home() {
  return (
    <>
      <WebGLBackground />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />

        <main className="flex-grow flex flex-col items-center pt-12 pb-24 px-4 sm:px-6 md:px-12 relative overflow-hidden">
          {/* Floating Aesthetic Doodles (Absolute) */}
          <div
            className="absolute top-16 left-8 text-tertiary opacity-80 wiggle animate-fade-up stagger-2 pointer-events-none"
            style={{ fontSize: "2.5rem" }}
          >
            ✦
          </div>
          <div
            className="absolute top-44 right-12 text-outline opacity-40 wiggle animate-fade-up stagger-3 pointer-events-none"
            style={{ fontSize: "3.5rem" }}
          >
            ✧
          </div>
          <div
            className="absolute top-72 left-1/5 text-primary opacity-50 wiggle animate-fade-up stagger-4 pointer-events-none"
            style={{ fontSize: "2rem" }}
          >
            ✶
          </div>

          {/* ========================================================================= */}
          {/* 1. HERO SECTION */}
          {/* ========================================================================= */}
          <section className="max-w-5xl mx-auto text-center flex flex-col items-center gap-6 relative w-full mb-12 animate-fade-up stagger-2">
            {/* Top Announcement Pill */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-surface-container border border-outline-variant/60 rounded-full font-mono text-xs text-on-surface-variant hover:border-primary/60 transition-colors cursor-pointer group">
              <span className="text-primary font-bold">★ v1.0.0 is live</span>
              <span className="text-outline">·</span>
              <span className="text-sketch-white">Autonomous Cloud Platform</span>
              <span className="text-tertiary group-hover:translate-x-0.5 transition-transform">→</span>
            </div>

            {/* Central Logo Presentation with Hand-drawn Doodle Box & Arrow */}
            <div className="relative inline-block my-2 group">
              <div className="absolute inset-0 bg-surface-variant/30 rotate-3 doodle-border scale-110 -z-10 transition-transform group-hover:rotate-6"></div>
              <div className="bg-surface p-4 md:p-6 doodle-border paper-shadow flex items-center justify-center transform -rotate-1 group-hover:rotate-0 transition-transform">
                <DeployHubLogo className="h-14 md:h-18" showText={false} />
              </div>

              {/* Hand-drawn Arrow pointing to logo */}
              <div className="absolute -right-28 -bottom-10 hidden sm:block pointer-events-none text-tertiary">
                <SketchArrowCurved className="w-24 h-24 text-tertiary wiggle" />
                <span className="font-mono text-xs font-bold text-tertiary bg-surface px-2 py-0.5 doodle-border paper-shadow -rotate-6 block -mt-4">
                  0s config!
                </span>
              </div>
            </div>

            {/* Main Headline */}
            <h1
              className="text-5xl sm:text-7xl md:text-8xl lg:text-[96px] font-extrabold leading-[1.05] text-sketch-white max-w-5xl tracking-tight mt-4 font-serif"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              Structure that adapts to <br className="hidden sm:inline" />
              <span className="text-primary sketch-underline italic">your</span> thinking
            </h1>

            {/* Subtitle */}
            <p className="font-body-md text-lg sm:text-xl md:text-2xl text-on-surface-variant max-w-3xl mt-2 leading-relaxed">
              Deployments shouldn't be rigid. Push code to GitHub, and DeployHub automatically isolates containers, streams live build logs, and serves atomic rollbacks in <span className="text-primary font-mono font-bold">&lt; 350ms</span>.
            </p>

            {/* Dual Hero Action Buttons */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-4 animate-fade-up stagger-3">
              <a
                href="#demo"
                className="bg-sketch-white text-surface font-mono font-bold text-base sm:text-lg px-8 py-4 hover:bg-gray-200 transition-all flex items-center gap-3 doodle-border paper-shadow transform -rotate-1 hover:rotate-0 hover:-translate-y-0.5"
              >
                <SketchRocket className="w-5 h-5 text-surface" />
                <span>Start Deploying Free</span>
              </a>

              <a
                href="#features"
                className="doodle-btn bg-surface-container font-mono font-bold text-base sm:text-lg px-6 py-4 text-sketch-white hover:bg-surface-variant transition-all paper-shadow flex items-center gap-2"
              >
                <span>Explore Features</span>
                <span className="text-tertiary">✦</span>
              </a>
            </div>

            {/* Social proof line */}
            <div className="flex items-center gap-4 text-xs font-mono text-outline mt-4">
              <div className="flex -space-x-1.5">
                {["#10b981", "#FF9900", "#0099FF", "#ffb3b0"].map((c, i) => (
                  <div
                    key={i}
                    className="w-5 h-5 rounded-full border border-surface flex items-center justify-center text-[9px] font-bold text-surface"
                    style={{ backgroundColor: c }}
                  >
                    ✓
                  </div>
                ))}
              </div>
              <span>Loved by 2,000+ indie hackers & fast-moving engineering teams</span>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 2. INTERACTIVE LIVE HERO SANDBOX (#demo) */}
          {/* ========================================================================= */}
          <section id="demo" className="w-full scroll-mt-24">
            <InteractiveHeroSandbox />
          </section>

          {/* ========================================================================= */}
          {/* 3. PERFORMANCE & PLATFORM STATS STRIP (#benchmarks) */}
          {/* ========================================================================= */}
          <section id="benchmarks" className="w-full max-w-6xl mx-auto my-16 grid grid-cols-2 md:grid-cols-4 gap-4 px-2 scroll-mt-28">
            {[
              { label: "Atomic Rollback", value: "< 350ms", note: "Zero container re-builds" },
              { label: "Pipeline Uptime", value: "99.99%", note: "Kafka at-least-once delivery" },
              { label: "Deployment Storage", value: "MinIO S3", note: "100% immutable artifacts" },
              { label: "Config Overhead", value: "0 Seconds", note: "Auto-detects framework" },
            ].map((stat, idx) => (
              <div
                key={idx}
                className="bg-surface-container p-5 rounded-xl doodle-border paper-shadow flex flex-col justify-center text-center group hover:border-primary/60 transition-colors"
              >
                <span className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-primary font-mono">
                  {stat.value}
                </span>
                <span className="font-bold text-sketch-white text-sm mt-1 font-serif">
                  {stat.label}
                </span>
                <span className="text-[11px] font-mono text-outline mt-0.5">
                  {stat.note}
                </span>
              </div>
            ))}
          </section>

          {/* ========================================================================= */}
          {/* 4. FEATURE BENTO GRID (6 RICH CARDS) (#features) */}
          {/* ========================================================================= */}
          <section id="features" className="w-full max-w-6xl mx-auto my-16 scroll-mt-28">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container border border-outline-variant/60 rounded-full font-mono text-xs text-primary mb-3">
                <SketchSparkle className="w-4 h-4 text-tertiary" />
                <span>Everything Included</span>
              </div>
              <h2
                className="text-4xl md:text-5xl font-bold text-sketch-white tracking-tight font-serif"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                Crafted for Speed, Resilient by Design
              </h2>
              <p className="text-on-surface-variant font-body-md text-lg max-w-2xl mx-auto mt-3">
                No complex YAML hell or fragile CI/CD scripts. DeployHub manages the entire lifecycle from commit to live traffic.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Card 1: Instant Git Deploys */}
              <div className="bg-surface-container p-7 doodle-border paper-shadow relative transform -rotate-1 hover:rotate-0 hover:-translate-y-1 transition-all duration-300 flex flex-col">
                <div className="washi-tape-1 bg-primary"></div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-primary/20 text-primary flex items-center justify-center doodle-border">
                    <SketchRocket className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-2xl text-sketch-white font-serif">Instant Deploys</h3>
                </div>
                <p className="text-on-surface-variant text-sm flex-grow">
                  Push code to GitHub and watch it go live instantly. Webhook triggers are cryptographically verified and queued with zero drop rate.
                </p>
                {/* Mock UI snippet */}
                <div className="mt-6 bg-surface-dim p-4 doodle-border font-mono text-xs text-left">
                  <div className="flex justify-between items-center border-b border-outline-variant/40 pb-2 mb-2">
                    <span className="text-primary font-bold">git push origin main</span>
                    <span className="text-outline">12s ago</span>
                  </div>
                  <div className="text-sketch-white flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-primary animate-pulse"></span>
                    <span>Building Next.js v15.2...</span>
                  </div>
                  <div className="text-primary mt-1 font-bold">✓ Subdomain Ready</div>
                </div>
              </div>

              {/* Card 2: Interactive Logs + AI Root Cause */}
              <div className="bg-surface-container-high p-7 doodle-border paper-shadow-orange relative transform translate-y-2 rotate-1 hover:rotate-0 hover:-translate-y-1 transition-all duration-300 flex flex-col">
                <div className="washi-tape-2 bg-tertiary"></div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-tertiary/20 text-tertiary flex items-center justify-center doodle-border">
                    <SketchTerminalIcon className="w-5 h-5 text-tertiary" />
                  </div>
                  <h3 className="font-bold text-2xl text-sketch-white font-serif">Live Streaming Logs</h3>
                </div>
                <p className="text-on-surface-variant text-sm flex-grow">
                  Watch stdout/stderr stream in real-time over persistent WebSockets. Built-in AI failure diagnosis highlights root causes automatically.
                </p>
                {/* Mock UI snippet */}
                <div className="mt-6 bg-surface-dim p-4 doodle-border font-mono text-xs text-left">
                  <div className="text-outline mb-1">&gt; tail -f build.log</div>
                  <div className="text-error font-bold">[ERR] Missing dependency @types/react</div>
                  <div className="text-surface mt-2 bg-tertiary p-1.5 rounded font-bold text-[10px] transform -rotate-1">
                    AI Fix: Add &apos;@types/react&apos; to devDependencies
                  </div>
                </div>
              </div>

              {/* Card 3: Team Previews & Collab */}
              <div className="bg-surface-container p-7 doodle-border paper-shadow relative transform -rotate-1 hover:rotate-0 hover:-translate-y-1 transition-all duration-300 flex flex-col">
                <div className="washi-tape-1 bg-outline" style={{ left: "auto", right: "20px", top: "-12px" }}></div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-accent-blue/20 text-accent-blue flex items-center justify-center doodle-border">
                    <SketchUsersIcon className="w-5 h-5 text-accent-blue" />
                  </div>
                  <h3 className="font-bold text-2xl text-sketch-white font-serif">Preview Branches</h3>
                </div>
                <p className="text-on-surface-variant text-sm flex-grow">
                  Every Pull Request generates an isolated preview subdomain (`feat-auth.my-app.deployhub.local`) for seamless team QA.
                </p>
                {/* Mock UI snippet */}
                <div className="mt-6 bg-surface-dim p-3.5 doodle-border flex gap-3 items-start transform rotate-1">
                  <div className="w-7 h-7 rounded-full bg-primary text-surface font-mono font-bold flex items-center justify-center text-xs shrink-0">
                    AX
                  </div>
                  <div className="text-left font-mono text-xs">
                    <div className="text-sketch-white font-bold">Alex (Lead Architect)</div>
                    <div className="text-on-surface-variant text-[11px] mt-0.5">
                      Preview looks blazing fast! Approved to merge 🚀
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 4: Encrypted Secrets Vault */}
              <div className="bg-surface-container p-7 doodle-border paper-shadow relative flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-tertiary/20 text-tertiary flex items-center justify-center doodle-border">
                    <SketchLockIcon className="w-5 h-5 text-tertiary" />
                  </div>
                  <h3 className="font-bold text-2xl text-sketch-white font-serif">Encrypted Secrets</h3>
                </div>
                <p className="text-on-surface-variant text-sm flex-grow">
                  Store sensitive API keys with AES-256-GCM encryption. Decrypted only inside isolated ephemeral build containers.
                </p>
                <div className="mt-6 bg-surface-dim p-3.5 doodle-border font-mono text-xs space-y-1.5">
                  <div className="flex justify-between text-outline">
                    <span>DATABASE_URL</span>
                    <span className="text-primary">••••••••••••• [LOCKED]</span>
                  </div>
                  <div className="flex justify-between text-outline">
                    <span>STRIPE_SECRET</span>
                    <span className="text-primary">••••••••••••• [LOCKED]</span>
                  </div>
                </div>
              </div>

              {/* Card 5: Isolated Docker Workers */}
              <div className="bg-surface-container p-7 doodle-border paper-shadow relative flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-primary/20 text-primary flex items-center justify-center doodle-border">
                    <SketchBoltIcon className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="font-bold text-2xl text-sketch-white font-serif">Sandboxed Workers</h3>
                </div>
                <p className="text-on-surface-variant text-sm flex-grow">
                  Every build runs in a strictly isolated Docker container with dedicated memory and CPU cgroups. Zero noisy neighbors.
                </p>
                <div className="mt-6 bg-surface-dim p-3.5 doodle-border font-mono text-xs flex justify-between items-center">
                  <span className="text-on-surface-variant">Worker Status:</span>
                  <span className="text-primary font-bold">2.0 CPU / 4GB RAM Dedicated</span>
                </div>
              </div>

              {/* Card 6: Dynamic Subdomain Routing */}
              <div className="bg-surface-container p-7 doodle-border paper-shadow relative flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-accent-blue/20 text-accent-blue flex items-center justify-center doodle-border">
                    <SketchGlobeIcon className="w-5 h-5 text-accent-blue" />
                  </div>
                  <h3 className="font-bold text-2xl text-sketch-white font-serif">Dynamic Domains</h3>
                </div>
                <p className="text-on-surface-variant text-sm flex-grow">
                  Caddy reverse proxy updates subdomains automatically with wildcard SSL. Instant routing without reverse proxy restarts.
                </p>
                <div className="mt-6 bg-surface-dim p-3.5 doodle-border font-mono text-xs flex justify-between items-center">
                  <span className="text-outline">Route Sync:</span>
                  <span className="text-accent-blue font-bold">&lt; 350ms Caddy Sync</span>
                </div>
              </div>
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 5. ARCHITECTURAL BLUEPRINT SECTION (Commented out as requested) */}
          {/* ========================================================================= */}
          {/* 
          <section id="architecture" className="w-full scroll-mt-28">
            <ArchitectureMap />
          </section>
          */}

          {/* ========================================================================= */}
          {/* 6. INTERACTIVE ROLLBACK PLAYGROUND */}
          {/* ========================================================================= */}
          <section className="w-full max-w-6xl mx-auto">
            <InteractiveRollbackDemo />
          </section>

          {/* ========================================================================= */}
          {/* 7. "HOW IT WORKS" 4-STEP TIMELINE (#how-it-works) */}
          {/* ========================================================================= */}
          <section id="how-it-works" className="w-full max-w-6xl mx-auto my-20 px-4 scroll-mt-28">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container border border-outline-variant/60 rounded-full font-mono text-xs text-primary mb-3">
                <SketchRocket className="w-4 h-4 text-primary" />
                <span>Simple 4-Step Pipeline</span>
              </div>
              <h2
                className="text-4xl md:text-5xl font-bold text-sketch-white tracking-tight font-serif"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                From <span className="text-primary sketch-underline">Code</span> to Global Live URL
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                {
                  step: "01",
                  title: "Push Code",
                  desc: "Commit to GitHub. Our idempotent webhook listener verifies HMAC signatures and registers the build.",
                  color: "primary",
                },
                {
                  step: "02",
                  title: "Kafka Queue",
                  desc: "Pushes are published to a distributed Kafka partition to ensure zero build loss under heavy load.",
                  color: "tertiary",
                },
                {
                  step: "03",
                  title: "Docker Sandbox",
                  desc: "An ephemeral runner container builds your app, streams logs, and uploads artifacts to MinIO S3.",
                  color: "accent-blue",
                },
                {
                  step: "04",
                  title: "Instant Live",
                  desc: "Caddy registers the live subdomain in <350ms. Your app is online and ready for traffic.",
                  color: "primary",
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="bg-surface-container p-6 rounded-xl doodle-border paper-shadow flex flex-col justify-between"
                >
                  <div>
                    <span className="text-3xl font-extrabold font-mono text-primary/40 block mb-2">
                      {item.step}
                    </span>
                    <h3 className="text-xl font-bold text-sketch-white mb-2 font-serif">
                      {item.title}
                    </h3>
                    <p className="text-on-surface-variant text-xs leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-outline-variant/30 font-mono text-[11px] text-primary flex items-center gap-1">
                    <span>✓ Automated</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 8. DEVELOPER TESTIMONIAL POLAROID WALL */}
          {/* ========================================================================= */}
          <section className="w-full max-w-6xl mx-auto my-20 px-4">
            <div className="text-center mb-12">
              <h2
                className="text-4xl md:text-5xl font-bold text-sketch-white tracking-tight font-serif"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                Built for Developers, Trusted by Builders
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  quote:
                    "The instant rollbacks saved our launch. Swapping a route in 280ms without waiting for a re-build is an absolute game-changer.",
                  author: "Sarah Jenkins",
                  role: "CTO @ FastFlow",
                  color: "rotate-[-2deg]",
                },
                {
                  quote:
                    "DeployHub feels like what cloud deployment should have been from day one. Clean, zero bloat, and the streaming logs are buttery smooth.",
                  author: "Marcus Chen",
                  role: "Indie Hacker & Creator",
                  color: "rotate-[2deg]",
                },
                {
                  quote:
                    "We migrated 40 micro-frontends from heavy CI/CD pipelines. Our deployment times dropped from 8 minutes down to 45 seconds.",
                  author: "Elena Rostova",
                  role: "Head of Infra @ DevScale",
                  color: "rotate-[-1deg]",
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className={`bg-surface-container p-6 doodle-border paper-shadow transform ${item.color} hover:rotate-0 transition-transform`}
                >
                  <div className="washi-tape-1 bg-tertiary opacity-70"></div>
                  <p className="text-on-surface-variant text-sm italic mb-6 leading-relaxed">
                    &ldquo;{item.quote}&rdquo;
                  </p>
                  <div className="border-t border-outline-variant/30 pt-4 font-mono text-xs">
                    <strong className="text-sketch-white block">{item.author}</strong>
                    <span className="text-outline">{item.role}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ========================================================================= */}
          {/* 9. FAQ ACCORDION NOTEBOOK (#faq) */}
          {/* ========================================================================= */}
          <section id="faq" className="w-full scroll-mt-28">
            <InteractiveFAQ />
          </section>

          {/* ========================================================================= */}
          {/* 10. FINAL PRE-FOOTER CTA CARD */}
          {/* ========================================================================= */}
          <section className="w-full max-w-5xl mx-auto my-16 px-4">
            <div className="bg-surface-container-high p-8 md:p-14 doodle-border-emerald paper-shadow-lg relative text-center flex flex-col items-center">
              <div className="washi-tape-1 bg-primary"></div>
              <div className="washi-tape-2 bg-tertiary"></div>

              <DeployHubLogo className="h-16 mb-4" showText={false} />

              <h2
                className="text-4xl sm:text-5xl md:text-6xl font-bold text-sketch-white tracking-tight font-serif max-w-2xl"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                Ready to Ship at the Speed of Thought?
              </h2>

              <p className="text-on-surface-variant text-base sm:text-lg max-w-xl mt-4 mb-8">
                Join thousands of engineers deploying resilient apps with instant subdomains and real-time observability.
              </p>

              {/* Quick Start Terminal Snippet */}
              <div className="bg-surface-dim px-6 py-3 rounded-xl doodle-border font-mono text-xs sm:text-sm text-primary mb-8 flex items-center gap-3 paper-shadow">
                <span className="text-outline select-none">$</span>
                <span>curl -sSL https://get.deployhub.dev | bash</span>
                <span className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded ml-2 hidden sm:inline">
                  COPY
                </span>
              </div>

              {/* Primary Action Button */}
              <a
                href="#demo"
                className="bg-primary text-surface font-mono font-bold text-lg px-10 py-4 hover:bg-primary-fixed transition-transform transform -rotate-1 hover:rotate-0 doodle-border-emerald paper-shadow-emerald"
              >
                Deploy Your First Project ⚡
              </a>

              <span className="text-xs font-mono text-outline mt-4">
                No credit card required · Free forever tier available
              </span>
            </div>
          </section>
        </main>

        <Footer />
      </div>
    </>
  );
}
