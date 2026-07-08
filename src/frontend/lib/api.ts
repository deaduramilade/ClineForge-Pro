/**
 * CineForge AI Pro — Typed API client
 *
 * All requests to the backend API should go through this module.
 * Script uploads must use encryptFile() from lib/crypto.ts before calling uploadScript().
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(response.status, body.detail ?? 'Unknown error')
  }

  return response.json() as Promise<T>
}

// ── Health ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  timestamp: string
  version: string
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

// ── Scripts ─────────────────────────────────────────────────────────────────

export interface ScriptUploadResponse {
  script_id: string
  filename: string
  size_bytes: number
  message: string
}

/**
 * Upload an AES-256-encrypted script file.
 *
 * IMPORTANT: encryptedBlob must already be AES-256-GCM encrypted.
 * Never pass a plaintext file to this function.
 */
export async function uploadScript(
  encryptedBlob: Blob,
  filename: string,
): Promise<ScriptUploadResponse> {
  const formData = new FormData()
  formData.append('file', encryptedBlob, filename)

  return request<ScriptUploadResponse>('/api/scripts/upload', {
    method: 'POST',
    body: formData,
  })
}

// ── Generate ─────────────────────────────────────────────────────────────────

export interface StoryboardResponse {
  scene_index: number
  image_url: string
  watermarked: boolean
  style: string
  generation_time_ms: number
}

export async function generateStoryboardFrame(
  scriptId: string,
  sceneIndex: number,
  style = 'cinematic',
  language = 'en',
): Promise<StoryboardResponse> {
  return request<StoryboardResponse>('/api/generate/storyboard', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_id: scriptId,
      scene_index: sceneIndex,
      style,
      language,
    }),
  })
}

// ── Budget ───────────────────────────────────────────────────────────────────

export interface BudgetLineItem {
  category: string
  description: string
  estimated_cost: number
  currency: string
}

export interface BudgetResponse {
  script_id: string
  currency: string
  region: string
  total_estimated_cost: number
  line_items: BudgetLineItem[]
}

export async function estimateBudget(
  scriptId: string,
  currency = 'USD',
  region = 'international',
): Promise<BudgetResponse> {
  return request<BudgetResponse>('/api/budget/estimate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script_id: scriptId, currency, region }),
  })
}
