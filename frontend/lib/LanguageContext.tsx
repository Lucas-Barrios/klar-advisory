'use client'
import { createContext, useContext, useState, ReactNode } from 'react'
import { translations, Lang } from './translations'

type ContextType = {
  lang: Lang
  setLang: (l: Lang) => void
  t: typeof translations.en
}

const LanguageContext = createContext<ContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('en')
  const t = translations[lang]
  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
