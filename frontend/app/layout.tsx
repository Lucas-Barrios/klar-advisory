import type { Metadata } from 'next'
import { Space_Grotesk } from 'next/font/google'
import Link from 'next/link'
import './globals.css'
import { LanguageProvider } from '@/lib/LanguageContext'
import LanguageToggle from './components/LanguageToggle'
import GermanFlag from '@/components/GermanFlag'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-space-grotesk',
})

export const metadata: Metadata = {
  title: 'Klar — Your clear path to Germany',
  description:
    'Free AI-powered readiness diagnostic for Latin Americans pursuing university, Ausbildung, or work visa pathways in Germany.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col" style={{ background: '#0A0E1A', color: '#F9FAFB' }}>
        <LanguageProvider>
          <nav
            style={{
              background: 'rgba(10,14,26,0.8)',
              backdropFilter: 'blur(12px)',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              position: 'sticky',
              top: 0,
              zIndex: 50,
            }}
          >
            <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
              <Link
                href="/"
                className="font-bold text-xl"
                style={{ color: '#F9FAFB', letterSpacing: '-0.02em' }}
              >
                Klar <GermanFlag size={20} />
              </Link>
              <div className="flex items-center gap-4">
                <LanguageToggle />
              </div>
            </div>
          </nav>
          <main className="flex-1">{children}</main>
        </LanguageProvider>
      </body>
    </html>
  )
}
