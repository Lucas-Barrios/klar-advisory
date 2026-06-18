'use client'
import { useState, useEffect } from 'react'
import { FileText, Lock, ChevronDown, ChevronUp } from 'lucide-react'
import { useLanguage } from '@/lib/LanguageContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ─── Types ────────────────────────────────────────────────────────────────────

type CVEntry = { zeitraum: string; beschreibung: string }
type SprachEntry = { sprache: string; niveau: string }
type CVData = {
  profil: string
  ausbildung: CVEntry[]
  berufserfahrung: CVEntry[]
  sprachkenntnisse: SprachEntry[]
  kompetenzen: string[]
}
type Documents = {
  cv: CVData
  anschreiben: string
  cv_de?: CVData
  anschreiben_de?: string
  cv_target?: CVData | null
  anschreiben_target?: string | null
}

// ─── Placeholder highlighting ─────────────────────────────────────────────────

function HighlightedText({ text }: { text: string }) {
  const parts = text.split(/(\[[^\]]*\])/g)
  return (
    <>
      {parts.map((part, i) =>
        /^\[[^\]]*\]$/.test(part) ? (
          <span
            key={i}
            style={{
              background: 'rgba(245,158,11,0.15)',
              color: '#F59E0B',
              padding: '0 3px',
              borderRadius: 3,
              fontWeight: 500,
            }}
          >
            {part}
          </span>
        ) : (
          part
        )
      )}
    </>
  )
}

// ─── Collapsible CV column ────────────────────────────────────────────────────

function CVColumn({ cv, anschreiben }: { cv: CVData; anschreiben: string }) {
  const [open, setOpen] = useState(false)

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>
          Profile
        </div>
        <p style={{ fontSize: 13, color: '#D1D5DB', lineHeight: 1.65, margin: 0 }}>
          <HighlightedText text={cv.profil} />
        </p>
      </div>

      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'none',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 8,
          padding: '5px 11px',
          fontSize: 11,
          color: '#9CA3AF',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          marginBottom: 12,
        }}
      >
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {open ? 'Collapse full CV' : 'Expand full CV'}
      </button>

      {open && (
        <div style={{ fontSize: 13, color: '#D1D5DB', lineHeight: 1.65, marginBottom: 12 }}>
          {cv.ausbildung?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 700, color: '#9CA3AF', marginBottom: 5, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Education</div>
              {cv.ausbildung.map((e, i) => (
                <div key={i} style={{ marginBottom: 5, paddingLeft: 10, borderLeft: '2px solid rgba(37,99,235,0.3)' }}>
                  <div style={{ color: '#F59E0B', fontSize: 11, fontWeight: 600 }}><HighlightedText text={e.zeitraum} /></div>
                  <div><HighlightedText text={e.beschreibung} /></div>
                </div>
              ))}
            </div>
          )}
          {cv.berufserfahrung?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 700, color: '#9CA3AF', marginBottom: 5, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Experience</div>
              {cv.berufserfahrung.map((e, i) => (
                <div key={i} style={{ marginBottom: 5, paddingLeft: 10, borderLeft: '2px solid rgba(37,99,235,0.3)' }}>
                  <div style={{ color: '#F59E0B', fontSize: 11, fontWeight: 600 }}><HighlightedText text={e.zeitraum} /></div>
                  <div><HighlightedText text={e.beschreibung} /></div>
                </div>
              ))}
            </div>
          )}
          {cv.sprachkenntnisse?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 700, color: '#9CA3AF', marginBottom: 5, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Languages</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {cv.sprachkenntnisse.map((s, i) => (
                  <span key={i} style={{ fontSize: 12, color: '#D1D5DB' }}>
                    {s.sprache}{' '}
                    <span style={{ background: 'rgba(37,99,235,0.2)', color: '#60A5FA', border: '1px solid rgba(37,99,235,0.3)', borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 700 }}>
                      {s.niveau}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}
          {cv.kompetenzen?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 700, color: '#9CA3AF', marginBottom: 5, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Skills</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                {cv.kompetenzen.map((k, i) => (
                  <span key={i} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 9999, padding: '2px 10px', fontSize: 11, color: '#D1D5DB' }}>
                    {k}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
          Cover Letter
        </div>
        <div style={{
          background: 'rgba(255,255,255,0.025)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: 8,
          padding: '12px 14px',
          fontSize: 12,
          color: '#D1D5DB',
          lineHeight: 1.7,
          whiteSpace: 'pre-wrap',
        }}>
          <HighlightedText text={anschreiben} />
        </div>
      </div>
    </div>
  )
}

// ─── Premium PDF ──────────────────────────────────────────────────────────────

type RgbColor = [number, number, number]

function tokenize(text: string) {
  return text.split(/(\[[^\]]*\])/g).filter(s => s.length > 0).map(s => ({
    text: s,
    isPlaceholder: /^\[[^\]]*\]$/.test(s),
  }))
}

function renderLineTokens(
  doc: any,
  tokens: { text: string; isPlaceholder: boolean }[],
  x: number,
  y: number,
  normal: RgbColor,
) {
  let cx = x
  for (const { text, isPlaceholder } of tokens) {
    doc.setTextColor(...(isPlaceholder ? ([245, 158, 11] as RgbColor) : normal))
    doc.text(text, cx, y)
    cx += doc.getTextWidth(text)
  }
}

function renderStyledParagraph(
  doc: any,
  text: string,
  x: number,
  startY: number,
  maxWidth: number,
  lineHeight: number,
  normal: RgbColor = [209, 213, 219],
): number {
  const allTokens = tokenize(text)
  const words: { text: string; isPlaceholder: boolean }[] = []
  for (const tok of allTokens) {
    if (tok.isPlaceholder) {
      words.push(tok)
    } else {
      tok.text.split(/( )/).filter(s => s.length > 0).forEach(w =>
        words.push({ text: w, isPlaceholder: false })
      )
    }
  }

  let lineTokens: { text: string; isPlaceholder: boolean }[] = []
  let lineWidth = 0
  let curY = startY

  const flush = () => {
    if (!lineTokens.length) return
    renderLineTokens(doc, lineTokens, x, curY, normal)
    curY += lineHeight
    lineTokens = []
    lineWidth = 0
  }

  for (const word of words) {
    const w = doc.getTextWidth(word.text)
    if (lineWidth + w > maxWidth && lineTokens.length > 0 && word.text !== ' ') {
      flush()
    }
    lineTokens.push(word)
    lineWidth += w
  }
  flush()

  doc.setTextColor(0, 0, 0)
  return curY
}

async function generatePremiumPdf(
  cvData: CVData,
  anschreiben: string,
  langLabel: string,
  filename: string,
) {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })

  const W = 210, H = 297
  const ML = 15, MR = 15, MT = 34, MB = 14
  const BLUE: RgbColor = [37, 99, 235]
  const BLUE_LIGHT: RgbColor = [96, 165, 250]
  const DARK_BG: RgbColor = [18, 22, 38]
  const MID: RgbColor = [107, 114, 128]
  const LIGHT: RgbColor = [209, 213, 219]
  const WHITE: RgbColor = [249, 250, 251]
  const AMBER: RgbColor = [245, 158, 11]

  const SIDEBAR_W = 46
  const CONTENT_X = ML + SIDEBAR_W + 7
  const CONTENT_W = W - CONTENT_X - MR
  const LH = 4.8
  const LH_SM = 4.2

  const drawHeader = (subtitle: string) => {
    doc.setFillColor(...BLUE)
    doc.rect(0, 0, W, 28, 'F')
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(17)
    doc.setTextColor(...WHITE)
    doc.text('Klar', ML, 11)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.5)
    doc.text('klar-advisory.com', W - MR, 11, { align: 'right' })
    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.text(subtitle, ML, 21)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.5)
    doc.setTextColor(180, 200, 255)
    doc.text(langLabel, W - MR, 21, { align: 'right' })
  }

  const drawFooter = () => {
    doc.setDrawColor(40, 45, 65)
    doc.setLineWidth(0.3)
    doc.line(ML, H - MB + 1, W - MR, H - MB + 1)
    doc.setTextColor(...MID)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(6.5)
    doc.text(
      'Generated by Klar · klar-advisory.com · Fill all [bracketed] fields before sending',
      W / 2, H - MB + 5, { align: 'center' },
    )
  }

  const checkBreak = (curY: number, need: number): number => {
    if (curY + need > H - MB - 10) {
      doc.addPage()
      drawHeader('Lebenslauf / CV')
      drawFooter()
      // Redraw sidebar background on new page
      doc.setFillColor(...DARK_BG)
      doc.rect(ML - 2, MT - 4, SIDEBAR_W + 4, H - MT - MB + 4, 'F')
      return MT
    }
    return curY
  }

  // ── PAGE 1: Lebenslauf ─────────────────────────────────────────────────────
  drawHeader('Lebenslauf / CV')
  drawFooter()

  // Sidebar dark background panel
  doc.setFillColor(...DARK_BG)
  doc.rect(ML - 2, MT - 4, SIDEBAR_W + 4, H - MT - MB + 4, 'F')

  let sy = MT  // sidebar y

  // Photo placeholder
  doc.setDrawColor(...BLUE_LIGHT)
  doc.setLineWidth(0.5)
  doc.rect(ML, sy, 34, 40)
  doc.setFont('helvetica', 'italic')
  doc.setFontSize(8)
  doc.setTextColor(...MID)
  doc.text('[ Foto ]', ML + 17, sy + 22, { align: 'center' })
  sy += 46

  // Sidebar heading helper
  const sideHead = (label: string) => {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(7)
    doc.setTextColor(...BLUE_LIGHT)
    doc.text(label, ML, sy)
    sy += 4.5
  }

  // Contact
  sideHead('KONTAKT')
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.5)
  for (const c of ['[Ihre Adresse]', '[PLZ, Ort]', '[Telefon]', '[E-Mail]']) {
    doc.setTextColor(...AMBER)
    doc.text(c, ML, sy)
    sy += 4
  }
  sy += 4

  // Languages
  sideHead('SPRACHEN')
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.5)
  for (const s of (cvData.sprachkenntnisse ?? [])) {
    doc.setTextColor(...LIGHT)
    doc.text(s.sprache, ML, sy)
    const bx = ML + SIDEBAR_W - 16
    doc.setFillColor(...BLUE)
    doc.roundedRect(bx, sy - 3.3, 13, 4.6, 1, 1, 'F')
    doc.setTextColor(...WHITE)
    doc.setFontSize(6.5)
    doc.text(s.niveau, bx + 6.5, sy, { align: 'center' })
    doc.setFontSize(7.5)
    sy += 5
  }
  sy += 4

  // Skills
  sideHead('KOMPETENZEN')
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  for (const skill of (cvData.kompetenzen ?? [])) {
    const sw = doc.getTextWidth(skill) + 6
    doc.setFillColor(28, 34, 52)
    doc.roundedRect(ML, sy - 3.2, Math.min(sw, SIDEBAR_W - 2), 4.6, 1, 1, 'F')
    doc.setTextColor(...LIGHT)
    doc.text(skill.slice(0, 22), ML + 3, sy)
    sy += 5.5
  }

  // ── Right content ───────────────────────────────────────────────────────────
  let ry = MT

  const contentSection = (title: string) => {
    ry = checkBreak(ry, 14)
    doc.setFillColor(...BLUE)
    doc.rect(CONTENT_X - 5, ry, 3, 7, 'F')
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.setTextColor(...WHITE)
    doc.text(title, CONTENT_X, ry + 5.5)
    ry += 10
  }

  // Profil
  contentSection('Profil')
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  ry = renderStyledParagraph(doc, cvData.profil, CONTENT_X, ry, CONTENT_W, LH, LIGHT)
  ry += 5

  // Ausbildung
  if (cvData.ausbildung?.length > 0) {
    contentSection('Bildung')
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    for (const entry of cvData.ausbildung) {
      ry = checkBreak(ry, 12)
      doc.setFillColor(...BLUE)
      doc.circle(CONTENT_X - 2, ry, 1.3, 'F')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8)
      doc.setTextColor(...AMBER)
      doc.text(entry.zeitraum, CONTENT_X + 2, ry + 0.5)
      ry += 5
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      ry = renderStyledParagraph(doc, entry.beschreibung, CONTENT_X + 2, ry, CONTENT_W - 2, LH_SM, LIGHT)
      ry += 3
    }
    ry += 2
  }

  // Berufserfahrung
  if (cvData.berufserfahrung?.length > 0) {
    contentSection('Berufserfahrung')
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    for (const entry of cvData.berufserfahrung) {
      ry = checkBreak(ry, 12)
      doc.setFillColor(...BLUE)
      doc.circle(CONTENT_X - 2, ry, 1.3, 'F')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8)
      doc.setTextColor(...AMBER)
      doc.text(entry.zeitraum, CONTENT_X + 2, ry + 0.5)
      ry += 5
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      ry = renderStyledParagraph(doc, entry.beschreibung, CONTENT_X + 2, ry, CONTENT_W - 2, LH_SM, LIGHT)
      ry += 3
    }
  }

  // ── PAGE 2: Anschreiben ────────────────────────────────────────────────────
  doc.addPage()
  drawHeader('Anschreiben / Cover Letter')
  drawFooter()

  let cy = MT + 2
  // Date + address placeholder block (top right)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  doc.setTextColor(...AMBER)
  doc.text('[Ort], [Datum]', W - MR, cy, { align: 'right' })
  cy += 5
  doc.text('[Unternehmensname]', W - MR, cy, { align: 'right' })
  cy += 4.5
  doc.text('[Straße, PLZ Ort]', W - MR, cy, { align: 'right' })
  cy += 10

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9.5)
  cy = renderStyledParagraph(doc, anschreiben, ML, cy, W - ML - MR, LH + 0.5, LIGHT)

  // Signature
  cy += 10
  doc.setFontSize(9)
  doc.setTextColor(...AMBER)
  doc.text('[Unterschrift]', ML, cy)
  cy += 5
  doc.setTextColor(...LIGHT)
  doc.text('[Ihr vollständiger Name]', ML, cy)

  doc.save(filename)
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function DocumentFactoryClient({
  diagnosticId,
  documentsUnlocked,
  paymentJustSucceeded = false,
  sessionId,
}: {
  diagnosticId: string
  documentsUnlocked: boolean
  paymentJustSucceeded?: boolean
  sessionId?: string
}) {
  const { lang } = useLanguage()
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<Documents | null>(null)
  const [error, setError] = useState(false)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [isUnlocked, setIsUnlocked] = useState(documentsUnlocked)
  const [checkingPayment, setCheckingPayment] = useState(paymentJustSucceeded && !documentsUnlocked)

  const langFlag = lang === 'es' ? '🇪🇸' : '🇬🇧'
  const langLabel = lang === 'es' ? 'Spanish' : 'English'

  // ── Payment unlock: session verify → polling fallback ────────────────────────
  useEffect(() => {
    if (!paymentJustSucceeded || isUnlocked) return

    let cancelled = false

    const startPolling = () => {
      let attempts = 0
      const id = setInterval(async () => {
        if (cancelled) { clearInterval(id); return }
        attempts++
        try {
          const res = await fetch(`${API_URL}/api/diagnostic/${diagnosticId}/result`, { cache: 'no-store' })
          const data = await res.json()
          if (data.documents_unlocked) {
            setIsUnlocked(true)
            setCheckingPayment(false)
            clearInterval(id)
          } else if (attempts >= 6) {
            setCheckingPayment(false)
            clearInterval(id)
          }
        } catch { /* silent */ }
      }, 2000)
      return id
    }

    if (sessionId) {
      fetch(`${API_URL}/api/payments/verify-session?session_id=${encodeURIComponent(sessionId)}`)
        .then(r => r.json())
        .then(data => {
          if (cancelled) return
          if (data.documents_unlocked && data.diagnostic_id === diagnosticId) {
            setIsUnlocked(true)
            setCheckingPayment(false)
          } else {
            startPolling()
          }
        })
        .catch(() => { if (!cancelled) startPolling() })
    } else {
      const id = startPolling()
      return () => { cancelled = true; clearInterval(id) }
    }

    return () => { cancelled = true }
  }, [paymentJustSucceeded, isUnlocked, diagnosticId, sessionId])

  // ── Checkout ─────────────────────────────────────────────────────────────────
  const handleUnlock = async () => {
    setCheckoutLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/payments/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diagnostic_id: diagnosticId, product: 'documents', target_language: lang }),
      })
      const data = await res.json()
      if (data.url) window.location.href = data.url
      else setCheckoutLoading(false)
    } catch { setCheckoutLoading(false) }
  }

  // ── Generate ──────────────────────────────────────────────────────────────────
  const generate = async () => {
    setLoading(true)
    setError(false)
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 60000)
    try {
      const res = await fetch(`${API_URL}/api/diagnostic/${diagnosticId}/generate-documents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_language: lang }),
        signal: controller.signal,
      })
      clearTimeout(timeout)
      if (!res.ok) throw new Error()
      setDocuments(await res.json())
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  // ── Paywall ──────────────────────────────────────────────────────────────────
  if (!isUnlocked) {
    return (
      <div style={{ marginTop: 24 }}>
        {checkingPayment && (
          <div style={{ background: 'rgba(13,148,136,0.1)', border: '1px solid rgba(13,148,136,0.3)', borderRadius: 8, padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#5EEAD4' }}>
            Payment received — confirming your unlock, this takes a few seconds...
          </div>
        )}
        {!checkingPayment && paymentJustSucceeded && !isUnlocked && (
          <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 8, padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#FCD34D' }}>
            Your payment was successful, but unlocking is taking longer than expected. Please refresh in a moment.
          </div>
        )}
        <div style={{ background: 'rgba(13,148,136,0.06)', border: '1px solid rgba(13,148,136,0.2)', borderRadius: 16, padding: '28px 24px', textAlign: 'center' }}>
          <div style={{ marginBottom: 8 }}><Lock size={24} color="var(--accent)" style={{ display: 'inline-block' }} /></div>
          <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#F9FAFB', margin: '0 0 6px' }}>
            German CV &amp; Cover Letter
          </h3>
          <p style={{ color: '#9CA3AF', fontSize: '0.875rem', margin: '0 auto 20px', maxWidth: 380 }}>
            Get a personalised bilingual CV and cover letter in German + {langLabel} — ready to send to employers.
          </p>
          <button
            onClick={handleUnlock}
            disabled={checkoutLoading}
            style={{ background: 'var(--accent)', color: 'white', padding: '12px 28px', borderRadius: 9999, fontWeight: 700, fontSize: '0.9375rem', border: 'none', cursor: checkoutLoading ? 'wait' : 'pointer', opacity: checkoutLoading ? 0.7 : 1 }}
          >
            {checkoutLoading ? 'Redirecting…' : 'Unlock CV & Cover Letter — €15'}
          </button>
        </div>
      </div>
    )
  }

  // ── Documents generated ───────────────────────────────────────────────────────
  if (documents) {
    const cvDe = documents.cv_de ?? documents.cv
    const anschDe = documents.anschreiben_de ?? documents.anschreiben
    const cvTarget = documents.cv_target ?? null
    const anschTarget = documents.anschreiben_target ?? null

    return (
      <div style={{ marginTop: 24 }}>
        <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 20, fontSize: 13, color: '#FCD34D' }}>
          ⚠️ Replace all{' '}
          <span style={{ background: 'rgba(245,158,11,0.2)', color: '#F59E0B', padding: '0 3px', borderRadius: 3 }}>[bracketed]</span>
          {' '}placeholders with your real information before sending to any employer.
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: cvTarget ? '1fr 1fr' : '1fr',
          gap: 16,
          marginBottom: 20,
        }}>
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: 18 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#F9FAFB', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 7 }}>
              🇩🇪 <span>DE</span>
            </div>
            <CVColumn cv={cvDe} anschreiben={anschDe} />
          </div>

          {cvTarget && anschTarget && (
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: 18 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#F9FAFB', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 7 }}>
                {langFlag} <span>{lang.toUpperCase()}</span>
              </div>
              <CVColumn cv={cvTarget} anschreiben={anschTarget} />
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={() => generatePremiumPdf(cvDe, anschDe, 'DE 🇩🇪', 'Klar_CV_DE.pdf')}
            style={{ background: 'rgba(37,99,235,0.12)', border: '1px solid rgba(37,99,235,0.3)', borderRadius: 9999, padding: '10px 22px', fontSize: 13, color: '#60A5FA', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 7 }}
          >
            <FileText size={14} /> Download DE PDF
          </button>
          {cvTarget && anschTarget && (
            <button
              onClick={() => generatePremiumPdf(cvTarget, anschTarget, `${lang.toUpperCase()} ${langFlag}`, `Klar_CV_${lang.toUpperCase()}.pdf`)}
              style={{ background: 'rgba(37,99,235,0.12)', border: '1px solid rgba(37,99,235,0.3)', borderRadius: 9999, padding: '10px 22px', fontSize: 13, color: '#60A5FA', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 7 }}
            >
              <FileText size={14} /> Download {lang.toUpperCase()} PDF
            </button>
          )}
        </div>
      </div>
    )
  }

  // ── Unlocked — not yet generated ──────────────────────────────────────────────
  return (
    <div style={{ marginTop: 24 }}>
      <button
        onClick={generate}
        disabled={loading}
        style={{ background: 'var(--accent)', color: 'white', padding: '12px 28px', borderRadius: 9999, fontWeight: 600, fontSize: 14, border: 'none', cursor: loading ? 'wait' : 'pointer', opacity: loading ? 0.7 : 1 }}
      >
        {loading
          ? 'Generating your bilingual CV & cover letter…'
          : <><FileText size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 6 }} />Generate My CV &amp; Cover Letter</>
        }
      </button>
      <p style={{ color: '#6B7280', fontSize: 12, marginTop: 8 }}>
        Your documents will be generated in German + {langLabel} {langFlag}. Switch language in the navbar above to change.
      </p>
      {error && <p style={{ color: '#EF4444', fontSize: 13, marginTop: 8 }}>Something went wrong. Please try again.</p>}
    </div>
  )
}
