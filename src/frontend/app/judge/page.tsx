'use client'

import { useEffect, useState } from 'react'
import {
  getParsedScript,
  estimateBudget,
  getFrameCount,
  ParsedScriptResponse,
  BudgetResponse,
} from '@/lib/api'
import { getActiveScript } from '@/lib/session'

type StepStatus = 'pending' | 'done' | 'available'

interface Step {
  id: number
  label: string
  icon: string
  status: StepStatus
}

const POLL_INTERVAL_MS = 3000

export default function JudgePage() {
  const [script, setScript] = useState<ParsedScriptResponse | null>(null)
  const [budget, setBudget] = useState<BudgetResponse | null>(null)
  const [frameCount, setFrameCount] = useState(0)

  useEffect(() => {
    const scriptId = getActiveScript()
    if (!scriptId) return

    let cancelled = false

    async function poll() {
      const id = scriptId as string
      const [scriptResult, budgetResult, framesResult] = await Promise.allSettled([
        getParsedScript(id),
        estimateBudget(id),
        getFrameCount(id),
      ])
      if (cancelled) return
      if (scriptResult.status === 'fulfilled') setScript(scriptResult.value)
      if (budgetResult.status === 'fulfilled') setBudget(budgetResult.value)
      if (framesResult.status === 'fulfilled') setFrameCount(framesResult.value.frame_count)
    }

    poll()
    const interval = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const steps: Step[] = [
    { id: 1, label: 'Script Upload', icon: '📄', status: script ? 'done' : 'pending' },
    { id: 2, label: 'AES-256 Encryption', icon: '🔒', status: 'available' },
    { id: 3, label: 'Scene Parsing', icon: '📝', status: script ? 'done' : 'pending' },
    { id: 4, label: 'Storyboard Generation', icon: '🤖', status: frameCount > 0 ? 'done' : 'available' },
    { id: 5, label: 'C2PA-Inspired Watermarking', icon: '©️', status: frameCount > 0 ? 'done' : 'available' },
    { id: 6, label: 'Animatic Export', icon: '🎬', status: 'available' },
    { id: 7, label: 'Budget Estimate', icon: '💰', status: budget ? 'done' : 'pending' },
  ]

  const badge: Record<StepStatus, string> = {
    done: 'border-green-700 text-green-400',
    pending: 'border-gray-600 text-gray-400',
    available: 'border-blue-700 text-blue-400',
  }
  const label: Record<StepStatus, string> = {
    done: 'Done',
    pending: 'Pending',
    available: 'Ready — not yet run for this script',
  }

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
          {steps.map((step) => (
            <div
              key={step.id}
              className="flex items-center gap-4 rounded-lg bg-gray-700/50 px-4 py-3"
            >
              <span className="text-xl">{step.icon}</span>
              <span className="flex-1 text-sm font-medium">{step.label}</span>
              <span className={`rounded-full border px-2 py-0.5 text-xs ${badge[step.status]}`}>
                {label[step.status]}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div className="grid gap-6 sm:grid-cols-3">
        {[
          { label: 'Scenes Processed', value: script ? String(script.scene_count) : '—', unit: 'scenes' },
          { label: 'Frames Generated', value: String(frameCount), unit: 'frames' },
          {
            label: 'Budget Estimate',
            value: budget ? budget.total_estimated_cost.toLocaleString() : '—',
            unit: budget?.currency ?? 'USD',
          },
        ].map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-gray-700 bg-gray-800 p-6 text-center"
          >
            <div className="mb-1 text-3xl font-bold text-brand-500">{metric.value}</div>
            <div className="text-xs text-gray-500">{metric.unit}</div>
            <div className="mt-1 text-sm text-gray-400">{metric.label}</div>
          </div>
        ))}
      </div>

      {!script && (
        <div className="mt-8 rounded-lg border border-gray-700 bg-gray-800/50 p-6 text-center text-sm text-gray-500">
          Start the pipeline by uploading a script.{' '}
          <a href="/upload" className="text-brand-500 hover:underline">
            Upload Script →
          </a>
        </div>
      )}
    </div>
  )
}
