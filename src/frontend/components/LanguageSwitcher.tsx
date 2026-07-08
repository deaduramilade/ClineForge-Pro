/**
 * LanguageSwitcher component
 *
 * Allows users to switch between Arabic (RTL) and English (LTR).
 * Updates the HTML dir attribute and locale.
 */

'use client'

import { localeNames, type Locale } from '@/lib/i18n'

interface LanguageSwitcherProps {
  currentLocale: Locale
  onChange: (locale: Locale) => void
}

export function LanguageSwitcher({ currentLocale, onChange }: LanguageSwitcherProps) {
  return (
    <div className="flex gap-2">
      {(Object.keys(localeNames) as Locale[]).map((locale) => (
        <button
          key={locale}
          onClick={() => onChange(locale)}
          className={`rounded-md px-3 py-1.5 text-sm transition ${
            currentLocale === locale
              ? 'bg-brand-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
          aria-label={`Switch to ${localeNames[locale]}`}
        >
          {localeNames[locale]}
        </button>
      ))}
    </div>
  )
}
