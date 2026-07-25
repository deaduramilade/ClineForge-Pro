"use client";

import { motion } from "framer-motion";
import {
  CheckCircle2,
  Activity,
  FileText,
  ImageIcon,
  BrainCircuit,
} from "lucide-react";

const items = [
  {
    icon: FileText,
    title: "Script Upload",
    status: "Ready",
  },
  {
    icon: BrainCircuit,
    title: "Scene Reasoning",
    status: "Operational",
  },
  {
    icon: ImageIcon,
    title: "Storyboard Generation",
    status: "Available",
  },
  {
    icon: Activity,
    title: "Judge Mode",
    status: "Live Preview",
  },
];

export default function JudgePreview() {
  return (
    <section
      id="judge"
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
            Judge Mode Preview
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-lg text-gray-400">
            Demonstrates the end-to-end CineForge workflow in a clean dashboard,
            allowing reviewers to observe each processing stage.
          </p>

        </div>

        <div className="mt-16 rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">

          <div className="mb-8 flex items-center justify-between border-b border-white/10 pb-6">
            <div>
              <h3 className="text-2xl font-bold">
                Live Processing Dashboard
              </h3>
              <p className="text-sm text-gray-400">
                Simulation of the AI production pipeline
              </p>
            </div>

            <span className="rounded-full bg-green-500/20 px-4 py-2 text-sm font-semibold text-green-400">
              System Online
            </span>
          </div>

          <div className="grid gap-6 md:grid-cols-2">

            {items.map((item) => {
              const Icon = item.icon;

              return (
                <div
                  key={item.title}
                  className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 p-5"
                >
                  <div className="flex items-center gap-4">
                    <div className="rounded-xl bg-cyan-500/10 p-3">
                      <Icon className="h-6 w-6 text-cyan-400" />
                    </div>

                    <div>
                      <h4 className="font-semibold">
                        {item.title}
                      </h4>

                      <p className="text-sm text-gray-400">
                        {item.status}
                      </p>
                    </div>
                  </div>

                  <CheckCircle2 className="h-6 w-6 text-green-400" />
                </div>
              );
            })}

          </div>
        </div>
      </motion.div>
    </section>
  );
}