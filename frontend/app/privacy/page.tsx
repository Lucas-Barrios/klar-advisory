// Spanish translation of legal documents is intentionally deferred pending reviewed translation.
// This page always renders in English regardless of the site language toggle.

import Link from 'next/link'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy — Klar',
  description: 'Privacy Policy for Klar, the AI-powered Germany readiness diagnostic platform.',
}

export default function PrivacyPage() {
  return (
    <div style={{ background: '#0A0E1A', minHeight: '100vh' }}>
      <div
        style={{
          maxWidth: '720px',
          margin: '0 auto',
          padding: '64px 24px 96px',
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: '48px' }}>
          <p
            style={{
              fontSize: '11px',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: '#6B7280',
              marginBottom: '16px',
            }}
          >
            Legal
          </p>
          <h1
            style={{
              fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
              fontWeight: 700,
              color: '#F9FAFB',
              letterSpacing: '-0.04em',
              lineHeight: 1.1,
              marginBottom: '12px',
            }}
          >
            Privacy Policy
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#6B7280' }}>
            Last updated: June 20, 2026
          </p>
          <p
            style={{
              fontSize: '0.875rem',
              color: '#9CA3AF',
              fontStyle: 'italic',
              marginTop: '8px',
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.04)',
              borderLeft: '3px solid rgba(37,99,235,0.5)',
              borderRadius: '0 6px 6px 0',
            }}
          >
            This Privacy Policy is currently under review by legal counsel and may be updated.
            Operated by Lucas Barrios.
          </p>
        </div>

        <LegalContent />

        {/* Footer nav */}
        <div
          style={{
            marginTop: '64px',
            paddingTop: '32px',
            borderTop: '1px solid rgba(255,255,255,0.08)',
            display: 'flex',
            gap: '24px',
            flexWrap: 'wrap',
          }}
        >
          <Link
            href="/terms"
            style={{ color: '#9CA3AF', fontSize: '0.875rem', textDecoration: 'underline' }}
          >
            Terms of Service
          </Link>
          <Link
            href="/"
            style={{ color: '#9CA3AF', fontSize: '0.875rem', textDecoration: 'underline' }}
          >
            Back to Klar
          </Link>
        </div>
      </div>
    </div>
  )
}

function LegalContent() {
  return (
    <div style={{ color: '#D1D5DB', lineHeight: 1.75, fontSize: '0.9375rem' }}>
      <p style={{ marginBottom: '24px' }}>
        This Privacy Policy explains what personal data Klar collects, why, and how it's protected,
        in plain language. For the legal terms governing your use of Klar generally, see our{' '}
        <Link href="/terms" style={{ color: '#93C5FD', textDecoration: 'underline' }}>
          Terms of Service
        </Link>
        .
      </p>

      <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)', margin: '40px 0' }} />

      <Section number="1" title="What Data We Collect">
        <p style={{ marginBottom: '16px' }}>
          When you complete the Germany Readiness Diagnostic, we collect: your name, email, country,
          age, German and English level, education level, field of study, work experience, your
          timeline, your financial situation, your current location, and any additional context you
          choose to share.
        </p>
        <p style={{ marginBottom: '16px' }}>
          If you purchase the Germany Application Kit and generate documents, we additionally process
          whatever details you choose to add — for example, an employer name, address, or phone
          number you enter to complete your CV.
        </p>
        <p>We never ask for more than what's needed to assess your readiness or generate your documents.</p>
      </Section>

      <Section number="2" title="Why We Collect It, and Our Legal Basis">
        <p style={{ marginBottom: '16px' }}>
          We process your data to deliver the service you've asked for — generating your Diagnostic,
          matching you to real positions, and drafting your application documents. Under GDPR, this
          is processed on the basis of{' '}
          <strong style={{ color: '#F9FAFB' }}>performance of a contract</strong> (Article 6(1)(b)):
          you've asked us to provide this assessment, and we need this information to do it.
        </p>
        <p style={{ marginBottom: '16px' }}>
          Where you've explicitly checked a consent box on the intake form, we also rely on your{' '}
          <strong style={{ color: '#F9FAFB' }}>explicit consent</strong> (Article 6(1)(a)) for that
          specific processing.
        </p>
        <p>
          We keep an internal audit record of key actions (such as a diagnostic being approved) as a{' '}
          <strong style={{ color: '#F9FAFB' }}>legal obligation</strong> under the EU AI Act's
          transparency and record-keeping requirements (Article 6(1)(c)).
        </p>
      </Section>

      <Section number="3" title="Human Review — Not a Fully Automated Decision">
        <p>
          Your Diagnostic score is generated by AI, but it is{' '}
          <strong style={{ color: '#F9FAFB' }}>
            always reviewed by a human consultant before it reaches you
          </strong>
          . This is not a solely automated decision under GDPR Article 22 — a person reviews and
          approves every result.
        </p>
      </Section>

      <Section number="4" title="Who We Share Your Data With">
        <p style={{ marginBottom: '20px' }}>
          We use a small number of carefully chosen service providers to operate Klar. None of them
          are permitted to use your data for their own purposes.
        </p>
        <DataTable />
        <p style={{ marginTop: '20px' }}>
          Where data leaves the EU (Anthropic, Stripe, LangSmith), this is covered by Standard
          Contractual Clauses, the standard legal mechanism for protecting data transferred outside
          the EU.
        </p>
      </Section>

      <Section number="5" title="How Long We Keep Your Data">
        <p>
          We retain your data for 24 months from your last activity with Klar. You can request
          earlier deletion at any time — see Section 6.
        </p>
      </Section>

      <Section number="6" title="Your Rights">
        <p style={{ marginBottom: '16px' }}>You have the right to:</p>
        <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
          <li>
            <strong style={{ color: '#F9FAFB' }}>Access</strong> the data we hold about you
          </li>
          <li>
            <strong style={{ color: '#F9FAFB' }}>Correct</strong> inaccurate data
          </li>
          <li>
            <strong style={{ color: '#F9FAFB' }}>Delete</strong> your data ("right to erasure")
          </li>
          <li>
            <strong style={{ color: '#F9FAFB' }}>Receive a copy</strong> of your data in a portable
            format
          </li>
          <li>
            <strong style={{ color: '#F9FAFB' }}>Object</strong> to certain processing
          </li>
        </ul>
        <p>
          To exercise any of these rights, contact us at{' '}
          <a
            href="mailto:hello@kairosconsulting.co"
            style={{ color: '#93C5FD', textDecoration: 'underline' }}
          >
            hello@kairosconsulting.co
          </a>
          . We will respond within the timeframe required by GDPR.
        </p>
      </Section>

      <Section number="7" title="Security">
        <p>
          Your data is protected in transit via HTTPS, stored in an EU-based database with row-level
          access controls, and accessible only to authorized systems and our reviewing consultant.
        </p>
      </Section>

      <Section number="8" title="Changes to This Policy">
        <p>
          We may update this Privacy Policy from time to time. Material changes will update the
          "Last updated" date above.
        </p>
      </Section>

      <Section number="9" title="Contact" last>
        <p>
          Questions about this Privacy Policy or your data:{' '}
          <a
            href="mailto:hello@kairosconsulting.co"
            style={{ color: '#93C5FD', textDecoration: 'underline' }}
          >
            hello@kairosconsulting.co
          </a>
        </p>
      </Section>
    </div>
  )
}

function DataTable() {
  const rows = [
    {
      service: 'Anthropic',
      what: 'Generates your Diagnostic score and documents',
      where: 'United States',
      data: 'Your profile information, sent for processing only — not stored by Anthropic',
    },
    {
      service: 'Supabase',
      what: 'Stores your data',
      where: 'EU (Frankfurt, Germany)',
      data: 'All data you provide',
    },
    {
      service: 'Stripe',
      what: 'Processes payment for the Application Kit',
      where: 'United States/Ireland',
      data: 'Payment details only — Klar never sees or stores your card number',
    },
    {
      service: 'Resend',
      what: 'Sends you transactional emails (approval notice, payment confirmation)',
      where: 'EU (Ireland)',
      data: 'Your name and email address only',
    },
    {
      service: 'LangSmith',
      what: 'Helps us monitor and improve the AI\'s performance',
      where: 'United States (routed via an EU endpoint)',
      data: 'A version of your request with personal details (name, financial information, address, phone) automatically removed before it\'s logged',
    },
  ]

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.875rem',
          tableLayout: 'fixed',
        }}
      >
        <thead>
          <tr>
            {['Service', 'What it does', 'Where', 'Data shared'].map((h) => (
              <th
                key={h}
                style={{
                  textAlign: 'left',
                  padding: '10px 12px',
                  color: '#9CA3AF',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  borderBottom: '1px solid rgba(255,255,255,0.1)',
                  background: 'rgba(255,255,255,0.03)',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.service}
              style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}
            >
              <td
                style={{
                  padding: '12px 12px',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  color: '#F9FAFB',
                  fontWeight: 600,
                  verticalAlign: 'top',
                }}
              >
                {row.service}
              </td>
              <td
                style={{
                  padding: '12px 12px',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  color: '#D1D5DB',
                  verticalAlign: 'top',
                }}
              >
                {row.what}
              </td>
              <td
                style={{
                  padding: '12px 12px',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  color: '#D1D5DB',
                  verticalAlign: 'top',
                  whiteSpace: 'nowrap',
                }}
              >
                {row.where}
              </td>
              <td
                style={{
                  padding: '12px 12px',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  color: '#9CA3AF',
                  verticalAlign: 'top',
                }}
              >
                {row.data}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Section({
  number,
  title,
  children,
  last = false,
}: {
  number: string
  title: string
  children: React.ReactNode
  last?: boolean
}) {
  return (
    <section style={{ marginBottom: last ? 0 : '40px' }}>
      <h2
        style={{
          fontSize: '1.125rem',
          fontWeight: 700,
          color: '#F9FAFB',
          letterSpacing: '-0.02em',
          marginBottom: '16px',
          display: 'flex',
          gap: '10px',
          alignItems: 'baseline',
        }}
      >
        <span style={{ color: '#4B5563', fontWeight: 500, fontSize: '0.875rem', flexShrink: 0 }}>
          {number}.
        </span>
        {title}
      </h2>
      {children}
      {!last && (
        <hr
          style={{
            border: 'none',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            marginTop: '40px',
          }}
        />
      )}
    </section>
  )
}
