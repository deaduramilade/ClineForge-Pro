"use client";

import {
  Film,
  Globe,
  Mail,
} from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black/30 backdrop-blur">
      <div className="mx-auto max-w-7xl px-8 py-16">

        <div className="grid gap-12 md:grid-cols-3">

          {/* Logo */}

          <div>

            <div className="flex items-center gap-3">

              <Film className="h-8 w-8 text-cyan-400" />

              <div>

                <h2 className="text-2xl font-bold">
                  CineForge AI Pro
                </h2>

                <p className="text-sm text-gray-400">
                  AI Powered Film Production
                </p>

              </div>

            </div>

            <p className="mt-6 max-w-md leading-7 text-gray-400">

              Transforming multilingual screenplays into
              AI-generated storyboards through secure,
              modular and production-ready workflows.

            </p>

          </div>

          {/* Links */}

          <div>

            <h3 className="mb-5 text-lg font-semibold">

              Platform

            </h3>

            <ul className="space-y-3 text-gray-400">

              <li>
                <a href="/upload" className="hover:text-cyan-400">
                  Upload Script
                </a>
              </li>

              <li>
                <a href="/storyboard" className="hover:text-cyan-400">
                  Storyboard
                </a>
              </li>

              <li>
                <a href="/judge" className="hover:text-cyan-400">
                  Judge Mode
                </a>
              </li>

            </ul>

          </div>

          {/* Contact */}

          <div>

            <h3 className="mb-5 text-lg font-semibold">

              Connect

            </h3>

            <div className="flex gap-4">

              <a
                href="#"
                className="rounded-xl border border-white/10 p-3 hover:border-cyan-400"
              >
                <Globe className="h-5 w-5" />
              </a>

              <a
                href="#"
                className="rounded-xl border border-white/10 p-3 hover:border-cyan-400"
              >
                <Globe className="h-5 w-5" />
              </a>

              <a
                href="mailto:info@cineforge.ai"
                className="rounded-xl border border-white/10 p-3 hover:border-cyan-400"
              >
                <Mail className="h-5 w-5" />
              </a>

            </div>

          </div>

        </div>

        <div className="mt-12 border-t border-white/10 pt-8 text-center text-sm text-gray-500">

          © 2026 CineForge AI Pro • Built for the IBM SkillsBuild AI Builders Challenge

        </div>

      </div>
    </footer>
  );
}