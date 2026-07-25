"use client";

import { motion } from "framer-motion";
import {
  BrainCircuit,
  Languages,
  ShieldCheck,
  ImageIcon,
  MonitorPlay,
  Lock,
} from "lucide-react";

const features = [
  {
    icon: BrainCircuit,
    title: "AI Scene Reasoning",
    description:
      "Understands screenplay context, characters, locations, and cinematic intent before generating storyboard prompts.",
  },
  {
    icon: Languages,
    title: "Multilingual Support",
    description:
      "Processes both English and Arabic scripts while preserving scene structure and meaning.",
  },
  {
    icon: ImageIcon,
    title: "Storyboard Generation",
    description:
      "Creates consistent AI storyboard frames with production-ready prompts for every detected scene.",
  },
  {
    icon: ShieldCheck,
    title: "Creative IP Protection",
    description:
      "Supports secure workflows, watermarking, and protected handling of screenplay content.",
  },
  {
    icon: MonitorPlay,
    title: "Judge Mode",
    description:
      "Live visualization of the complete AI pipeline for demos, presentations, and technical evaluation.",
  },
  {
    icon: Lock,
    title: "Secure Architecture",
    description:
      "Designed around encrypted workflows, modular AI providers, and enterprise-ready backend integration.",
  },
];

export default function Features() {
  return (
    <section
      id="features"
      className="mx-auto max-w-7xl px-8 py-32"
    >
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
      >
        <div className="text-center">

          <h2 className="text-5xl font-black">
            Why CineForge AI Pro?
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-lg text-gray-400">
            Built for filmmakers, studios, researchers, and AI-powered creative
            workflows with a focus on automation, security, and production
            readiness.
          </p>

        </div>

        <div className="mt-20 grid gap-8 md:grid-cols-2 xl:grid-cols-3">

          {features.map((feature, index) => {
            const Icon = feature.icon;

            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                viewport={{ once: true }}
                className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur transition hover:-translate-y-2 hover:border-cyan-400 hover:bg-white/10"
              >
                <div className="mb-6 inline-flex rounded-2xl bg-cyan-500/10 p-4">
                  <Icon className="h-8 w-8 text-cyan-400" />
                </div>

                <h3 className="text-2xl font-bold">
                  {feature.title}
                </h3>

                <p className="mt-5 leading-8 text-gray-400">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}

        </div>
      </motion.div>
    </section>
  );
}