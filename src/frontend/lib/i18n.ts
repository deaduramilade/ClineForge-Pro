/**
 * CineForge AI Pro — Internationalisation (i18n)
 *
 * Bilingual support: Arabic (RTL) and English (LTR)
 * TODO: expand with full translation dictionaries as UI grows
 */

export type Locale = 'en' | 'ar'

export const locales: Locale[] = ['en', 'ar']
export const defaultLocale: Locale = 'en'

export const localeNames: Record<Locale, string> = {
  en: 'English',
  ar: 'العربية',
}

export const localeDirections: Record<Locale, 'ltr' | 'rtl'> = {
  en: 'ltr',
  ar: 'rtl',
}

// ── Translation dictionaries ─────────────────────────────────────────────────

type TranslationKey =
  | 'nav.upload'
  | 'nav.storyboard'
  | 'nav.judge'
  | 'upload.title'
  | 'upload.description'
  | 'upload.dropzone'
  | 'upload.formats'
  | 'storyboard.title'
  | 'storyboard.description'
  | 'judge.title'
  | 'judge.description'

const translations: Record<Locale, Record<TranslationKey, string>> = {
  en: {
    'nav.upload': 'Upload Script',
    'nav.storyboard': 'Storyboard',
    'nav.judge': 'Judge Mode',
    'upload.title': 'Upload Script',
    'upload.description':
      'Your script is encrypted client-side using AES-256-GCM before leaving your browser.',
    'upload.dropzone': 'Drop your script here',
    'upload.formats': 'Supports PDF, DOCX, and TXT — Arabic (RTL) and English',
    'storyboard.title': 'Storyboard Canvas',
    'storyboard.description':
      'AI-generated storyboard frames for your script. Each frame includes a C2PA provenance watermark.',
    'judge.title': 'Live Judge Mode',
    'judge.description':
      'Real-time pipeline view for the IBM SkillsBuild AI Builders Challenge demo.',
  },
  ar: {
    'nav.upload': 'رفع النص',
    'nav.storyboard': 'لوحة القصة',
    'nav.judge': 'وضع التحكيم',
    'upload.title': 'رفع النص',
    'upload.description':
      'يتم تشفير النص على الجانب العميل باستخدام AES-256-GCM قبل مغادرة المتصفح.',
    'upload.dropzone': 'اسحب نصك هنا',
    'upload.formats': 'يدعم PDF وDOCX وTXT — العربية والإنجليزية',
    'storyboard.title': 'لوحة القصة المصورة',
    'storyboard.description':
      'إطارات القصة المصورة المولدة بالذكاء الاصطناعي. كل إطار يحمل علامة مائية C2PA.',
    'judge.title': 'وضع التحكيم المباشر',
    'judge.description': 'عرض خط الأنابيب في الوقت الفعلي لعرض تحدي IBM SkillsBuild.',
  },
}

export function t(key: TranslationKey, locale: Locale = defaultLocale): string {
  return translations[locale][key] ?? translations[defaultLocale][key] ?? key
}
