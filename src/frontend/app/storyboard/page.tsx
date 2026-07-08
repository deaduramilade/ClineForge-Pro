import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Storyboard Canvas — CineForge AI Pro',
}

export default function StoryboardPage() {
  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="mb-2 text-3xl font-bold">Storyboard Canvas</h1>
          <p className="text-gray-400">
            AI-generated storyboard frames for your script. Each frame includes a
            C2PA provenance watermark.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            disabled
            className="rounded-lg border border-gray-600 px-4 py-2 text-sm text-gray-400 opacity-50"
          >
            Export Animatic
          </button>
          <button
            disabled
            className="rounded-lg border border-gray-600 px-4 py-2 text-sm text-gray-400 opacity-50"
          >
            Budget Estimate
          </button>
        </div>
      </div>

      {/* Placeholder grid — TODO: wire to storyboard state */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="overflow-hidden rounded-xl border border-gray-700 bg-gray-800"
          >
            <div className="flex aspect-video items-center justify-center bg-gray-700 text-4xl text-gray-500">
              🎬
            </div>
            <div className="p-4">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-400">
                  Scene {i + 1}
                </span>
                <span className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-400">
                  ©️ C2PA
                </span>
              </div>
              <p className="text-sm text-gray-500">
                Scene description will appear here after generation.
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-lg border border-gray-700 bg-gray-800/50 p-6 text-center text-sm text-gray-500">
        Upload a script to generate storyboard frames.{' '}
        <a href="/upload" className="text-brand-500 hover:underline">
          Upload Script →
        </a>
      </div>
    </div>
  )
}
