import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Upload Script — CineForge AI Pro',
}

export default function UploadPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">Upload Script</h1>
        <p className="text-gray-400">
          Your script is encrypted client-side using AES-256-GCM before leaving your
          browser. Your intellectual property stays protected.
        </p>
      </div>

      {/* Upload area — TODO: wire to UploadForm component */}
      <div className="rounded-xl border-2 border-dashed border-gray-600 bg-gray-800/50 p-12 text-center">
        <div className="mb-4 text-5xl">📄</div>
        <p className="mb-2 text-lg font-medium">Drop your script here</p>
        <p className="mb-6 text-sm text-gray-400">
          Supports PDF, DOCX, and TXT — Arabic (RTL) and English
        </p>
        <label className="cursor-pointer rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">
          Choose File
          <input type="file" className="sr-only" accept=".pdf,.docx,.txt" />
        </label>
      </div>

      <div className="mt-6 rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 className="mb-2 text-sm font-semibold text-gray-300">
          🔒 Security Notice
        </h3>
        <ul className="space-y-1 text-xs text-gray-400">
          <li>• Script is encrypted with AES-256-GCM before upload</li>
          <li>• Encryption key is derived from your passphrase and never transmitted</li>
          <li>• Generated storyboards include C2PA provenance watermarks</li>
        </ul>
      </div>
    </div>
  )
}
