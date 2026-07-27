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
  title: string
  language: string
  scene_count: number
}

export interface SceneMetadata {
  index: number
  heading: string
  description: string
  characters: string[]
  location: string
  time_of_day: string
  mood: string
  dialogue: string[]
  language: string
}

export interface ParsedScriptResponse {
  script_id: string
  title: string
  language: string
  scene_count: number
  characters: string[]
  locations: string[]
  scenes: SceneMetadata[]
}

export async function getParsedScript(scriptId: string): Promise<ParsedScriptResponse> {
  return request<ParsedScriptResponse>(`/api/scripts/${scriptId}`)
}

/**
 * Upload a script file.
 *
 * If `passphrase` is provided, `fileOrBlob` MUST already be AES-256-GCM
 * encrypted with that same passphrase (see lib/crypto.ts's encryptFile())
 * -- the backend will decrypt it server-side before parsing. If
 * `passphrase` is omitted, the file is uploaded as plaintext.
 */
export async function uploadScript(
  fileOrBlob: Blob,
  filename: string,
  passphrase?: string,
): Promise<ScriptUploadResponse> {
  const formData = new FormData()
  formData.append('file', fileOrBlob, filename)
  if (passphrase) {
    formData.append('passphrase', passphrase)
  }

  return request<ScriptUploadResponse>('/api/scripts/upload', {
    method: 'POST',
    body: formData,
  })
}

// ── Generate ─────────────────────────────────────────────────────────────────

export interface StoryboardResponse {
  scene_index: number
  image_data_b64: string
  mime_type: string
  provider_id: string
  model_id: string
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

/** Build a displayable data: URI from a StoryboardResponse. */
export function storyboardImageUrl(frame: StoryboardResponse): string {
  return `data:${frame.mime_type};base64,${frame.image_data_b64}`
}

export interface FrameCountResponse {
  script_id: string
  frame_count: number
}

export async function getFrameCount(scriptId: string): Promise<FrameCountResponse> {
  return request<FrameCountResponse>(`/api/generate/frames/${scriptId}`)
}

// ── Animatic ────────────────────────────────────────────────────────────────

export interface AnimaticResponse {
  script_id: string
  export_url: string
  format: string
  duration_seconds: number
  frame_count: number
}

/**
 * Export previously-generated storyboard frames as a motion animatic.
 * 'gif' works with no server-side system dependency; 'mp4' requires
 * ffmpeg to be installed on the backend host.
 */
export async function exportAnimatic(
  scriptId: string,
  format: 'gif' | 'mp4' = 'gif',
  frameDurationMs = 2000,
): Promise<AnimaticResponse> {
  return request<AnimaticResponse>('/api/animatic/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_id: scriptId,
      format,
      frame_duration_ms: frameDurationMs,
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
