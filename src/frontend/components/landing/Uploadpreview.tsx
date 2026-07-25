"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Upload, FileText, CheckCircle2, ArrowRight } from "lucide-react";

export default function UploadPreview() {
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setFileName(file.name);
  };

  return (
    <section className="relative overflow-hidden bg-[#050816] py-32">
      {/* Ambient Background */}
      <div className="absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[450px] w-[450px] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-[180px]" />
      </div>

      <div className="relative mx-auto max-w-5xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mx-auto mb-16 max-w-2xl text-center"
        >
          <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-300">
            Try It Now
          </span>

          <h2 className="mt-6 text-5xl font-bold text-white">
            Upload Your
            <span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
              {" "}Screenplay
            </span>
          </h2>

          <p className="mt-6 text-lg leading-8 text-gray-400">
            Drop in a script and see how CineForge parses scenes, characters,
            and camera direction before generating storyboards.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="rounded-[32px] border border-white/10 bg-white/5 p-10 backdrop-blur-xl"
        >
          <label
            htmlFor="script-upload"
            className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/15 px-6 py-16 text-center transition hover:border-cyan-400/50 hover:bg-white/5"
          >
            <div className="mb-5 rounded-2xl bg-cyan-500/10 p-4">
              <Upload className="h-8 w-8 text-cyan-400" />
            </div>

            <p className="text-lg font-semibold text-white">
              {fileName ? "Ready to process" : "Click to upload a screenplay"}
            </p>

            <p className="mt-2 text-sm text-gray-400">
              Supports .pdf, .fountain, .txt — up to 10MB
            </p>

            <input
              id="script-upload"
              type="file"
              accept=".pdf,.fountain,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          {fileName && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 flex items-center justify-between rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-6 py-4"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-emerald-400" />
                <span className="text-white">{fileName}</span>
              </div>

              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="h-5 w-5" />
                <span className="text-sm font-medium">Ready</span>
              </div>
            </motion.div>
          )}

          <button
            disabled={!fileName}
            className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-8 py-4 font-semibold text-black transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-gray-500"
          >
            Start Processing
            <ArrowRight className="h-5 w-5" />
          </button>
        </motion.div>
      </div>
    </section>
  );
}