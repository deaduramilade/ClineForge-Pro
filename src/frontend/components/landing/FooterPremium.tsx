"use client";

import { motion } from "framer-motion";
import {
  Mail,
  Terminal,
  Activity,
  ShieldCheck,
  ArrowUpRight,
  Globe,
} from "lucide-react";
import { FaGithub, FaLinkedin } from "react-icons/fa";

export default function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-white/10 bg-[#01030A]">
      {/* Ambient Glow */}
      <div className="absolute left-1/2 top-0 h-[450px] w-[450px] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-[180px]" />

      <div className="relative mx-auto max-w-7xl px-6 py-24">
        {/* Hero Footer */}
        <div className="grid gap-16 lg:grid-cols-2">
          <div>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-5xl font-bold text-white"
            >
              Build Movies
              <br />
              <span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
                With AI.
              </span>
            </motion.h2>

            <p className="mt-8 max-w-xl text-lg leading-8 text-gray-400">
              CineForge AI transforms screenplays into intelligent,
              production-ready cinematic storyboards using multi-stage AI
              reasoning.
            </p>
          </div>

          {/* Runtime Card */}
          <div className="rounded-[32px] border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <div className="mb-8 flex items-center gap-3">
              <Activity className="text-cyan-400" />
              <span className="font-semibold text-white">Runtime Status</span>
            </div>

            <div className="space-y-5">
              {[
                ["Backend", "Online"],
                ["AI Engine", "Running"],
                ["Inference", "Healthy"],
                ["API", "Available"],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between">
                  <span className="text-gray-400">{k}</span>
                  <span className="text-emerald-400">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Links */}
        <div className="mt-20 border-t border-white/10 pt-12">
          <div className="grid gap-12 md:grid-cols-4">
            <div>
              <h4 className="mb-5 font-semibold text-white">Platform</h4>
              <div className="space-y-3 text-gray-400">
                <p>Pipeline</p>
                <p>Architecture</p>
                <p>Director Monitor</p>
                <p>Upload</p>
              </div>
            </div>

            <div>
              <h4 className="mb-5 font-semibold text-white">Technology</h4>
              <div className="space-y-3 text-gray-400">
                <p>FastAPI</p>
                <p>Next.js</p>
                <p>HuggingFace</p>
                <p>Docker</p>
              </div>
            </div>

            <div>
              <h4 className="mb-5 font-semibold text-white">Resources</h4>
              <div className="space-y-3 text-gray-400">
                <p>Documentation</p>
                <p>API</p>
                <p>GitHub</p>
                <p>Status</p>
              </div>
            </div>

            <div>
              <h4 className="mb-5 font-semibold text-white">Contact</h4>
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-gray-400">
                  <Mail size={18} />
                  hello@cineforge.ai
                </div>
                <div className="flex items-center gap-3 text-gray-400">
                  <FaGithub size={18} />
                  GitHub
                </div>
                <div className="flex items-center gap-3 text-gray-400">
                  <FaLinkedin size={18} />
                  LinkedIn
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Copyright */}
          <div className="mt-16 flex flex-col items-center justify-between gap-6 border-t border-white/10 pt-8 lg:flex-row">
            <div className="flex items-center gap-3">
              <Terminal className="text-cyan-400" />
              <span className="text-gray-500">
                CineForge AI • Production Runtime v1.0
              </span>
            </div>

            <div className="flex items-center gap-6">
              <ShieldCheck className="text-emerald-400" />
              <span className="text-gray-500">
                Built with Next.js • FastAPI • AI
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}