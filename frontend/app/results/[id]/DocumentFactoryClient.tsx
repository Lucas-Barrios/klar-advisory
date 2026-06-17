'use client'
import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function DocumentFactoryClient({ diagnosticId }: { diagnosticId: string }) {
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<any>(null)
  const [error, setError] = useState(false)

  const generate = async () => {
    setLoading(true)
    setError(false)

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 30000)

    try {
      const res = await fetch(`${API_URL}/api/diagnostic/${diagnosticId}/generate-documents`, {
        method: 'POST',
        signal: controller.signal,
      })
      clearTimeout(timeout)
      if (!res.ok) throw new Error('Generation failed')
      const data = await res.json()
      setDocuments(data)
    } catch (err) {
      console.error('Document generation failed:', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  const downloadPdf = async () => {
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 20
    const maxWidth = pageWidth - margin * 2
    let y = margin

    const checkPageBreak = (neededHeight: number) => {
      if (y + neededHeight > pageHeight - margin) {
        doc.addPage()
        y = margin
      }
    }

    // Page 1 — Lebenslauf
    doc.setFontSize(20)
    doc.setFont('helvetica', 'bold')
    doc.text('Lebenslauf', margin, y)
    y += 12

    // Profil
    doc.setFontSize(13)
    doc.setFont('helvetica', 'bold')
    doc.text('Profil', margin, y)
    y += 7
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    const profilLines = doc.splitTextToSize(documents.cv.profil, maxWidth)
    checkPageBreak(profilLines.length * 5 + 10)
    doc.text(profilLines, margin, y)
    y += profilLines.length * 5 + 10

    // Ausbildung / Bildung
    if (documents.cv.ausbildung?.length > 0) {
      checkPageBreak(14)
      doc.setFontSize(13)
      doc.setFont('helvetica', 'bold')
      doc.text('Bildung', margin, y)
      y += 7
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      documents.cv.ausbildung.forEach((item: any) => {
        const line = `${item.zeitraum}: ${item.beschreibung}`
        const lines = doc.splitTextToSize(line, maxWidth)
        checkPageBreak(lines.length * 5 + 4)
        doc.text(lines, margin, y)
        y += lines.length * 5 + 4
      })
      y += 4
    }

    // Berufserfahrung
    if (documents.cv.berufserfahrung?.length > 0) {
      checkPageBreak(14)
      doc.setFontSize(13)
      doc.setFont('helvetica', 'bold')
      doc.text('Berufserfahrung', margin, y)
      y += 7
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      documents.cv.berufserfahrung.forEach((item: any) => {
        const line = `${item.zeitraum}: ${item.beschreibung}`
        const lines = doc.splitTextToSize(line, maxWidth)
        checkPageBreak(lines.length * 5 + 4)
        doc.text(lines, margin, y)
        y += lines.length * 5 + 4
      })
      y += 4
    }

    // Sprachkenntnisse
    if (documents.cv.sprachkenntnisse?.length > 0) {
      checkPageBreak(14)
      doc.setFontSize(13)
      doc.setFont('helvetica', 'bold')
      doc.text('Sprachkenntnisse', margin, y)
      y += 7
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      documents.cv.sprachkenntnisse.forEach((item: any) => {
        checkPageBreak(8)
        doc.text(`${item.sprache}: ${item.niveau}`, margin, y)
        y += 6
      })
      y += 4
    }

    // Kompetenzen
    if (documents.cv.kompetenzen?.length > 0) {
      checkPageBreak(14)
      doc.setFontSize(13)
      doc.setFont('helvetica', 'bold')
      doc.text('Kompetenzen', margin, y)
      y += 7
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      documents.cv.kompetenzen.forEach((skill: string) => {
        checkPageBreak(8)
        doc.text(`• ${skill}`, margin, y)
        y += 6
      })
    }

    // Page 2 — Anschreiben
    doc.addPage()
    y = margin
    doc.setFontSize(20)
    doc.setFont('helvetica', 'bold')
    doc.text('Anschreiben', margin, y)
    y += 12
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    const coverLines = doc.splitTextToSize(documents.anschreiben, maxWidth)
    coverLines.forEach((line: string) => {
      checkPageBreak(6)
      doc.text(line, margin, y)
      y += 5
    })

    doc.save('Klar_Bewerbungsunterlagen.pdf')
  }

  if (!documents) {
    return (
      <div style={{ marginTop: '24px' }}>
        <button
          onClick={generate}
          disabled={loading}
          style={{
            background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
            color: 'white',
            padding: '12px 28px',
            borderRadius: '9999px',
            fontWeight: 600,
            fontSize: '14px',
            border: 'none',
            cursor: loading ? 'wait' : 'pointer',
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? 'Generating your German CV & cover letter...' : '📄 Generate My German CV & Cover Letter'}
        </button>
        {error && (
          <p style={{ color: '#EF4444', fontSize: '13px', marginTop: '8px' }}>
            Something went wrong. Please try again.
          </p>
        )}
      </div>
    )
  }

  return (
    <div style={{ marginTop: '24px' }}>
      <div style={{
        background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
        borderRadius: '8px', padding: '12px 16px', marginBottom: '16px',
        fontSize: '13px', color: '#FCD34D'
      }}>
        ⚠️ This is a structural template. Replace all [bracketed] placeholders
        with your real information — address, employer names, exact dates — before
        sending to any employer. Klar generates the format, you provide the facts.
      </div>
      <div
        style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '16px',
        }}
      >
        <h3 style={{ color: '#F9FAFB', fontSize: '18px', marginBottom: '12px' }}>
          Ihr Profil (Your CV Summary)
        </h3>
        <p style={{ color: '#9CA3AF', fontSize: '14px', lineHeight: 1.6 }}>
          {documents.cv.profil}
        </p>
      </div>
      <button
        onClick={downloadPdf}
        style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '9999px',
          padding: '10px 24px',
          fontSize: '14px',
          color: '#F9FAFB',
          cursor: 'pointer',
        }}
      >
        📥 Download Full CV & Cover Letter (PDF)
      </button>
    </div>
  )
}
