import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Live Judge Mode — CineForge AI Pro',
}

const pipelineSteps = [
  { id: 1, label: 'Script Upload', icon: '📄', status: 'pending' },
  { id: 2, label: 'AES-256 Encryption', icon: '🔒', status: 'pending' },
  { id: 3, label: 'Scene Parsing', icon: '📝', status: 'pending' },
  { id: 4, label: 'Granite Generation', icon: '🤖', status: 'pending' },
  { id: 5, label: 'C2PA Watermarking', icon: '©️', status: 'pending' },
  { id: 6, label: 'Animatic Export', icon: '🎬', status: 'pending' },
  { id: 7, label: 'Budget Estimate', icon: '💰', status: 'pending' },
] as const

export default function JudgePage() {
  return (
    <div>
      <div className="mb-8">
        <div className="mb-2 flex items-center gap-3">
          <span className="rounded-full bg-red-600 px-3 py-1 text-xs font-bold uppercase tracking-wider text-white">
            ● Live
          </span>
          <h1 className="text-3xl font-bold">Judge Mode Dashboard</h1>
        </div>
        <p className="text-gray-400">
          Real-time pipeline view for the IBM SkillsBuild AI Builders Challenge demo.
        </p>
      </div>

      {/* Pipeline status */}
      <div className="mb-8 rounded-xl border border-gray-700 bg-gray-800 p-6">
        <h2 className="mb-4 text-lg font-semibold">Pipeline Status</h2>
        <div className="space-y-3">
          {pipelineSteps.map((step) => (
            <div
              key={step.id}
              className="flex items-center gap-4 rounded-lg bg-gray-700/50 px-4 py-3"
            >
              <span className="text-xl">{step.icon}</span>
              <span className="flex-1 text-sm font-medium">{step.label}</span>
              <span className="rounded-full border border-gray-600 px-2 py-0.5 text-xs text-gray-400">
                Pending
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div className="grid gap-6 sm:grid-cols-3">
        {[
          { label: 'Scenes Processed', value: '—', unit: 'scenes' },
          { label: 'Frames Generated', value: '—', unit: 'frames' },
          { label: 'Budget Estimate', value: '—', unit: 'USD' },
        ].map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-gray-700 bg-gray-800 p-6 text-center"
          >
            <div className="mb-1 text-3xl font-bold text-brand-500">
              {metric.value}
            </div>
            <div className="text-xs text-gray-500">{metric.unit}</div>
            <div className="mt-1 text-sm text-gray-400">{metric.label}</div>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-lg border border-gray-700 bg-gray-800/50 p-6 text-center text-sm text-gray-500">
        Start the pipeline by uploading a script.{' '}
        <a href="/upload" className="text-brand-500 hover:underline">
          Upload Script →
        </a>
      </div>
    </div>
  )
}
