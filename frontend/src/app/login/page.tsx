import Link from "next/link";
import { DeployHubLogo, SketchLockIcon, SketchSparkle } from "@/components/SketchIcons";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface paper-texture flex flex-col justify-between relative overflow-hidden">
      {/* Decorative Background Doodles (Absolute Positioned) */}
      <div className="absolute top-20 left-20 opacity-20 text-outline-variant transform -rotate-12 pointer-events-none hidden md:block select-none">
        <div className="text-8xl font-mono">☁</div>
        <div className="font-mono text-xs mt-2 text-center text-on-surface-variant">
          deploy_cluster_v2
        </div>
      </div>

      <div className="absolute bottom-40 right-20 opacity-20 text-outline-variant transform rotate-12 pointer-events-none hidden md:block select-none">
        <div className="text-8xl font-mono">&lt;/&gt;</div>
        <div className="font-mono text-xs mt-2 text-center text-on-surface-variant">
          &lt; init /&gt;
        </div>
      </div>

      <div className="absolute top-1/4 right-1/4 opacity-40 text-tertiary pointer-events-none hidden lg:block">
        <SketchSparkle className="w-10 h-10 text-tertiary" />
      </div>

      {/* Top back navigation */}
      <header className="p-6 md:px-12 flex justify-between items-center z-10">
        <Link href="/" className="flex items-center gap-2 group text-sm font-mono text-on-surface-variant hover:text-primary transition-colors">
          <span className="group-hover:-translate-x-1 transition-transform">←</span>
          <span>Back to Home</span>
        </Link>
        <div className="font-mono text-xs text-outline">
          Auth Service v1.0
        </div>
      </header>

      {/* Main Login Card Area */}
      <main className="flex-grow flex items-center justify-center px-4 py-8 relative z-10">
        <div className="relative w-full max-w-md">
          {/* Logo Above Card */}
          <div className="flex justify-center mb-6 relative z-10">
            <Link href="/" className="wiggle transform hover:scale-105 transition-transform">
              <DeployHubLogo className="h-16" />
            </Link>
          </div>

          {/* Tape Accent (Top Left) */}
          <div className="washi-tape-1 -top-3 left-6 bg-tertiary z-20 pointer-events-none"></div>

          {/* Ghost Border Element (Underneath for paper depth) */}
          <div className="absolute inset-0 bg-surface-container-low doodle-border -z-10 translate-x-3 translate-y-3 pointer-events-none hidden md:block"></div>

          {/* Login Card */}
          <div className="bg-surface-container-high doodle-border p-8 md:p-10 relative z-10 paper-shadow-lg backdrop-blur-sm">
            <div className="text-center mb-8">
              <h1
                className="text-3xl md:text-4xl font-bold text-sketch-white transform -rotate-1 mb-2 inline-block font-serif tracking-tight"
                style={{ fontFamily: "var(--font-bricolage)" }}
              >
                Initialize Session
              </h1>
              <p className="font-mono text-xs text-on-surface-variant mt-1">
                Connect your GitHub workspace
              </p>
            </div>

            {/* Action Button */}
            <div className="flex flex-col gap-4">
              <a
                href="http://localhost:8001/api/v1/auth/github/login"
                className="doodle-btn bg-surface hover:bg-surface-variant text-sketch-white flex items-center justify-center gap-3.5 py-4 px-6 w-full group relative overflow-hidden paper-shadow cursor-pointer transition-all hover:border-primary"
              >
                {/* GitHub Vector Icon */}
                <svg
                  aria-hidden="true"
                  className="w-6 h-6 text-sketch-white fill-current shrink-0"
                  viewBox="0 0 24 24"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.379.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.416 22 12c0-5.523-4.477-10-10-10z"
                  />
                </svg>
                <span className="font-mono text-base font-bold tracking-tight">
                  Continue with GitHub
                </span>
              </a>
            </div>

            {/* Security Guarantee Note */}
            <div className="mt-8 text-center border-t-2 border-outline-variant/40 pt-5 border-dashed">
              <p className="font-mono text-xs text-on-surface-variant flex items-center justify-center gap-2">
                <SketchLockIcon className="w-4 h-4 text-primary" />
                <span>Stateless JWT & AES-256 encrypted OAuth token vault</span>
              </p>
            </div>
          </div>

          {/* Tape Accent (Bottom Right) */}
          <div className="washi-tape-2 -bottom-3 right-6 bg-primary z-20 pointer-events-none"></div>
        </div>
      </main>

      {/* Login Footer */}
      <footer className="bg-surface-container-lowest flex flex-col md:flex-row justify-between items-center px-6 md:px-12 py-5 w-full border-t-2 border-outline-variant/30 text-xs font-mono text-outline">
        <div className="text-primary font-bold mb-2 md:mb-0">
          DeployHub
        </div>
        <div className="text-on-surface-variant mb-2 md:mb-0 text-center">
          © {new Date().getFullYear()} DeployHub — Crafted with Ink & Code
        </div>
        <nav className="flex gap-4">
          <Link href="#" className="hover:text-primary transition-colors">Terms</Link>
          <Link href="#" className="hover:text-primary transition-colors">Privacy</Link>
          <Link href="#" className="hover:text-primary transition-colors">Status</Link>
        </nav>
      </footer>
    </div>
  );
}
