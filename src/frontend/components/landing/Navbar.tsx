"use client";

import { motion } from "framer-motion";
import { Film, Upload, Globe } from "lucide-react";

export default function Navbar() {
  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-black/30 backdrop-blur-xl"
    >
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-8">

        {/* Logo */}

        <div className="flex items-center gap-3">

          <div className="rounded-xl bg-cyan-500/20 p-2">

            <Film className="h-7 w-7 text-cyan-400" />

          </div>

          <div>

            <h1 className="text-xl font-bold tracking-wide">

              CineForge AI Pro

            </h1>

            <p className="text-xs text-gray-400">

              AI Film Production Suite

            </p>

          </div>

        </div>

        {/* Navigation */}

        <nav className="hidden items-center gap-10 text-sm text-gray-300 lg:flex">

          <a
            href="#hero"
            className="transition hover:text-cyan-400"
          >
            Home
          </a>

          <a
            href="#pipeline"
            className="transition hover:text-cyan-400"
          >
            Pipeline
          </a>

          <a
            href="#features"
            className="transition hover:text-cyan-400"
          >
            Features
          </a>

          <a
            href="#architecture"
            className="transition hover:text-cyan-400"
          >
            Architecture
          </a>

          <a
            href="#judge"
            className="transition hover:text-cyan-400"
          >
            Judge Mode
          </a>

        </nav>

        {/* Buttons */}

        <div className="flex items-center gap-3">

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="rounded-xl border border-white/10 p-3 transition hover:border-cyan-400 hover:bg-white/5"
          >
            <Globe className="h-5 w-5" />
          </a>

          <a
            href="/upload"
            className="flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-black transition hover:scale-105 hover:bg-cyan-400"
          >
            <Upload className="h-4 w-4" />
            Upload Script
          </a>

        </div>

      </div>
    </motion.header>
  );
}