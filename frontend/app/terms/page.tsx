// Spanish translation of legal documents is intentionally deferred pending reviewed translation.
// This page always renders in English regardless of the site language toggle.

import Link from 'next/link'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service — Klar',
  description: 'Terms of Service for Klar, the AI-powered Germany readiness diagnostic platform.',
}

export default function TermsPage() {
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
            Terms of Service
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
            These Terms of Service are currently under review by legal counsel and may be updated.
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
            href="/privacy"
            style={{ color: '#9CA3AF', fontSize: '0.875rem', textDecoration: 'underline' }}
          >
            Privacy Policy
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
        These Terms of Service ("Terms") govern your use of Klar, an AI-powered Germany readiness
        diagnostic and application platform operated by Lucas Barrios ("Klar," "we," "us"). By
        using Klar, you agree to these Terms.
      </p>

      <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)', margin: '40px 0' }} />

      <Section number="1" title="What Klar Is">
        <p style={{ marginBottom: '16px' }}>Klar provides:</p>
        <ul style={{ paddingLeft: '20px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <li>
            A free AI-generated, human-reviewed assessment of your readiness for university,
            Ausbildung, or work-visa pathways to Germany ("the Diagnostic").
          </li>
          <li>
            An optional, one-time paid "Germany Application Kit" (currently €39) that unlocks
            matched Ausbildung and job positions sourced from Germany's Federal Employment Agency,
            and AI-generated bilingual CV and cover letter drafts.
          </li>
        </ul>
        <p>
          Every Diagnostic is reviewed by a human consultant before it is delivered to you. No
          AI-generated result reaches you without this review.
        </p>
      </Section>

      <Section number="2" title="Not Legal, Immigration, Financial, or Employment Advice">
        <p style={{ marginBottom: '16px' }}>
          <strong style={{ color: '#F9FAFB' }}>
            Klar does not provide legal, immigration, financial, or employment advice.
          </strong>{' '}
          Specifically, Klar does not:
        </p>
        <ul style={{ paddingLeft: '20px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <li>Provide legal immigration or visa advice of any kind.</li>
          <li>
            Guarantee admission to any institution, approval of any visa, or placement in any
            Ausbildung or job position.
          </li>
          <li>
            Replace a licensed immigration lawyer, a certified translator, or any other licensed
            professional you may need for your application.
          </li>
          <li>
            Verify the accuracy of information you provide. Your Diagnostic score and any generated
            documents are based entirely on the information you enter, which we do not independently
            confirm.
          </li>
        </ul>
        <p>
          You are solely responsible for verifying any information before relying on it, submitting
          it to a third party, or using it in connection with an immigration, visa, education, or
          employment application.
        </p>
      </Section>

      <Section number="3" title="AI-Generated Content">
        <p style={{ marginBottom: '16px' }}>
          Klar uses artificial intelligence to generate your Diagnostic score, roadmap, and (if you
          purchase the Application Kit) draft application documents. This is disclosed to you before
          you begin the Diagnostic.
        </p>
        <p>
          Generated CV and cover letter drafts use bracketed placeholders (for example,{' '}
          <code
            style={{
              background: 'rgba(255,255,255,0.08)',
              padding: '1px 6px',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '0.875em',
              color: '#93C5FD',
            }}
          >
            [Employer name]
          </code>
          ) for any specific fact Klar cannot verify from the information you provided.{' '}
          <strong style={{ color: '#F9FAFB' }}>
            You must review, complete, and verify every generated document before using it for any
            real application.
          </strong>{' '}
          Klar is not responsible for inaccuracies in a document you have not reviewed and completed
          yourself.
        </p>
      </Section>

      <Section number="4" title="Ownership of Generated Content">
        <p style={{ marginBottom: '16px' }}>
          Documents and content generated specifically for you from your own input data — your
          Diagnostic results, roadmap, matched positions, and any CV or cover letter drafts —
          belong to you. You may use, edit, and share them as you wish.
        </p>
        <p>
          Klar retains all rights to the underlying platform, including its software, prompts,
          scoring methodology, and design. Using Klar does not grant you any rights to these
          underlying systems.
        </p>
      </Section>

      <Section number="5" title="Payment and Refunds">
        <p style={{ marginBottom: '16px' }}>
          The Germany Application Kit is a one-time payment of €39, processed securely through
          Stripe. Klar does not store your payment card details.
        </p>
        <p>
          A full refund is available if requested before the Application Kit's contents (matched
          positions or generated documents) have been accessed or generated. Once the Kit's contents
          have been delivered, the service has been fully performed and no refund applies. To request
          a refund, contact us at the address below.
        </p>
      </Section>

      <Section number="6" title="Your Account and Data">
        <p style={{ marginBottom: '16px' }}>
          Your use of Klar, including what personal data we collect and how we use it, is also
          governed by our{' '}
          <Link
            href="/privacy"
            style={{ color: '#93C5FD', textDecoration: 'underline' }}
          >
            Privacy Policy
          </Link>
          . By using Klar, you also agree to the Privacy Policy.
        </p>
        <p>
          You may request access to, correction of, or deletion of your data at any time — see the
          Privacy Policy for how.
        </p>
      </Section>

      <Section number="7" title="Third-Party Services">
        <p>
          Klar uses third-party services to operate, including Anthropic (AI processing), Stripe
          (payments), Supabase (data storage, EU-based), Resend (transactional email, EU-based),
          and LangSmith (AI observability, with personal data fields redacted before logging). These
          services have their own terms and privacy practices. Full details of what data is shared
          with each are in our{' '}
          <Link href="/privacy" style={{ color: '#93C5FD', textDecoration: 'underline' }}>
            Privacy Policy
          </Link>
          .
        </p>
      </Section>

      <Section number="8" title="Limitation of Liability">
        <p style={{ marginBottom: '16px' }}>
          Klar is provided "as is," without warranties of any kind, express or implied. To the
          fullest extent permitted by law, Klar and its operator are not liable for any decision you
          make, or outcome you experience (including but not limited to visa denial, non-admission,
          or employment outcomes), based on use of the Diagnostic, matched positions, or generated
          documents.
        </p>
        <p>
          Nothing in these Terms limits liability for fraud, gross negligence, or anything else that
          cannot be limited under applicable law.
        </p>
      </Section>

      <Section number="9" title="Changes to These Terms">
        <p>
          We may update these Terms from time to time. If we make material changes, we will update
          the "Last updated" date above. Continued use of Klar after changes means you accept the
          updated Terms.
        </p>
      </Section>

      <Section number="10" title="Governing Law">
        <p>
          These Terms are governed by the laws of Germany. Any disputes will be subject to the
          jurisdiction of the courts of Berlin, Germany, to the extent permitted by applicable
          consumer protection law in your country of residence.
        </p>
      </Section>

      <Section number="11" title="Contact" last>
        <p>
          Questions about these Terms:{' '}
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
