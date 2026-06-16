'use client'
import { useState } from 'react'
import type { Diagnostic } from './ResultsContent'

interface Props {
  studentName: string
  diagnostic: Diagnostic
}

export default function DownloadPdfButton({ studentName, diagnostic }: Props) {
  const [generating, setGenerating] = useState(false)

  const handleDownload = async () => {
    setGenerating(true)
    try {
      const { jsPDF } = await import('jspdf')
      const doc = new jsPDF()

      const pageWidth = doc.internal.pageSize.getWidth()
      let y = 20

      // Header
      doc.setFontSize(22)
      doc.setFont('helvetica', 'bold')
      doc.text('Klar — Germany Readiness Report', 20, y)
      y += 10

      doc.setFontSize(11)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(100)
      doc.text(`Prepared for ${studentName}`, 20, y)
      y += 15

      // Overall score
      doc.setFontSize(16)
      doc.setTextColor(0)
      doc.setFont('helvetica', 'bold')
      doc.text(`Overall Readiness Score: ${diagnostic.overall_score}/100`, 20, y)
      y += 12

      // Summary
      if (diagnostic.summary) {
        doc.setFontSize(11)
        doc.setFont('helvetica', 'normal')
        const summaryLines = doc.splitTextToSize(diagnostic.summary, pageWidth - 40)
        doc.text(summaryLines, 20, y)
        y += summaryLines.length * 6 + 10
      }

      // Dimension scores
      doc.setFontSize(14)
      doc.setFont('helvetica', 'bold')
      doc.text('Dimension Scores', 20, y)
      y += 8

      const dims = diagnostic.dimension_scores
      const dimensions: [string, number][] = dims
        ? [
            ['German Language', dims.language],
            ['Education', dims.education],
            ['Pathway Fit', dims.pathway_fit],
            ['Timeline', dims.timeline],
            ['Finances', dims.financial],
            ['Documentation', dims.documentation],
          ]
        : []

      doc.setFontSize(11)
      doc.setFont('helvetica', 'normal')
      dimensions.forEach(([label, score]) => {
        doc.text(`${label}: ${score}/100`, 25, y)
        y += 7
      })
      y += 8

      // Roadmap
      if (diagnostic.roadmap && diagnostic.roadmap.length > 0) {
        doc.setFontSize(14)
        doc.setFont('helvetica', 'bold')
        doc.text('Your Roadmap', 20, y)
        y += 8

        diagnostic.roadmap.forEach((step) => {
          if (y > 270) {
            doc.addPage()
            y = 20
          }
          doc.setFontSize(12)
          doc.setFont('helvetica', 'bold')
          doc.text(`Month ${step.month}: ${step.title}`, 20, y)
          y += 7

          doc.setFontSize(10)
          doc.setFont('helvetica', 'normal')
          const descLines = doc.splitTextToSize(step.description, pageWidth - 45)
          doc.text(descLines, 25, y)
          y += descLines.length * 5 + 3

          step.action_items?.forEach((item) => {
            if (y > 275) {
              doc.addPage()
              y = 20
            }
            const itemLines = doc.splitTextToSize(`• ${item}`, pageWidth - 50)
            doc.text(itemLines, 28, y)
            y += itemLines.length * 5
          })
          y += 6
        })
      }

      // Recommendations
      if (diagnostic.recommendations && diagnostic.recommendations.length > 0) {
        if (y > 240) {
          doc.addPage()
          y = 20
        }
        doc.setFontSize(14)
        doc.setFont('helvetica', 'bold')
        doc.text('Recommended Resources', 20, y)
        y += 8

        diagnostic.recommendations.forEach((rec) => {
          if (y > 270) {
            doc.addPage()
            y = 20
          }
          doc.setFontSize(11)
          doc.setFont('helvetica', 'bold')
          doc.text(rec.name, 20, y)
          y += 6
          doc.setFontSize(9)
          doc.setFont('helvetica', 'normal')
          const recLines = doc.splitTextToSize(rec.description, pageWidth - 40)
          doc.text(recLines, 20, y)
          y += recLines.length * 5 + 6
        })
      }

      // Footer disclaimer
      doc.setFontSize(8)
      doc.setTextColor(150)
      doc.text(
        'This report is AI-generated and reviewed by a human consultant. For guidance only, not legal or immigration advice.',
        20,
        290
      )

      doc.save(`Klar_Report_${studentName.replace(/\s+/g, '_')}.pdf`)
    } catch (err) {
      console.error('PDF generation failed:', err)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={generating}
      style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '9999px',
        padding: '10px 24px',
        fontSize: '14px',
        color: '#F9FAFB',
        cursor: generating ? 'wait' : 'pointer',
        opacity: generating ? 0.6 : 1,
        transition: 'all 0.2s',
      }}
    >
      {generating ? 'Generating...' : '📄 Download PDF'}
    </button>
  )
}
