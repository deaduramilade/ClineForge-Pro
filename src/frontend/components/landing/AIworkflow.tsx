"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  FileSearch,
  BrainCircuit,
  Camera,
  Images,
  CheckCircle2,
} from "lucide-react";

const steps = [
  {
    title: "Uploading Screenplay",
    icon: Upload,
  },
  {
    title: "Parsing Script",
    icon: FileSearch,
  },
  {
    title: "Reasoning",
    icon: BrainCircuit,
  },
  {
    title: "Planning Camera",
    icon: Camera,
  },
  {
    title: "Generating Storyboards",
    icon: Images,
  },
  {
    title: "Completed",
    icon: CheckCircle2,
  },
];

/**
 * Animated pipeline-steps indicator, auto-advancing every 2.5s on a loop.
 *
 * NOTE: not currently imported/used anywhere in the app (verified via
 * grep before this fix) -- it duplicates Pipeline.tsx's static step list.
 * Fixed to be valid, working code (it previously had hooks and JSX
 * sitting at module top level with no component wrapper or export at
 * all, so it could not have been imported successfully by anything).
 * Left in place rather than deleted since removing someone else's
 * in-progress work wasn't asked for -- wire it into a page or delete it
 * as you see fit.
 */
export default function AIWorkflow() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev + 1) % steps.length);
    }, 2500);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      {steps.map((step, index) => {
        const Icon = step.icon;

        return (
          <div key={step.title} className="flex items-center gap-5">
            <div
              className={`rounded-xl p-4 ${
                index <= active
                  ? "bg-cyan-500 text-black"
                  : "bg-white/10 text-white"
              }`}
            >
              <Icon size={24} />
            </div>

            <div className="flex-1">
              <div className="flex justify-between">
                <span className="text-white">{step.title}</span>

                <span className="text-cyan-300">
                  {index < active
                    ? "Done"
                    : index === active
                      ? "Running"
                      : "Waiting"}
                </span>
              </div>

              <div className="mt-2 h-2 rounded-full bg-white/10">
                <motion.div
                  animate={{
                    width: index <= active ? "100%" : "0%",
                  }}
                  transition={{
                    duration: 1,
                  }}
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500"
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
