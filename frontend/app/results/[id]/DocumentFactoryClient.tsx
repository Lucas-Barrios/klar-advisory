'use client'
import { useState, useEffect, useMemo } from 'react'
import { FileText, Lock, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
import { useLanguage } from '@/lib/LanguageContext'
import ErrorMessage from '@/components/ErrorMessage'
import { getErrorMessage } from '@/lib/errors'

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
type DocumentFacts = {
  employer_name?: string
  employer_location?: string
  job_title?: string
  employment_period?: string
  employment_duties?: string
  institution_name?: string
  institution_location?: string
  study_period?: string
  street_address?: string
  phone_number?: string
  full_address?: string
  city?: string
  placeholder_values?: Record<string, string>
}
type MatchedPosition = {
  refnr: string
  titel: string | null
  arbeitgeber: string | null
  beruf?: string | null
}

// ─── Placeholder helpers ──────────────────────────────────────────────────────

const PLACEHOLDER_RE = /\[([^\]]+)\]/g

// Map of known German placeholder text (inner, no brackets) → {label, factsKey}
const KNOWN_PLACEHOLDERS: Record<string, { label: string; factsKey: keyof Omit<DocumentFacts, 'placeholder_values'> }> = {
  'Arbeitgeber': { label: 'Employer name', factsKey: 'employer_name' },
  'Name des Arbeitgebers': { label: 'Employer name', factsKey: 'employer_name' },
  'Arbeitgeber], [Ort': { label: 'Employer', factsKey: 'employer_name' },
  'Position': { label: 'Job title / Position', factsKey: 'job_title' },
  'Stelle': { label: 'Job title / Role', factsKey: 'job_title' },
  'Berufsbezeichnung': { label: 'Job title', factsKey: 'job_title' },
  'Zeitraum': { label: 'Period (e.g. 2021–2023)', factsKey: 'employment_period' },
  'Zeitraum, z.B. 2021–2023': { label: 'Period', factsKey: 'employment_period' },
  'Zeitraum z.B. 2021–2023': { label: 'Period', factsKey: 'employment_period' },
  'Studienzeitraum': { label: 'Study period', factsKey: 'study_period' },
  'Name der Bildungseinrichtung': { label: 'Institution name', factsKey: 'institution_name' },
  'Bildungseinrichtung': { label: 'Institution name', factsKey: 'institution_name' },
  'Universität': { label: 'University name', factsKey: 'institution_name' },
  'Schule': { label: 'School name', factsKey: 'institution_name' },
  'Ort': { label: 'Location / City', factsKey: 'employer_location' },
  'Ihre Adresse': { label: 'Your street address', factsKey: 'street_address' },
  'PLZ, Ort': { label: 'Postal code & city', factsKey: 'full_address' },
  'Ihre Telefonnummer': { label: 'Your phone number', factsKey: 'phone_number' },
  'Telefon': { label: 'Phone number', factsKey: 'phone_number' },
}

export function hasIncompletePlaceholders(text: string): boolean {
  return /\[[^\]]+\]/.test(text)
}

function collectDocText(docs: Documents): string[] {
  const cvDe = docs.cv_de ?? docs.cv
  const texts: string[] = [cvDe.profil, docs.anschreiben_de ?? docs.anschreiben]
  cvDe.ausbildung?.forEach(e => { texts.push(e.zeitraum, e.beschreibung) })
  cvDe.berufserfahrung?.forEach(e => { texts.push(e.zeitraum, e.beschreibung) })
  if (docs.cv_target) {
    texts.push(docs.cv_target.profil)
    docs.cv_target.ausbildung?.forEach(e => { texts.push(e.zeitraum, e.beschreibung) })
    docs.cv_target.berufserfahrung?.forEach(e => { texts.push(e.zeitraum, e.beschreibung) })
  }
  if (docs.anschreiben_target) texts.push(docs.anschreiben_target)
  return texts
}

function remainingPlaceholderList(docs: Documents): string[] {
  const texts = collectDocText(docs)
  const seen = new Set<string>()
  const result: string[] = []
  for (const t of texts) {
    const ms = t?.matchAll(PLACEHOLDER_RE) ?? []
    for (const m of ms) {
      const inner = m[1]
      if (!['Unterschrift', 'Ihr vollständiger Name', 'Ort', 'Datum'].includes(inner) && !seen.has(inner)) {
        seen.add(inner)
        result.push(`[${inner}]`)
      }
    }
  }
  return result
}

// ─── Inline-editable placeholder ─────────────────────────────────────────────

function EditablePlaceholder({
  inner,
  facts,
  setFacts,
}: {
  inner: string
  facts: Record<string, string>
  setFacts: React.Dispatch<React.SetStateAction<Record<string, string>>>
}) {
  const [editing, setEditing] = useState(false)
  const value = facts[inner] ?? ''
  const filled = value.trim().length > 0

  if (editing) {
    return (
      <input
        autoFocus
        type="text"
        value={value}
        onChange={e => setFacts(f => ({ ...f, [inner]: e.target.value }))}
        onBlur={() => setEditing(false)}
        onKeyDown={e => { if (e.key === 'Enter') setEditing(false) }}
        style={{
          font: 'inherit',
          fontSize: 'inherit',
          fontWeight: 'inherit',
          color: '#14B8A6',
          background: 'transparent',
          border: 'none',
          borderBottom: '1.5px solid #14B8A6',
          outline: 'none',
          padding: '0 2px',
          minWidth: `${Math.max((value.length || inner.length) + 4, 6)}ch`,
          display: 'inline',
          verticalAlign: 'baseline',
        }}
      />
    )
  }

  return (
    <span
      onClick={() => setEditing(true)}
      title={`Click to fill in: ${inner}`}
      style={{
        background: filled ? 'rgba(20,184,166,0.1)' : 'rgba(245,158,11,0.15)',
        color: filled ? '#14B8A6' : '#F59E0B',
        padding: '0 3px',
        borderRadius: 3,
        fontWeight: 500,
        cursor: 'pointer',
        borderBottom: filled ? '1.5px solid #14B8A6' : 'none',
        whiteSpace: 'nowrap',
      }}
    >
      {filled ? value : `[${inner}]`}
    </span>
  )
}

// ─── Placeholder highlighting ─────────────────────────────────────────────────

function HighlightedText({
  text,
  facts,
  setFacts,
}: {
  text: string
  facts: Record<string, string>
  setFacts: React.Dispatch<React.SetStateAction<Record<string, string>>>
}) {
  const parts = text.split(/(\[[^\]]*\])/g)
  return (
    <>
      {parts.map((part, i) =>
        /^\[[^\]]*\]$/.test(part) ? (
          <EditablePlaceholder
            key={i}
            inner={part.slice(1, -1)}
            facts={facts}
            setFacts={setFacts}
          />
        ) : (
          part
        )
      )}
    </>
  )
}

// ─── Collapsible CV column ────────────────────────────────────────────────────

function CVColumn({
  cv,
  anschreiben,
  facts,
  setFacts,
  regenerating,
}: {
  cv: CVData
  anschreiben: string
  facts: Record<string, string>
  setFacts: React.Dispatch<React.SetStateAction<Record<string, string>>>
  regenerating: boolean
}) {
  const [open, setOpen] = useState(false)

  return (
    <div style={{ position: 'relative' }}>
      {regenerating && (
        <div style={{
          position: 'absolute',
          inset: -18,
          borderRadius: 12,
          background: 'rgba(0,0,0,0.45)',
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(2px)',
          animation: 'cvPulse 1.5s ease-in-out infinite',
        }}>
          <span style={{ color: '#60A5FA', fontSize: 13, fontWeight: 500 }}>Updating your document…</span>
        </div>
      )}

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>
          Profile
        </div>
        <p style={{ fontSize: 13, color: '#D1D5DB', lineHeight: 1.65, margin: 0 }}>
          <HighlightedText text={cv.profil} facts={facts} setFacts={setFacts} />
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
                  <div style={{ color: '#F59E0B', fontSize: 11, fontWeight: 600 }}><HighlightedText text={e.zeitraum} facts={facts} setFacts={setFacts} /></div>
                  <div><HighlightedText text={e.beschreibung} facts={facts} setFacts={setFacts} /></div>
                </div>
              ))}
            </div>
          )}
          {cv.berufserfahrung?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 700, color: '#9CA3AF', marginBottom: 5, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Experience</div>
              {cv.berufserfahrung.map((e, i) => (
                <div key={i} style={{ marginBottom: 5, paddingLeft: 10, borderLeft: '2px solid rgba(37,99,235,0.3)' }}>
                  <div style={{ color: '#F59E0B', fontSize: 11, fontWeight: 600 }}><HighlightedText text={e.zeitraum} facts={facts} setFacts={setFacts} /></div>
                  <div><HighlightedText text={e.beschreibung} facts={facts} setFacts={setFacts} /></div>
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
          <HighlightedText text={anschreiben} facts={facts} setFacts={setFacts} />
        </div>
      </div>
    </div>
  )
}

// ─── PDF — ATS-safe, debranded ────────────────────────────────────────────────

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
  normal: RgbColor = [30, 30, 30],
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
  city?: string,
) {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })

  const W = 210, H = 297
  const ML = 20, MR = 20, MT = 20, MB = 18
  const BODY_W = W - ML - MR
  const DARK: RgbColor = [30, 30, 30]
  const MID: RgbColor = [90, 90, 90]
  const LIGHT: RgbColor = [150, 150, 150]
  const AMBER: RgbColor = [180, 110, 0]
  const LH = 5.2
  const LH_SM = 4.6

  const today = new Date()
  const dateStr = today.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  const cityStr = city && city.trim() ? city.trim() : '[Ort]'

  // Section header helper — returns new Y
  const section = (title: string, y: number): number => {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8)
    doc.setTextColor(...LIGHT)
    doc.text(title.toUpperCase(), ML, y)
    doc.setDrawColor(...LIGHT)
    doc.setLineWidth(0.3)
    doc.line(ML + doc.getTextWidth(title.toUpperCase()) + 3, y - 0.5, W - MR, y - 0.5)
    doc.setTextColor(...DARK)
    return y + 5
  }

  const checkBreak = (y: number, need: number): number => {
    if (y + need > H - MB - 5) {
      doc.addPage()
      return MT
    }
    return y
  }

  // ── PAGE 1: Lebenslauf ──────────────────────────────────────────────────────
  let y = MT

  // Name / document type header — no branding, clean
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(14)
  doc.setTextColor(...DARK)
  doc.text('Lebenslauf', ML, y)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...MID)
  doc.text(langLabel, W - MR, y, { align: 'right' })
  y += 3
  doc.setDrawColor(...DARK)
  doc.setLineWidth(0.5)
  doc.line(ML, y, W - MR, y)
  y += 8

  // PERSÖNLICHE DATEN
  y = section('Persönliche Daten', y)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)

  const personalFields = [
    ['[Ihre Adresse]', 'street_address'],
    ['[PLZ, Ort]', 'postal'],
    ['[Telefon]', 'phone'],
    ['[E-Mail]', 'email'],
  ]

  for (const [ph] of personalFields) {
    doc.setTextColor(...AMBER)
    doc.text(ph, ML, y)
    y += LH_SM
  }
  // Photo note
  doc.setFont('helvetica', 'italic')
  doc.setFontSize(8)
  doc.setTextColor(...LIGHT)
  doc.text('[Foto einfügen]', W - MR, y - LH_SM * 4 + 2, { align: 'right' })
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  y += 4

  // PROFIL
  y = checkBreak(y, 20)
  y = section('Profil', y)
  doc.setFontSize(9.5)
  y = renderStyledParagraph(doc, cvData.profil, ML, y, BODY_W, LH, DARK)
  y += 5

  // BERUFSERFAHRUNG
  if (cvData.berufserfahrung?.length > 0) {
    y = checkBreak(y, 16)
    y = section('Berufserfahrung', y)
    doc.setFontSize(9)
    for (const entry of cvData.berufserfahrung) {
      y = checkBreak(y, 14)
      // Date inline: "2021–2023 | Description..."
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8.5)
      doc.setTextColor(...AMBER)
      doc.text(entry.zeitraum, ML, y)
      y += LH_SM
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      y = renderStyledParagraph(doc, entry.beschreibung, ML + 4, y, BODY_W - 4, LH_SM, DARK)
      y += 4
    }
    y += 2
  }

  // AUSBILDUNG
  if (cvData.ausbildung?.length > 0) {
    y = checkBreak(y, 16)
    y = section('Ausbildung', y)
    doc.setFontSize(9)
    for (const entry of cvData.ausbildung) {
      y = checkBreak(y, 14)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8.5)
      doc.setTextColor(...AMBER)
      doc.text(entry.zeitraum, ML, y)
      y += LH_SM
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      y = renderStyledParagraph(doc, entry.beschreibung, ML + 4, y, BODY_W - 4, LH_SM, DARK)
      y += 4
    }
    y += 2
  }

  // SPRACHKENNTNISSE
  if (cvData.sprachkenntnisse?.length > 0) {
    y = checkBreak(y, 16)
    y = section('Sprachkenntnisse', y)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    for (const s of cvData.sprachkenntnisse) {
      y = checkBreak(y, 8)
      doc.setTextColor(...DARK)
      doc.text(s.sprache, ML + 4, y)
      doc.setTextColor(...MID)
      doc.text(s.niveau, ML + 50, y)
      y += LH_SM
    }
    y += 4
  }

  // KOMPETENZEN
  if (cvData.kompetenzen?.length > 0) {
    y = checkBreak(y, 16)
    y = section('Kompetenzen', y)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(...DARK)
    const skillText = cvData.kompetenzen.join(' · ')
    y = renderStyledParagraph(doc, skillText, ML + 4, y, BODY_W - 4, LH_SM, DARK)
    y += 4
  }

  // Signature line — German CV convention
  y = checkBreak(y, 24)
  y += 14
  doc.setDrawColor(...MID)
  doc.setLineWidth(0.3)
  doc.line(ML, y, ML + 60, y)
  y += 4
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  doc.setTextColor(...MID)
  doc.text(`${cityStr}, ${dateStr}`, ML, y)
  doc.setFont('helvetica', 'italic')
  doc.setFontSize(8)
  doc.text('(Unterschrift)', ML, y + 5)

  // ── PAGE 2: Anschreiben (DIN 5008) ─────────────────────────────────────────
  doc.addPage()
  let cy = MT

  // Sender block top-left
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...DARK)
  for (const ph of ['[Ihr Name]', '[Ihre Adresse]', '[PLZ, Ort]', '[Telefon]', '[E-Mail]']) {
    doc.setTextColor(hasIncompletePlaceholders(ph) ? (AMBER[0] as number) : DARK[0], hasIncompletePlaceholders(ph) ? (AMBER[1] as number) : DARK[1], hasIncompletePlaceholders(ph) ? (AMBER[2] as number) : DARK[2])
    doc.text(ph, ML, cy)
    cy += 4.8
  }
  cy += 4

  // Date right-aligned
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...DARK)
  doc.text(dateStr, W - MR, cy, { align: 'right' })
  cy += 10

  // Recipient block
  for (const ph of ['[Unternehmensname]', '[Straße, PLZ Ort]']) {
    doc.setTextColor(...AMBER)
    doc.text(ph, ML, cy)
    cy += 4.8
  }
  cy += 8

  // Subject line — bold
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...DARK)
  doc.text('Bewerbung als [Position]', ML, cy)
  cy += 10

  // Salutation
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9.5)
  doc.text('Sehr geehrte Damen und Herren,', ML, cy)
  cy += 8

  // Body
  cy = renderStyledParagraph(doc, anschreiben, ML, cy, BODY_W, LH + 0.3, DARK)

  // Closing
  cy += 6
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9.5)
  doc.setTextColor(...DARK)
  doc.text('Mit freundlichen Grüßen,', ML, cy)
  cy += 14
  doc.setDrawColor(...MID)
  doc.setLineWidth(0.3)
  doc.line(ML, cy, ML + 60, cy)
  cy += 4
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  doc.setTextColor(...MID)
  doc.text('[Ihr vollständiger Name]', ML, cy)

  doc.save(filename)
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function DocumentFactoryClient({
  diagnosticId,
  documentsUnlocked,
  matchesUnlocked = false,
  paymentJustSucceeded = false,
  sessionId,
}: {
  diagnosticId: string
  documentsUnlocked: boolean
  matchesUnlocked?: boolean
  paymentJustSucceeded?: boolean
  sessionId?: string
}) {
  const { lang } = useLanguage()
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<Documents | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [isUnlocked, setIsUnlocked] = useState(documentsUnlocked)
  const [checkingPayment, setCheckingPayment] = useState(paymentJustSucceeded && !documentsUnlocked)

  // Fact editor state
  const [facts, setFacts] = useState<Record<string, string>>({})
  const [selectedPositionIds, setSelectedPositionIds] = useState<string[]>([])
  const [matchedPositions, setMatchedPositions] = useState<MatchedPosition[]>([])
  const [regenerating, setRegenerating] = useState(false)
  const [regenError, setRegenError] = useState<string | null>(null)

  const langFlag = lang === 'es' ? '🇪🇸' : '🇬🇧'
  const langLabel = lang === 'es' ? 'Spanish' : 'English'

  // Remaining (unfilled) placeholders for QA gate
  const remaining = useMemo(() => {
    if (!documents) return []
    return remainingPlaceholderList(documents)
  }, [documents])

  const downloadsLocked = remaining.length > 0

  // Fetch matched positions when documents are generated and matches are unlocked
  useEffect(() => {
    if (!documents || !matchesUnlocked) return
    fetch(`${API_URL}/api/diagnostic/${diagnosticId}/matches`)
      .then(r => r.json())
      .then(data => {
        if (data?.matched_positions?.length) {
          setMatchedPositions(data.matched_positions)
        }
      })
      .catch(() => {})
  }, [documents, matchesUnlocked, diagnosticId])

  // ── Payment unlock: session verify → polling fallback ─────────────────────
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
          if (data.documents_unlocked && data.matches_unlocked && data.diagnostic_id === diagnosticId) {
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

  // ── Checkout ──────────────────────────────────────────────────────────────
  const handleUnlock = async () => {
    setCheckoutLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/payments/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diagnostic_id: diagnosticId, product: 'kit', target_language: lang }),
      })
      const data = await res.json()
      if (data.url) window.location.href = data.url
      else setCheckoutLoading(false)
    } catch { setCheckoutLoading(false) }
  }

  // ── Generate ──────────────────────────────────────────────────────────────
  const generate = async () => {
    setLoading(true)
    setError(null)
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
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setDocuments(await res.json())
    } catch (err) {
      setError(getErrorMessage(err, 'documents'))
    } finally {
      setLoading(false)
    }
  }

  // ── Regenerate ────────────────────────────────────────────────────────────
  const handleRegenerate = async () => {
    setRegenerating(true)
    setRegenError(null)
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 90000)

    // Build DocumentFacts from the facts dict (placeholder text → value)
    const builtFacts: DocumentFacts = {}
    const placeholderValues: Record<string, string> = {}
    for (const [inner, value] of Object.entries(facts)) {
      if (!value || !value.trim()) continue
      const known = KNOWN_PLACEHOLDERS[inner]
      if (known) {
        (builtFacts as any)[known.factsKey] = value.trim()
      } else {
        placeholderValues[inner] = value.trim()
      }
    }
    if (Object.keys(placeholderValues).length > 0) {
      builtFacts.placeholder_values = placeholderValues
    }

    try {
      const res = await fetch(`${API_URL}/api/diagnostic/${diagnosticId}/regenerate-documents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_language: lang,
          facts: Object.keys(builtFacts).length > 0 ? builtFacts : undefined,
          target_position_ids: selectedPositionIds.length > 0 ? selectedPositionIds : undefined,
        }),
        signal: controller.signal,
      })
      clearTimeout(timeout)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setDocuments(await res.json())
    } catch (err) {
      setRegenError(getErrorMessage(err, 'documents'))
    } finally {
      setRegenerating(false)
    }
  }

  // ── Paywall ───────────────────────────────────────────────────────────────
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
            {checkoutLoading ? 'Redirecting…' : 'Unlock Germany Application Kit — €39'}
          </button>
          <p style={{ fontSize: '0.75rem', color: '#6B7280', marginTop: '10px' }}>
            Includes matched positions + bilingual CV &amp; Cover Letter
          </p>
        </div>
      </div>
    )
  }

  // ── Documents generated — show editor + preview ───────────────────────────
  if (documents) {
    const cvDe = documents.cv_de ?? documents.cv
    const anschDe = documents.anschreiben_de ?? documents.anschreiben
    const cvTarget = documents.cv_target ?? null
    const anschTarget = documents.anschreiben_target ?? null

    const hasFacts = Object.values(facts).some(v => v.trim().length > 0)

    return (
      <div style={{ marginTop: 24 }}>
        <style>{`
          @keyframes cvPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.55; } }
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        `}</style>

        {/* Quiet instruction */}
        <p style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 16, marginTop: 0 }}>
          Click any <span style={{ color: '#F59E0B' }}>highlighted field</span> to edit it directly.
        </p>

        {/* ── Tailor to a Position ─────────────────────────────────────────── */}
        {matchedPositions.length > 0 && (
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: 16, marginBottom: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#F9FAFB', marginBottom: 4 }}>
              Tailor to a Position
            </div>
            <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 10 }}>
              Select a matched position and your CV will reflect relevant language from the posting.
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {matchedPositions.map(p => {
                const sel = selectedPositionIds.includes(p.refnr)
                return (
                  <button
                    key={p.refnr}
                    onClick={() => setSelectedPositionIds(ids =>
                      sel ? ids.filter(id => id !== p.refnr) : [...ids, p.refnr]
                    )}
                    style={{
                      background: sel ? 'rgba(37,99,235,0.25)' : 'rgba(255,255,255,0.04)',
                      border: sel ? '1px solid rgba(37,99,235,0.5)' : '1px solid rgba(255,255,255,0.1)',
                      borderRadius: 9999,
                      padding: '5px 12px',
                      fontSize: 11,
                      color: sel ? '#60A5FA' : '#9CA3AF',
                      cursor: 'pointer',
                    }}
                  >
                    {p.titel ?? p.beruf ?? p.refnr}
                    {p.arbeitgeber ? ` · ${p.arbeitgeber}` : ''}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* ── QA gate status ───────────────────────────────────────────────── */}
        {downloadsLocked ? (
          <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#FCD34D' }}>
            <strong>{remaining.length} field{remaining.length !== 1 ? 's' : ''} still need your info before downloading:</strong>
            <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {remaining.map(ph => (
                <span key={ph} style={{ background: 'rgba(245,158,11,0.15)', color: '#F59E0B', padding: '1px 8px', borderRadius: 4, fontSize: 12 }}>{ph}</span>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ background: 'rgba(13,148,136,0.08)', border: '1px solid rgba(13,148,136,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#5EEAD4' }}>
            All fields complete — your documents are ready to download.
          </div>
        )}

        {/* ── Document preview ─────────────────────────────────────────────── */}
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
            <CVColumn cv={cvDe} anschreiben={anschDe} facts={facts} setFacts={setFacts} regenerating={regenerating} />
          </div>

          {cvTarget && anschTarget && (
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: 18 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#F9FAFB', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 7 }}>
                {langFlag} <span>{lang.toUpperCase()}</span>
              </div>
              <CVColumn cv={cvTarget} anschreiben={anschTarget} facts={facts} setFacts={setFacts} regenerating={regenerating} />
            </div>
          )}
        </div>

        {/* ── Download buttons — gated ─────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={() => !downloadsLocked && generatePremiumPdf(cvDe, anschDe, 'DE', 'CV_DE.pdf', facts['Ort'] ?? facts['PLZ, Ort'])}
            disabled={downloadsLocked}
            title={downloadsLocked ? `Fill all placeholders first (${remaining.length} remaining)` : 'Download German PDF'}
            style={{
              background: downloadsLocked ? 'rgba(255,255,255,0.04)' : 'rgba(37,99,235,0.12)',
              border: downloadsLocked ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(37,99,235,0.3)',
              borderRadius: 9999,
              padding: '10px 22px',
              fontSize: 13,
              color: downloadsLocked ? '#4B5563' : '#60A5FA',
              cursor: downloadsLocked ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 7,
            }}
          >
            <FileText size={14} /> Download DE PDF
            {downloadsLocked && <Lock size={12} style={{ opacity: 0.5 }} />}
          </button>
          {cvTarget && anschTarget && (
            <button
              onClick={() => !downloadsLocked && generatePremiumPdf(cvTarget, anschTarget, langLabel, `CV_${lang.toUpperCase()}.pdf`, facts['Ort'] ?? facts['PLZ, Ort'])}
              disabled={downloadsLocked}
              title={downloadsLocked ? `Fill all placeholders first (${remaining.length} remaining)` : `Download ${langLabel} PDF`}
              style={{
                background: downloadsLocked ? 'rgba(255,255,255,0.04)' : 'rgba(37,99,235,0.12)',
                border: downloadsLocked ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(37,99,235,0.3)',
                borderRadius: 9999,
                padding: '10px 22px',
                fontSize: 13,
                color: downloadsLocked ? '#4B5563' : '#60A5FA',
                cursor: downloadsLocked ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 7,
              }}
            >
              <FileText size={14} /> Download {lang.toUpperCase()} PDF
              {downloadsLocked && <Lock size={12} style={{ opacity: 0.5 }} />}
            </button>
          )}
        </div>

        {/* Regenerate error */}
        {regenError && (
          <div style={{ marginTop: 16 }}>
            <ErrorMessage message={regenError} onRetry={handleRegenerate} onDismiss={() => setRegenError(null)} />
          </div>
        )}

        {/* ── Floating "Update My CV" — visible once any placeholder is filled */}
        {hasFacts && (
          <div style={{ position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 100 }}>
            <button
              onClick={handleRegenerate}
              disabled={regenerating}
              style={{
                background: regenerating ? 'rgba(37,99,235,0.8)' : '#2563EB',
                color: 'white',
                padding: '12px 28px',
                borderRadius: 9999,
                fontWeight: 700,
                fontSize: 14,
                border: 'none',
                cursor: regenerating ? 'wait' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                boxShadow: '0 4px 24px rgba(0,0,0,0.5), 0 1px 8px rgba(37,99,235,0.4)',
                opacity: regenerating ? 0.85 : 1,
              }}
            >
              <RefreshCw size={15} style={{ animation: regenerating ? 'spin 1s linear infinite' : 'none' }} />
              {regenerating ? 'Updating…' : 'Update My CV'}
            </button>
          </div>
        )}
      </div>
    )
  }

  // ── Unlocked — not yet generated ──────────────────────────────────────────
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
      {error && (
        <div style={{ marginTop: 8 }}>
          <ErrorMessage message={error} onRetry={generate} onDismiss={() => setError(null)} />
        </div>
      )}
    </div>
  )
}
