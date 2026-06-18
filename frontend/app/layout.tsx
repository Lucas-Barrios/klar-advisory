import type { Metadata } from 'next'
import { Space_Grotesk } from 'next/font/google'
import './globals.css'
import { LanguageProvider } from '@/lib/LanguageContext'
import Nav from './components/Nav'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-space-grotesk',
})

const description =
  'Free AI-powered readiness diagnostic for Latin Americans pursuing university, Ausbildung, or work visa pathways in Germany.'

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL ?? 'http://localhost:3000'),
  title: 'Klar — Your clear path to Germany',
  description,
  openGraph: {
    title: 'Klar — Your clear path to Germany',
    description,
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Klar — Your clear path to Germany',
    description,
  },
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
          <Nav />
          <main className="flex-1">{children}</main>
        </LanguageProvider>
      </body>
    </html>
  )
}
