'use client'

import { useRef, useState } from 'react'
import { uploadScript, ScriptUploadResponse } from '@/lib/api'
import { encryptFile } from '@/lib/crypto'
import { setActiveScript } from '@/lib/session'

type UploadState =
  | { status: 'idle' }
  | { status: 'uploading' }
  | { status: 'success'; result: ScriptUploadResponse; encrypted: boolean }
  | { status: 'error'; message: string }

export default function UploadPage() {
  const [state, setState] = useState<UploadState>({ status: 'idle' })
  const [encrypt, setEncrypt] = useState(true)
  const [passphrase, setPassphrase] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleFile(file: File) {
    if (encrypt && !passphrase) {
      setState({ status: 'error', message: 'Enter a passphrase, or turn off encryption.' })
      return
    }

    setState({ status: 'uploading' })
    try {
      let result: ScriptUploadResponse
      if (encrypt) {
        const plaintext = await file.arrayBuffer()
        const encryptedBuffer = await encryptFile(plaintext, passphrase)
        // Keep the original filename -- the parser dispatches on
        // extension, and that check runs *after* server-side decryption.
        result = await uploadScript(new Blob([encryptedBuffer]), file.name, passphrase)
      } else {
        result = await uploadScript(file, file.name)
      }
      setActiveScript(result.script_id)
      setState({ status: 'success', result, encrypted: encrypt })
    } catch (err) {
      setState({
        status: 'error',
        message: err instanceof Error ? err.message : 'Upload failed.',
      })
    }
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const busy = state.status === 'uploading'

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">Upload Script</h1>
        <p className="text-gray-400">
          Your script can be encrypted client-side using AES-256-GCM before
          leaving your browser. Parses into structured scenes (locations,
          characters, dialogue, mood) — Arabic, English, or mixed.
        </p>
      </div>

      <div className="mb-4 flex items-center justify-between rounded-lg border border-gray-700 bg-gray-800 px-4 py-3">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={encrypt}
            onChange={(e) => setEncrypt(e.target.checked)}
            disabled={busy}
          />
          Encrypt before upload (AES-256-GCM)
        </label>
      </div>

      {encrypt && (
        <div className="mb-4">
          <input
            type="password"
            placeholder="Passphrase (never stored, sent once per request)"
            value={passphrase}
            onChange={(e) => setPassphrase(e.target.value)}
            disabled={busy}
            className="w-full rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-sm text-gray-100 placeholder-gray-500"
          />
        </div>
      )}

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="rounded-xl border-2 border-dashed border-gray-600 bg-gray-800/50 p-12 text-center"
      >
        <div className="mb-4 text-5xl">📄</div>
        <p className="mb-2 text-lg font-medium">Drop your script here</p>
        <p className="mb-6 text-sm text-gray-400">
          Supports PDF, DOCX, and TXT — Arabic (RTL) and English
        </p>
        <label className="cursor-pointer rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">
          {busy ? 'Uploading…' : 'Choose File'}
          <input
            ref={inputRef}
            type="file"
            className="sr-only"
            accept=".pdf,.docx,.txt"
            disabled={busy}
            onChange={onInputChange}
          />
        </label>
      </div>

      {state.status === 'error' && (
        <div className="mt-6 rounded-lg border border-red-800 bg-red-950/50 p-4 text-sm text-red-300">
          {state.message}
        </div>
      )}

      {state.status === 'success' && (
        <div className="mt-6 rounded-lg border border-green-800 bg-green-950/30 p-4">
          <h3 className="mb-2 text-sm font-semibold text-green-300">
            ✅ Parsed successfully {state.encrypted && '(decrypted server-side)'}
          </h3>
          <dl className="grid grid-cols-2 gap-2 text-sm text-gray-300">
            <dt className="text-gray-500">Title</dt>
            <dd>{state.result.title || '—'}</dd>
            <dt className="text-gray-500">Language</dt>
            <dd>{state.result.language}</dd>
            <dt className="text-gray-500">Scenes detected</dt>
            <dd>{state.result.scene_count}</dd>
            <dt className="text-gray-500">Script ID</dt>
            <dd className="font-mono text-xs">{state.result.script_id}</dd>
          </dl>
          <div className="mt-4 flex gap-3">
            <a
              href="/storyboard"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              Continue to Storyboard →
            </a>
          </div>
        </div>
      )}

      <div className="mt-6 rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 className="mb-2 text-sm font-semibold text-gray-300">
          🔒 Security Notice
        </h3>
        <ul className="space-y-1 text-xs text-gray-400">
          <li>• Encryption is client-side AES-256-GCM (WebCrypto), key derived locally via PBKDF2</li>
          <li>• Passphrase is sent once per request over HTTPS for server-side decryption — never stored</li>
          <li>• This is client-side encryption with local key generation, not zero-knowledge (see SECURITY.md)</li>
          <li>• Generated storyboards include C2PA-inspired provenance watermarks</li>
        </ul>
      </div>
    </div>
  )
}
