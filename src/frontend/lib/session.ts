/**
 * CineForge AI Pro — Active-script session helper
 *
 * MVP-scoped: keeps track of the most recently uploaded script_id in
 * localStorage so the Upload, Storyboard, and Judge Mode pages can share
 * state without a full client-side store. Not intended as a durable
 * multi-project history — just enough to demo the pipeline end-to-end.
 */

const ACTIVE_SCRIPT_KEY = 'cineforge:active_script_id'

export function setActiveScript(scriptId: string): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(ACTIVE_SCRIPT_KEY, scriptId)
}

export function getActiveScript(): string | null {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(ACTIVE_SCRIPT_KEY)
}

export function clearActiveScript(): void {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(ACTIVE_SCRIPT_KEY)
}
