"use client";

import React, { useState } from "react";
import { SketchDatabaseIcon, SketchLockIcon, SketchGlobeIcon, SketchBoltIcon } from "./SketchIcons";

const NODES = [
  {
    id: "webhook",
    title: "1. Webhook Ingestion",
    tech: "FastAPI + Redis",
    summary: "Idempotent GitHub push listener verified via SHA-256 HMAC secrets.",
    details: "Deduplicates repeat webhooks using `X-GitHub-Delivery` Redis keys with 24h TTL. Never triggers duplicate builds.",
    color: "primary",
  },
  {
    id: "redpanda",
    title: "2. Event Queue",
    tech: "Redpanda / Kafka",
    summary: "Distributed event backbone with persistent partitions and zero dropped messages.",
    details: "Emits `build.queued`, `build.completed`, and `deployment.uploaded` events. Supports consumer groups and automated retry backoffs.",
    color: "tertiary",
  },
  {
    id: "orchestrator",
    title: "3. Docker Orchestrator",
    tech: "aiodocker + cgroups",
    summary: "Runs isolated build containers with CPU/RAM limits and streaming logs.",
    details: "Acquires distributed Redis locks per project so parallel pushes don't collide. Streams live stdout/stderr through WebSockets.",
    color: "accent-blue",
  },
  {
    id: "minio",
    title: "4. Artifact Storage",
    tech: "MinIO S3 Compatible",
    summary: "Immutable zip archive storage for versioned deployments.",
    details: "Enables instant rollbacks to any historical build artifact without re-running long build steps.",
    color: "tertiary",
  },
  {
    id: "caddy",
    title: "5. Dynamic Reverse Proxy",
    tech: "Caddy Server Admin API",
    summary: "Zero-downtime atomic subdomain route registration in <350ms.",
    details: "Listens to `deployment.live` events and updates dynamic route configs on-the-fly without restarting the reverse proxy daemon.",
    color: "primary",
  },
];

export function ArchitectureMap() {
  const [activeNode, setActiveNode] = useState(NODES[0]);

  return (
    <section id="architecture" className="w-full max-w-6xl mx-auto my-24 px-4 relative">
      {/* Washi tape on section */}
      <div className="washi-tape-1 -top-6 left-8 bg-tertiary"></div>
      <div className="washi-tape-2 -bottom-6 right-8 bg-primary"></div>

      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container border border-outline-variant/60 rounded-full font-mono text-xs text-primary mb-3">
          <SketchBoltIcon className="w-4 h-4 text-tertiary" />
          <span>Fail-Proof Distributed Architecture</span>
        </div>
        <h2
          className="text-4xl md:text-5xl font-bold text-sketch-white tracking-tight font-serif"
          style={{ fontFamily: "var(--font-bricolage)" }}
        >
          Engineered for <span className="text-primary sketch-underline">Scale</span> & Zero Downtime
        </h2>
        <p className="text-on-surface-variant font-body-md text-lg max-w-2xl mx-auto mt-4">
          Click any component in the pipeline below to inspect its fail-safe mechanisms and concurrency guarantees.
        </p>
      </div>

      {/* Main Architecture Blueprint Card */}
      <div className="bg-surface-container p-6 md:p-10 doodle-border paper-shadow-lg grid grid-cols-1 lg:grid-cols-12 gap-8 relative">
        {/* Node Pipeline Flow */}
        <div className="lg:col-span-7 flex flex-col gap-4 justify-between">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {NODES.map((node) => {
              const isSelected = activeNode.id === node.id;
              return (
                <button
                  key={node.id}
                  onClick={() => setActiveNode(node)}
                  className={`text-left p-4 rounded-xl doodle-border transition-all cursor-pointer relative ${
                    isSelected
                      ? "bg-surface-container-high border-primary paper-shadow-emerald transform -translate-y-1"
                      : "bg-surface hover:bg-surface-container-high border-outline-variant/40"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-mono text-xs text-outline">{node.tech}</span>
                    {isSelected && (
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 bg-primary/20 text-primary rounded">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-sketch-white text-base mb-1 font-serif">
                    {node.title}
                  </h3>
                  <p className="text-on-surface-variant text-xs leading-relaxed">
                    {node.summary}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Hand-drawn note */}
          <div className="bg-surface-dim p-4 doodle-border flex items-center gap-3 font-mono text-xs text-on-surface-variant mt-2">
            <span className="text-tertiary text-lg">✎</span>
            <span>
              <strong>Resilience Guarantee:</strong> All microservices are fully stateless except MinIO and PostgreSQL. Orchestrator crashes trigger automated offset replay.
            </span>
          </div>
        </div>

        {/* Deep Dive Node Inspector Pane */}
        <div className="lg:col-span-5 bg-surface-dim p-6 rounded-xl doodle-border flex flex-col justify-between relative">
          <div className="washi-tape-blue"></div>

          <div>
            <div className="flex items-center justify-between border-b border-outline-variant/40 pb-3 mb-4">
              <span className="font-mono text-xs text-primary font-bold">
                {activeNode.tech}
              </span>
              <span className="font-mono text-xs text-outline">
                STAGE INSPECTOR
              </span>
            </div>

            <h4
              className="text-2xl font-bold text-sketch-white mb-2 font-serif"
              style={{ fontFamily: "var(--font-bricolage)" }}
            >
              {activeNode.title}
            </h4>

            <p className="text-on-surface-variant text-sm leading-relaxed mb-6">
              {activeNode.summary}
            </p>

            <div className="bg-surface-container p-4 rounded-lg border border-outline-variant/60 mb-4">
              <span className="text-xs font-mono text-tertiary block font-bold mb-1">
                // Resilience & Concurrency
              </span>
              <p className="text-sketch-white text-xs leading-relaxed font-mono">
                {activeNode.details}
              </p>
            </div>
          </div>

          {/* Technical Specs List */}
          <div className="space-y-2 border-t border-outline-variant/30 pt-4 font-mono text-xs">
            <div className="flex justify-between text-on-surface-variant">
              <span>Concurrency Lock:</span>
              <strong className="text-primary">Redis Distributed Redlock</strong>
            </div>
            <div className="flex justify-between text-on-surface-variant">
              <span>Delivery Guarantee:</span>
              <strong className="text-sketch-white">At-least-once + Idempotent</strong>
            </div>
            <div className="flex justify-between text-on-surface-variant">
              <span>Dynamic Routing Latency:</span>
              <strong className="text-tertiary">&lt; 350ms</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
