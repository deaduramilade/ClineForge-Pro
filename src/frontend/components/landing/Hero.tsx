"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Play,
  CheckCircle2,
  Cpu,
  Sparkles,
  Server,
} from "lucide-react";

const fadeUp = {
  hidden: {
    opacity: 0,
    y: 40,
  },
  visible: {
    opacity: 1,
    y: 0,
  },
};

const runtime = [
  {
    icon: Server,
    title: "Backend Connected",
    status: "ONLINE",
    color: "text-emerald-400",
  },
  {
    icon: Cpu,
    title: "Scene Reasoning",
    status: "ACTIVE",
    color: "text-cyan-400",
  },
  {
    icon: Sparkles,
    title: "Storyboard Engine",
    status: "READY",
    color: "text-amber-400",
  },
];

const metrics = [
  {
    value: "243+",
    label: "Backend Tests",
  },
  {
    value: "FastAPI",
    label: "Production API",
  },
  {
    value: "AI",
    label: "Scene Reasoning",
  },
];

type Particle = {
  x: number;
  y: number;
  driftUp: number;
  duration: number;
};

export default function Hero() {
  // Generate particle positions on the client only, after mount,
  // so server and client never disagree on the random values.
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    const generated = Array.from({ length: 18 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      driftUp: 120 + Math.random() * 60,
      duration: 6 + Math.random() * 5,
    }));
    setParticles(generated);
  }, []);

  return (
    <section className="relative overflow-hidden bg-[#050816] text-white">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute left-[-250px] top-[-250px] h-[520px] w-[520px] rounded-full bg-amber-500/15 blur-[180px]" />

        <div className="absolute right-[-220px] top-20 h-[450px] w-[450px] rounded-full bg-cyan-500/15 blur-[180px]" />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.04),transparent_70%)]" />

        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent,rgba(5,8,22,0.95))]" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 py-28 lg:flex-row lg:items-center lg:justify-between">
        {/* LEFT CONTENT */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="max-w-2xl"
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-amber-400/30 bg-amber-500/10 px-4 py-2 text-sm font-medium text-amber-300 backdrop-blur">
            <Sparkles className="h-4 w-4" />
            CineForge AI Pro
          </span>

          <h1 className="mt-8 text-5xl font-extrabold leading-tight tracking-tight md:text-7xl">
            Transform
            <br />
            <span className="bg-gradient-to-r from-white via-amber-200 to-cyan-300 bg-clip-text text-transparent">
              Screenplays
            </span>
            <br />
            Into Cinematic
            <br />
            Storyboards
          </h1>

          <p className="mt-8 max-w-xl text-lg leading-8 text-gray-300">
            AI-powered screenplay analysis with intelligent scene reasoning,
            multilingual understanding, and production-ready storyboard generation
            for filmmakers, creators, and studios.
          </p>

          <div className="mt-10 flex flex-wrap gap-4">
            <button className="group flex items-center gap-2 rounded-xl bg-amber-400 px-7 py-4 font-semibold text-black transition hover:bg-amber-300">
              Start Creating
              <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" />
            </button>

            <button className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-4 font-medium backdrop-blur transition hover:bg-white/10">
              <Play className="h-5 w-5" />
              Watch Demo
            </button>
          </div>

          <div className="mt-14 grid grid-cols-3 gap-6">
            {metrics.map((metric) => (
              <div
                key={metric.label}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur"
              >
                <h3 className="text-2xl font-bold text-amber-300">
                  {metric.value}
                </h3>
                <p className="mt-2 text-sm text-gray-400">
                  {metric.label}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* RIGHT - AI RUNTIME CONSOLE */}
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16 w-full max-w-xl lg:mt-0"
        >
          <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl backdrop-blur-xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-400">
                  AI Runtime
                </p>
                <h3 className="mt-1 text-xl font-semibold">
                  Production Console
                </h3>
              </div>

              <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1">
                <div className="h-2.5 w-2.5 animate-pulse rounded-full bg-emerald-400" />
                <span className="text-xs font-semibold text-emerald-300">
                  ONLINE
                </span>
              </div>
            </div>

            {/* Runtime Cards */}
            <div className="space-y-4 p-6">
              {runtime.map((item) => {
                const Icon = item.icon;

                return (
                  <div
                    key={item.title}
                    className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 p-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className="rounded-xl bg-white/5 p-3">
                        <Icon className={`h-5 w-5 ${item.color}`} />
                      </div>
                      <div>
                        <h4 className="font-medium">
                          {item.title}
                        </h4>
                        <p className="text-sm text-gray-400">
                          Runtime Service
                        </p>
                      </div>
                    </div>

                    <span className={`text-sm font-semibold ${item.color}`}>
                      {item.status}
                    </span>
                  </div>
                );
              })}

              {/* Progress */}
              <div className="rounded-2xl border border-white/10 bg-black/20 p-5">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm text-gray-300">
                    Storyboard Generation
                  </span>
                  <span className="font-semibold text-amber-300">
                    82%
                  </span>
                </div>

                <div className="h-3 overflow-hidden rounded-full bg-white/10">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "82%" }}
                    transition={{ duration: 2 }}
                    className="h-full rounded-full bg-gradient-to-r from-amber-400 to-cyan-400"
                  />
                </div>
              </div>

              {/* Scene Preview */}
              <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/5 p-5">
                <div className="mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-cyan-400" />
                  <span className="font-semibold">
                    Current Scene
                  </span>
                </div>

                <div className="space-y-2 text-sm text-gray-300">
                  <p>
                    <span className="text-gray-500">Scene</span> — INT. COFFEE SHOP — NIGHT
                  </p>
                  <p>
                    <span className="text-gray-500">Characters</span> — 4 detected
                  </p>
                  <p>
                    <span className="text-gray-500">Camera</span> — Medium Wide Shot
                  </p>
                  <p>
                    <span className="text-gray-500">Status</span> — Storyboard Ready
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Floating Particles */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {particles.map((p, i) => (
          <motion.div
            key={i}
            className="absolute h-1.5 w-1.5 rounded-full bg-white/20"
            style={{ left: p.x, top: p.y }}
            initial={{ opacity: 0.15, y: 0 }}
            animate={{
              y: [0, -p.driftUp, 0],
              opacity: [0.15, 0.5, 0.15],
            }}
            transition={{
              duration: p.duration,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </section>
  );
}