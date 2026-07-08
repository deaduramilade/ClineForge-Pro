export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h1 className="mb-4 text-5xl font-bold text-brand-500">
        🎬 CineForge AI Pro
      </h1>
      <p className="mb-8 max-w-2xl text-lg text-gray-400">
        Transform your Arabic &amp; English scripts into professional storyboards,
        motion animatics, and production budget estimates — powered by IBM Granite.
      </p>

      <div className="grid gap-6 sm:grid-cols-3">
        <a
          href="/upload"
          className="group rounded-xl border border-gray-700 bg-gray-800 p-6 text-left transition hover:border-brand-500 hover:bg-gray-750"
        >
          <div className="mb-3 text-3xl">📄</div>
          <h2 className="mb-2 text-lg font-semibold group-hover:text-brand-500">
            Upload Script
          </h2>
          <p className="text-sm text-gray-400">
            Upload your script (PDF, DOCX, or TXT). Client-side AES-256 encryption
            protects your IP.
          </p>
        </a>

        <a
          href="/storyboard"
          className="group rounded-xl border border-gray-700 bg-gray-800 p-6 text-left transition hover:border-brand-500"
        >
          <div className="mb-3 text-3xl">🎨</div>
          <h2 className="mb-2 text-lg font-semibold group-hover:text-brand-500">
            Storyboard Canvas
          </h2>
          <p className="text-sm text-gray-400">
            View AI-generated storyboard frames for each scene. All frames are
            C2PA-watermarked.
          </p>
        </a>

        <a
          href="/judge"
          className="group rounded-xl border border-gray-700 bg-gray-800 p-6 text-left transition hover:border-brand-500"
        >
          <div className="mb-3 text-3xl">⚡</div>
          <h2 className="mb-2 text-lg font-semibold group-hover:text-brand-500">
            Live Judge Mode
          </h2>
          <p className="text-sm text-gray-400">
            Real-time demo dashboard showing the full pipeline — perfect for the
            IBM SkillsBuild demo.
          </p>
        </a>
      </div>

      <div className="mt-12 rounded-lg border border-gray-700 bg-gray-800/50 px-8 py-4 text-sm text-gray-500">
        IBM SkillsBuild AI Builders Challenge — July 2026
      </div>
    </div>
  )
}
