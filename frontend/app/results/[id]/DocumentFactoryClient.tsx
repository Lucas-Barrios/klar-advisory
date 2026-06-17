'use client'
import { useState, useEffect } from 'react'
import { FileText, Lock } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function DocumentFactoryClient({
  diagnosticId,
  documentsUnlocked,
  paymentJustSucceeded = false,
}: {
  diagnosticId: string
  documentsUnlocked: boolean
  paymentJustSucceeded?: boolean
}) {
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<any>(null)
  const [error, setError] = useState(false)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [isUnlocked, setIsUnlocked] = useState(documentsUnlocked)
  const [checkingPayment, setCheckingPayment] = useState(paymentJustSucceeded && !documentsUnlocked)

  useEffect(() => {
    if (!paymentJustSucceeded || documentsUnlocked) return

    let attempts = 0
    const maxAttempts = 6

    const interval = setInterval(async () => {
      attempts++
      try {
        const res = await fetch(`${API_URL}/api/diagnostic/${diagnosticId}/result`, {
          cache: 'no-store',
        })
        const data = await res.json()
        if (data.documents_unlocked) {
          setIsUnlocked(true)
          setCheckingPayment(false)
          clearInterval(interval)
        } else if (attempts >= maxAttempts) {
          setCheckingPayment(false)
          clearInterval(interval)
        }
      } catch (err) {
        console.error('Polling for unlock status failed:', err)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [paymentJustSucceeded, documentsUnlocked, diagnosticId])

  const handleUnlock = async () => {
    setCheckoutLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/payments/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diagnostic_id: diagnosticId, product: 'documents' }),
      })
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      } else {
        setCheckoutLoading(false)
      }
    } catch {
      setCheckoutLoading(false)
    }
  }

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

  // Paywall — not yet purchased
  if (!isUnlocked) {
    return (
      <div style={{ marginTop: '24px' }}>
        {checkingPayment && (
          <div style={{
            background: 'rgba(13,148,136,0.1)', border: '1px solid rgba(13,148,136,0.3)',
            borderRadius: '8px', padding: '12px 16px', marginBottom: '16px',
            fontSize: '13px', color: '#5EEAD4',
          }}>
            Payment received — confirming your unlock, this takes a few seconds...
          </div>
        )}
        {!checkingPayment && paymentJustSucceeded && !isUnlocked && (
          <div style={{
            background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
            borderRadius: '8px', padding: '12px 16px', marginBottom: '16px',
            fontSize: '13px', color: '#FCD34D',
          }}>
            Your payment was successful, but unlocking is taking longer than expected. Please refresh this page in a moment.
          </div>
        )}
        <div style={{
          background: 'rgba(13,148,136,0.06)',
          border: '1px solid rgba(13,148,136,0.2)',
          borderRadius: '16px',
          padding: '28px 24px',
          textAlign: 'center',
        }}>
        <div style={{ marginBottom: '8px' }}>
          <Lock size={24} color="var(--accent)" style={{ display: 'inline-block' }} />
        </div>
        <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#F9FAFB', margin: '0 0 6px' }}>
          German CV &amp; Cover Letter
        </h3>
        <p style={{ color: '#9CA3AF', fontSize: '0.875rem', margin: '0 auto 20px', maxWidth: '380px' }}>
          Get a personalised German-format CV and cover letter generated from your diagnostic — ready to send to employers.
        </p>
        <button
          onClick={handleUnlock}
          disabled={checkoutLoading}
          style={{
            background: 'var(--accent)',
            color: 'white',
            padding: '12px 28px',
            borderRadius: '9999px',
            fontWeight: 700,
            fontSize: '0.9375rem',
            border: 'none',
            cursor: checkoutLoading ? 'wait' : 'pointer',
            opacity: checkoutLoading ? 0.7 : 1,
          }}
        >
          {checkoutLoading ? 'Redirecting…' : 'Unlock CV & Cover Letter — €15'}
        </button>
        </div>
      </div>
    )
  }

  // Documents already generated
  if (documents) {
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
          <FileText size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />Download Full CV &amp; Cover Letter (PDF)
        </button>
      </div>
    )
  }

  // Unlocked — not yet generated
  return (
    <div style={{ marginTop: '24px' }}>
      <button
        onClick={generate}
        disabled={loading}
        style={{
          background: 'var(--accent)',
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
        {loading
          ? 'Generating your German CV & cover letter...'
          : <><FileText size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />Generate My German CV &amp; Cover Letter</>
        }
      </button>
      {error && (
        <p style={{ color: '#EF4444', fontSize: '13px', marginTop: '8px' }}>
          Something went wrong. Please try again.
        </p>
      )}
    </div>
  )
}
