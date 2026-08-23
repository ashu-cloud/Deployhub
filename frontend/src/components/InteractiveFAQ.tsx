"use client";

import React, { useState } from "react";
import { SketchBoltIcon } from "./SketchIcons";

const FAQS = [
  {
    question: "How does DeployHub achieve sub-second rollbacks?",
    answer:
      "When a build completes, the output bundle is archived as an immutable artifact in MinIO (S3-compatible storage). During a rollback, DeployHub does not re-build your code from source; it simply updates Caddy's dynamic routing table via its Admin API to point the subdomain directly to the historical artifact directory. This takes less than 350ms.",
  },
  {
    question: "How does DeployHub handle build concurrency and prevent race conditions?",
    answer:
      "DeployHub leverages Apache Kafka (KRaft mode, no ZooKeeper) and Redis distributed locks (Redlock). When multiple webhooks arrive simultaneously for the same repository, each push event is assigned a dedicated partition offset. The Build Orchestrator acquires an atomic Redis lock per project, ensuring builds execute sequentially without overwriting artifacts or crashing memory.",
  },
  {
    question: "Can I bring my own custom Dockerfile or build commands?",
    answer:
      "Yes! DeployHub auto-detects Next.js, Vite, React, Vue, Svelte, and static HTML apps by default. You can also specify custom build commands (`npm run build:prod`, `pnpm build`, `cargo build`), custom output directories (`dist/`, `out/`, `build/`), and multi-stage Dockerfiles.",
  },
  {
    question: "Are environment variables encrypted and secure?",
    answer:
      "All environment variables and secret tokens are encrypted at rest using AES-256-GCM before being stored in PostgreSQL. They are only decrypted ephemerally inside the isolated build runner container and never exposed in public build logs or client bundles.",
  },
  {
    question: "Can I self-host DeployHub on my own cloud VPS or bare metal?",
    answer:
      "Absolutely. DeployHub is architected with modern open-source foundations (Docker, Apache Kafka, MinIO, Redis, PostgreSQL, Caddy). You can run the entire platform on a single $10 VPS using Docker Compose or deploy it on Kubernetes.",
  },
];

export function InteractiveFAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <section id="faq" className="w-full max-w-4xl mx-auto my-24 px-4 relative">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container border border-outline-variant/60 rounded-full font-mono text-xs text-primary mb-3">
          <SketchBoltIcon className="w-4 h-4 text-tertiary" />
          <span>Frequently Asked Questions</span>
        </div>
        <h2
          className="text-4xl md:text-5xl font-bold text-sketch-white tracking-tight font-serif"
          style={{ fontFamily: "var(--font-bricolage)" }}
        >
          Everything You Need to <span className="text-primary sketch-underline">Know</span>
        </h2>
      </div>

      {/* Notebook-styled FAQ Accordion */}
      <div className="bg-surface-container p-6 md:p-8 doodle-border paper-shadow-lg space-y-4">
        {FAQS.map((faq, idx) => {
          const isOpen = openIndex === idx;
          return (
            <div
              key={idx}
              className={`border-2 rounded-xl transition-all ${
                isOpen
                  ? "border-primary bg-surface-container-high paper-shadow-emerald"
                  : "border-outline-variant/40 bg-surface hover:border-outline-variant/80"
              }`}
            >
              <button
                onClick={() => toggle(idx)}
                className="w-full text-left p-5 flex items-center justify-between gap-4 cursor-pointer"
              >
                <span
                  className="font-bold text-sketch-white text-base md:text-lg font-serif"
                  style={{ fontFamily: "var(--font-bricolage)" }}
                >
                  {faq.question}
                </span>
                <span
                  className={`font-mono text-xl transition-transform duration-200 text-primary ${
                    isOpen ? "rotate-45" : ""
                  }`}
                >
                  +
                </span>
              </button>

              {isOpen && (
                <div className="px-5 pb-5 pt-1 text-on-surface-variant text-sm leading-relaxed border-t border-outline-variant/30 font-body-md">
                  {faq.answer}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
