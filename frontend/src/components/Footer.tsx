import Link from "next/link";
import { DeployHubLogo } from "./SketchIcons";

export default function Footer() {
  return (
    <footer className="bg-surface-dim border-t-2 border-outline-variant/40 pt-16 pb-12 w-full px-6 md:px-12 relative z-20 mt-20">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-5 gap-10 mb-12">
        {/* Brand Column */}
        <div className="md:col-span-2 space-y-4">
          <DeployHubLogo className="h-10" />
          <p className="text-on-surface-variant text-sm font-body-md max-w-sm">
            The autonomous, container-native deployment platform. Ship code to custom domains with real-time logs and atomic rollbacks.
          </p>
          <div className="flex items-center gap-2 font-mono text-xs text-primary">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse"></span>
            <span>Cluster Status: All Systems Operational</span>
          </div>
        </div>

        {/* Column 1: Product */}
        <div className="space-y-3 font-mono text-xs">
          <h4 className="text-sketch-white font-bold uppercase tracking-wider text-sm font-serif">
            Product
          </h4>
          <ul className="space-y-2 text-on-surface-variant">
            <li><a href="#demo" className="hover:text-primary transition-colors">Interactive Demo</a></li>
            <li><a href="#benchmarks" className="hover:text-primary transition-colors">Benchmarks</a></li>
            <li><a href="#features" className="hover:text-primary transition-colors">Features</a></li>
            {/* <li><a href="#architecture" className="hover:text-primary transition-colors">Architecture</a></li> */}
            <li><a href="#how-it-works" className="hover:text-primary transition-colors">How It Works</a></li>
            <li><a href="#faq" className="hover:text-primary transition-colors">FAQ</a></li>
          </ul>
        </div>

        {/* Column 2: Platform */}
        <div className="space-y-3 font-mono text-xs">
          <h4 className="text-sketch-white font-bold uppercase tracking-wider text-sm font-serif">
            Under The Hood
          </h4>
          <ul className="space-y-2 text-on-surface-variant">
            <li><span className="text-sketch-white">Apache Kafka</span> (KRaft Event Queue)</li>
            <li><span className="text-sketch-white">aiodocker</span> (Containers)</li>
            <li><span className="text-sketch-white">MinIO</span> (S3 Artifacts)</li>
            <li><span className="text-sketch-white">Redis</span> (Redlock Concurrency)</li>
            <li><span className="text-sketch-white">Caddy</span> (Dynamic Proxy)</li>
          </ul>
        </div>

        {/* Column 3: Community & Legal */}
        <div className="space-y-3 font-mono text-xs">
          <h4 className="text-sketch-white font-bold uppercase tracking-wider text-sm font-serif">
            Connect
          </h4>
          <ul className="space-y-2 text-on-surface-variant">
            <li><a href="https://github.com" className="hover:text-primary transition-colors">GitHub Repository</a></li>
            <li><a href="https://discord.com" className="hover:text-primary transition-colors">Discord Community</a></li>
            <li><a href="#" className="hover:text-primary transition-colors">Documentation</a></li>
            <li><a href="#" className="hover:text-primary transition-colors">Privacy Policy</a></li>
            <li><a href="#" className="hover:text-primary transition-colors">Terms of Service</a></li>
          </ul>
        </div>
      </div>

      <div className="max-w-6xl mx-auto border-t border-outline-variant/30 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-mono text-outline">
        <div>
          © {new Date().getFullYear()} DeployHub. Built for developers with high standards.
        </div>
        <div className="flex gap-4">
          <span>MIT License</span>
          <span>•</span>
          <span>Zero Telemetry</span>
          <span>•</span>
          <span>Cloud-Native</span>
        </div>
      </div>
    </footer>
  );
}
