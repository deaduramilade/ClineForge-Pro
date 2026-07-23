import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CineForge AI Pro',
  description:
    'Secure multimodal AI pipeline: Arabic & English scripts → storyboards, animatics, and budget estimates',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans min-h-screen bg-gray-950 text-gray-100">
        <header className="border-b border-gray-800 bg-gray-900 px-6 py-4">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-brand-500">
                🎬 CineForge AI Pro
              </span>
            </div>
            <nav className="flex items-center gap-6 text-sm text-gray-400">
              <a href="/upload" className="hover:text-white transition-colors">
                Upload Script
              </a>
              <a href="/storyboard" className="hover:text-white transition-colors">
                Storyboard
              </a>
              <a href="/judge" className="hover:text-white transition-colors">
                Judge Mode
              </a>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        <footer className="border-t border-gray-800 bg-gray-900 px-6 py-4 text-center text-xs text-gray-500">
          CineForge AI Pro — IBM SkillsBuild AI Builders Challenge 2026
        </footer>
      </body>
    </html>
  )
}
