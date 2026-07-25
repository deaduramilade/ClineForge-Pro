"use client";

import { motion } from "framer-motion";
import {
  Upload,
  FileSearch,
  BrainCircuit,
  Camera,
  Images,
  Download,
} from "lucide-react";

const pipeline = [
  {
    icon: Upload,
    title: "Upload Script",
    description:
      "Upload screenplay, Fountain or PDF files for AI processing.",
    color: "text-cyan-400",
  },
  {
    icon: FileSearch,
    title: "Scene Parsing",
    description:
      "Characters, dialogue, actions and locations are extracted.",
    color: "text-emerald-400",
  },
  {
    icon: BrainCircuit,
    title: "AI Scene Reasoning",
    description:
      "The reasoning engine understands emotion, pacing and intent.",
    color: "text-violet-400",
  },
  {
    icon: Camera,
    title: "Camera Planning",
    description:
      "Camera angles and shot suggestions are automatically generated.",
    color: "text-amber-400",
  },
  {
    icon: Images,
    title: "Storyboard Generation",
    description:
      "Scenes become production-ready storyboard frames.",
    color: "text-pink-400",
  },
  {
    icon: Download,
    title: "Export",
    description:
      "Export PDF, PNG or production-ready packages.",
    color: "text-cyan-300",
  },
];

export default function Pipeline() {
  return (
    <section
      id="pipeline"
      className="relative overflow-hidden bg-[#050816] py-28"
    >
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute left-0 top-0 h-[450px] w-[450px] rounded-full bg-cyan-500/10 blur-[180px]" />

        <div className="absolute right-0 bottom-0 h-[450px] w-[450px] rounded-full bg-violet-500/10 blur-[180px]" />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.03),transparent_70%)]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mx-auto mb-20 max-w-3xl text-center"
        >
          <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-300">
            AI Production Pipeline
          </span>

          <h2 className="mt-6 text-5xl font-bold text-white">
            How CineForge
            <span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
              {" "}Creates Storyboards
            </span>
          </h2>

          <p className="mt-6 text-lg leading-8 text-gray-400">
            Every screenplay passes through an intelligent production
            workflow—from script parsing to camera planning and storyboard
            generation.
          </p>
        </motion.div>

        <div className="grid gap-8 md:grid-cols-2 xl:grid-cols-3">
          {pipeline.map((step, index) => {
            const Icon = step.icon;

            return (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 40, scale: 0.95 }}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                viewport={{ once: true }}
                transition={{
                  duration: 0.6,
                  delay: index * 0.15,
                }}
                className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl transition-all duration-300 hover:-translate-y-2 hover:border-cyan-400/40"
              >
                <div className="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  <div className="absolute -top-20 right-0 h-48 w-48 rounded-full bg-cyan-500/10 blur-3xl" />
                </div>

                <div className="relative">
                  <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5">
                    <Icon className={`h-8 w-8 ${step.color}`} />
                  </div>

                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-2xl font-semibold text-white">
                      {step.title}
                    </h3>

                    <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-gray-400">
                      0{index + 1}
                    </span>
                  </div>

                  <p className="leading-7 text-gray-400">
                    {step.description}
                  </p>

                  <div className="mt-8 h-1 overflow-hidden rounded-full bg-white/10">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: "100%" }}
                      viewport={{ once: true }}
                      transition={{
                        duration: 1,
                        delay: index * 0.2,
                      }}
                      className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500"
                    />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Workflow Connector */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6, duration: 1 }}
          className="mt-24 overflow-hidden rounded-3xl border border-cyan-500/20 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-violet-500/10 p-8"
        >
          <div className="flex flex-col items-center justify-between gap-6 lg:flex-row">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">
                AI Workflow
              </p>

              <h3 className="mt-3 text-3xl font-bold text-white">
                From Script to Production
              </h3>

              <p className="mt-4 max-w-2xl text-gray-400">
                CineForge transforms raw screenplay text into structured,
                production-ready visual storyboards using multiple AI reasoning
                stages.
              </p>
            </div>

            <button className="rounded-2xl bg-cyan-500 px-8 py-4 font-semibold text-black transition hover:bg-cyan-400">
              Launch Workflow
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}