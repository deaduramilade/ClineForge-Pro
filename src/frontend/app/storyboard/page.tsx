'use client'

import { useEffect, useState } from 'react'
import {
  getParsedScript,
  estimateBudget,
  generateStoryboardFrame,
  exportAnimatic,
  storyboardImageUrl,
  ParsedScriptResponse,
  BudgetResponse,
  StoryboardResponse,
} from '@/lib/api'
import { getActiveScript } from '@/lib/session'

type FrameState =
  | { status: 'idle' }
  | { status: 'generating' }
  | { status: 'done'; frame: StoryboardResponse }
  | { status: 'error'; message: string }

export default function StoryboardPage() {
  const [script, setScript] = useState<ParsedScriptResponse | null>(null)
  const [budget, setBudget] = useState<BudgetResponse | null>(null)
  const [frames, setFrames] = useState<Record<number, FrameState>>({})
  const [loading, setLoading] = useState(true)
  const [budgetLoading, setBudgetLoading] = useState(false)
  const [animaticLoading, setAnimaticLoading] = useState(false)
  const [animaticUrl, setAnimaticUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const scriptId = getActiveScript()
    if (!scriptId) {
      setLoading(false)
      return
    }
    getParsedScript(scriptId)
      .then(setScript)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load script.'))
      .finally(() => setLoading(false))
  }, [])

  const generatedCount = Object.values(frames).filter((f) => f.status === 'done').length

  async function handleGenerateFrame(sceneIndex: number) {
    if (!script) return
    setFrames((prev) => ({ ...prev, [sceneIndex]: { status: 'generating' } }))
    try {
      const frame = await generateStoryboardFrame(script.script_id, sceneIndex)
      setFrames((prev) => ({ ...prev, [sceneIndex]: { status: 'done', frame } }))
    } catch (err) {
      setFrames((prev) => ({
        ...prev,
        [sceneIndex]: {
          status: 'error',
          message: err instanceof Error ? err.message : 'Generation failed.',
        },
      }))
    }
  }

  async function handleGenerateAll() {
    if (!script) return
    for (const scene of script.scenes) {
      await handleGenerateFrame(scene.index)
    }
  }

  async function handleBudgetEstimate() {
    if (!script) return
    setBudgetLoading(true)
    try {
      const result = await estimateBudget(script.script_id)
      setBudget(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Budget estimate failed.')
    } finally {
      setBudgetLoading(false)
    }
  }

  async function handleExportAnimatic() {
    if (!script) return
    setAnimaticLoading(true)
    setAnimaticUrl(null)
    try {
      // GIF has no server-side system dependency (mp4 needs ffmpeg on the
      // host), so it's the safer default for a demo environment.
      const result = await exportAnimatic(script.script_id, 'gif')
      setAnimaticUrl(result.export_url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Animatic export failed.')
    } finally {
      setAnimaticLoading(false)
    }
  }

  if (loading) {
    return <p className="text-gray-400">Loading…</p>
  }

  if (!script) {
    return (
      <div className="mt-8 rounded-lg border border-gray-700 bg-gray-800/50 p-6 text-center text-sm text-gray-500">
        No script loaded yet.{' '}
        <a href="/upload" className="text-brand-500 hover:underline">
          Upload Script →
        </a>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="mb-2 text-3xl font-bold">Storyboard Canvas</h1>
          <p className="text-gray-400">
            {script.title || 'Untitled script'} — {script.scene_count} scene
            {script.scene_count === 1 ? '' : 's'} detected ({script.language})
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExportAnimatic}
            disabled={animaticLoading || generatedCount === 0}
            title={generatedCount === 0 ? 'Generate at least one frame first' : undefined}
            className="rounded-lg border border-gray-600 px-4 py-2 text-sm text-gray-200 transition hover:border-brand-500 disabled:opacity-50"
          >
            {animaticLoading ? 'Exporting…' : 'Export Animatic'}
          </button>
          <button
            onClick={handleBudgetEstimate}
            disabled={budgetLoading}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            {budgetLoading ? 'Estimating…' : 'Budget Estimate'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-950/50 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {animaticUrl && (
        <div className="mb-8 rounded-xl border border-gray-700 bg-gray-800 p-6 text-center">
          <h2 className="mb-4 text-lg font-semibold">Animatic</h2>
          {/* eslint-disable-next-line @next/next/no-img-element -- data: URI, not an optimizable remote image */}
          <img src={animaticUrl} alt="Exported animatic" className="mx-auto rounded-lg" />
        </div>
      )}

      {budget && (
        <div className="mb-8 rounded-xl border border-gray-700 bg-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold">
            Budget Estimate — {budget.total_estimated_cost.toLocaleString()}{' '}
            {budget.currency}
          </h2>
          <div className="space-y-2">
            {budget.line_items.map((item) => (
              <div
                key={item.category}
                className="flex items-center justify-between rounded-lg bg-gray-700/50 px-4 py-2 text-sm"
              >
                <div>
                  <span className="font-medium">{item.category}</span>
                  <span className="ml-2 text-gray-400">{item.description}</span>
                </div>
                <span className="font-mono">
                  {item.estimated_cost.toLocaleString()} {item.currency}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Scenes {generatedCount > 0 && `(${generatedCount}/${script.scenes.length} generated)`}
        </h2>
        <button
          onClick={handleGenerateAll}
          className="rounded-lg border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:border-brand-500"
        >
          Generate All
        </button>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {script.scenes.map((scene) => {
          const frameState = frames[scene.index] ?? { status: 'idle' }
          return (
            <div
              key={scene.index}
              className="overflow-hidden rounded-xl border border-gray-700 bg-gray-800"
            >
              <div className="flex aspect-video items-center justify-center bg-gray-700 text-sm text-gray-500">
                {frameState.status === 'done' ? (
                  // eslint-disable-next-line @next/next/no-img-element -- data: URI
                  <img
                    src={storyboardImageUrl(frameState.frame)}
                    alt={`Storyboard frame for scene ${scene.index + 1}`}
                    className="h-full w-full object-cover"
                  />
                ) : frameState.status === 'generating' ? (
                  'Generating…'
                ) : frameState.status === 'error' ? (
                  <span className="px-4 text-center text-red-400">{frameState.message}</span>
                ) : (
                  <button
                    onClick={() => handleGenerateFrame(scene.index)}
                    className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700"
                  >
                    Generate Frame
                  </button>
                )}
              </div>
              <div className="p-4">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-400">
                    Scene {scene.index + 1} — {scene.heading || 'Untitled'}
                  </span>
                  <span className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-500">
                    {scene.location || '—'}
                  </span>
                </div>
                {frameState.status === 'done' && (
                  <span className="mb-1 inline-block rounded bg-green-900/50 px-2 py-0.5 text-xs text-green-400">
                    ✓ {frameState.frame.provider_id} · watermarked
                  </span>
                )}
                <p
                  className="text-sm text-gray-500"
                  style={{
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {scene.description || 'No description parsed.'}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
