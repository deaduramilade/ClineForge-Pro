"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  Upload,
  FileSearch,
  Users,
  HeartPulse,
  BrainCircuit,
  Camera,
  Images,
  Download,
} from "lucide-react";

const nodes = [
  { title: "Upload Script", icon: Upload, color: "text-cyan-400" },
  { title: "Scene Parser", icon: FileSearch, color: "text-emerald-400" },
  { title: "Character AI", icon: Users, color: "text-orange-400" },
  { title: "Emotion AI", icon: HeartPulse, color: "text-pink-400" },
  { title: "Context AI", icon: BrainCircuit, color: "text-violet-400" },
  { title: "Director Engine", icon: BrainCircuit, color: "text-cyan-300" },
  { title: "Camera Planner", icon: Camera, color: "text-yellow-400" },
  { title: "Storyboard", icon: Images, color: "text-blue-400" },
  { title: "Export", icon: Download, color: "text-green-400" },
];

export default function Architecture() {
  return (
    <section
      id="architecture"
      className="relative overflow-hidden bg-[#040611] py-32"
    >
      {/* Ambient Background */}
      <div className="absolute inset-0">
        <div className="absolute left-0 top-0 h-[500px] w-[500px] rounded-full bg-cyan-500/10 blur-[180px]" />
        <div className="absolute right-0 bottom-0 h-[500px] w-[500px] rounded-full bg-violet-500/10 blur-[180px]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:48px_48px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="mx-auto mb-24 max-w-3xl text-center"
        >
          <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-300">
            AI System Architecture
          </span>

          <h2 className="mt-6 text-5xl font-bold text-white">
            The Intelligence Behind
            <span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
              {" "}CineForge AI
            </span>
          </h2>

          <p className="mt-6 text-lg leading-8 text-gray-400">
            Every screenplay flows through a multi-stage reasoning engine that
            extracts cinematic context, understands narrative intent, plans
            camera language, and generates production-ready storyboards.
          </p>
        </motion.div>

        {/* AI Architecture Graph */}
        <div className="relative mx-auto flex max-w-6xl flex-col items-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-12"
          >
            <Node icon={nodes[0].icon} title={nodes[0].title} color={nodes[0].color} />
          </motion.div>

          <Connector />

          <motion.div
            initial={{ opacity: 0, y: 25 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="my-10"
          >
            <Node icon={nodes[1].icon} title={nodes[1].title} color={nodes[1].color} />
          </motion.div>

          <Connector />

          <div className="grid w-full max-w-5xl grid-cols-1 gap-8 md:grid-cols-3">
            <Node icon={nodes[2].icon} title={nodes[2].title} color={nodes[2].color} />
            <Node icon={nodes[3].icon} title={nodes[3].title} color={nodes[3].color} />
            <Node icon={nodes[4].icon} title={nodes[4].title} color={nodes[4].color} />
          </div>

          <Connector />

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="my-12"
          >
            <Node icon={nodes[5].icon} title={nodes[5].title} color={nodes[5].color} />
          </motion.div>

          <Connector />

          <div className="grid w-full max-w-5xl grid-cols-1 gap-8 md:grid-cols-3">
            <Node icon={nodes[6].icon} title={nodes[6].title} color={nodes[6].color} />
            <Node icon={nodes[7].icon} title={nodes[7].title} color={nodes[7].color} />
            <Node icon={nodes[8].icon} title={nodes[8].title} color={nodes[8].color} />
          </div>
        </div>

        {/* Runtime Metrics */}
        <div className="mt-28 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {[
            { value: "243", label: "Backend Tests", description: "Passing integration & unit tests" },
            { value: "4", label: "AI Modules", description: "Scene, Emotion, Context & Director" },
            { value: "1.2s", label: "Scene Processing", description: "Average reasoning latency" },
            { value: "6", label: "Export Formats", description: "PDF, PNG, JSON and more" },
          ].map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 25 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.15 }}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-violet-500/5 opacity-0 transition duration-500 group-hover:opacity-100" />
              <div className="relative">
                <motion.h3
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.3 }}
                  className="text-5xl font-bold bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent"
                >
                  {item.value}
                </motion.h3>
                <h4 className="mt-4 text-xl font-semibold text-white">{item.label}</h4>
                <p className="mt-3 text-gray-400 leading-7">{item.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

type NodeProps = {
  icon: React.ElementType;
  title: string;
  color: string;
};

function Node({ icon: Icon, title, color }: NodeProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.05, y: -6 }}
      animate={{ y: [0, -5, 0] }}
      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      className="group relative"
    >
      <div className="absolute inset-0 rounded-3xl bg-cyan-500/10 opacity-0 blur-2xl transition duration-500 group-hover:opacity-100" />
      <div className="relative w-64 rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <div className={`mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 ${color}`}>
          <Icon size={30} />
        </div>
        <h3 className="text-xl font-semibold text-white">{title}</h3>
        <div className="mt-5 h-1 overflow-hidden rounded-full bg-white/10">
          <motion.div
            animate={{ x: ["-100%", "100%"] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
            className="h-full w-1/2 bg-gradient-to-r from-cyan-400 via-blue-400 to-violet-500"
          />
        </div>
      </div>
    </motion.div>
  );
}

function Connector() {
  return (
    <motion.div
      initial={{ height: 0 }}
      whileInView={{ height: 70 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="relative w-[2px] bg-white/10"
    >
      <motion.div
        animate={{ y: ["0%", "100%"] }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="absolute left-1/2 h-8 w-2 -translate-x-1/2 rounded-full bg-cyan-400 blur-sm"
      />
    </motion.div>
  );
}