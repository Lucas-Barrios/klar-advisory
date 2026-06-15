import Link from 'next/link'
import { ShareButton } from '../[id]/ShareButton'

type RoadmapStep = {
  month: number
  title: string
  description: string
  action_items: string[]
}

type Recommendation = {
  name: string
  type: string
  description: string
  url: string | null
}

type DimensionScores = {
  language: number
  education: number
  pathway_fit: number
  timeline: number
  financial: number
  documentation: number
}

function scoreColor(score: number): string {
  if (score < 40) return '#EF4444'
  if (score < 60) return '#F59E0B'
  if (score < 80) return '#3B82F6'
  return '#0D9488'
}

function scoreLabel(score: number): { label: string; emoji: string; sub: string } {
  if (score < 40)
    return { label: 'Not ready yet', emoji: '💪', sub: "But don't worry — your roadmap starts here." }
  if (score < 60)
    return { label: 'Getting there', emoji: '📈', sub: "You're closer than you think." }
  if (score < 80)
    return { label: 'Ready with preparation', emoji: '⭐', sub: 'You have a strong foundation.' }
  return { label: 'Strong candidate', emoji: '🚀', sub: 'Germany is within reach.' }
}

const DIMENSIONS: { key: keyof DimensionScores; label: string; icon: string }[] = [
  { key: 'language', label: 'German Language', icon: '🗣️' },
  { key: 'education', label: 'Education', icon: '🎓' },
  { key: 'pathway_fit', label: 'Pathway Fit', icon: '🎯' },
  { key: 'timeline', label: 'Timeline', icon: '⏱️' },
  { key: 'financial', label: 'Finances', icon: '💰' },
  { key: 'documentation', label: 'Documentation', icon: '📋' },
]

const demoStudent = {
  name: 'Carlos Mendoza',
  email: 'carlos@example.com',
  country: 'Colombia',
  pathway: 'ausbildung',
}

const demoDimensionScores: DimensionScores = {
  language: 55,
  education: 72,
  pathway_fit: 80,
  timeline: 65,
  financial: 60,
  documentation: 58,
}

const demoRoadmap: RoadmapStep[] = [
  {
    month: 1,
    title: 'Intensive German language preparation',
    description:
      'Enrol in an intensive A2 to B1 German course. This is your most critical task and should take 15-20 hours per week.',
    action_items: [
      'Register at Goethe Institut or a local language school',
      'Download the Duolingo German course as a daily supplement',
      'Join a German language exchange group online',
    ],
  },
  {
    month: 2,
    title: 'Research Ausbildung positions',
    description:
      'Start identifying specific Ausbildung programs in your field. Nursing and IT have the highest vacancy rates and strongest match to your background.',
    action_items: [
      'Browse make-it-in-germany.com for your sector',
      'Create a profile on the Bundesagentur für Arbeit job portal',
      'Identify 10 target companies or hospitals in Berlin and Munich',
    ],
  },
  {
    month: 3,
    title: 'Document preparation',
    description:
      'Begin the credential recognition process for your Colombian degree. This can take 3-6 months so starting early is critical.',
    action_items: [
      'Request official transcripts from your university',
      'Contact the ZAB (Central Office for Foreign Education) for credential assessment',
      'Get documents officially translated by a sworn translator',
    ],
  },
  {
    month: 4,
    title: 'Reach B1 German — take the exam',
    description:
      'Sit the Goethe Institut B1 exam. This certificate unlocks most Ausbildung applications and is required for the visa.',
    action_items: [
      'Book the Goethe Institut B1 exam at least 4 weeks in advance',
      'Complete 2 full practice tests in the week before',
      'Get your results certificate — keep digital and physical copies',
    ],
  },
  {
    month: 5,
    title: 'Apply to Ausbildung positions',
    description:
      'With B1 certificate in hand, start sending applications. Tailor each cover letter to the specific company.',
    action_items: [
      'Send minimum 10 applications to nursing/IT Ausbildung positions',
      "Write a cover letter in German (use Klar's document service)",
      'Prepare for interviews — practice common German HR questions',
    ],
  },
  {
    month: 6,
    title: 'Visa application preparation',
    description:
      'Once you have an Ausbildung offer, begin the visa application process immediately.',
    action_items: [
      'Schedule appointment at German embassy in Bogotá',
      'Gather all required documents: offer letter, B1 certificate, credential recognition, blocked account proof',
      'Open a German blocked account (Sperrkonto) — Fintiba or Expatrio are recommended',
    ],
  },
  {
    month: 7,
    title: 'Submit visa application',
    description:
      'Attend your embassy appointment with all documents. Processing typically takes 6-12 weeks.',
    action_items: [
      'Attend embassy appointment',
      'Pay visa fee (~€75)',
      'Track application status through the embassy portal',
    ],
  },
  {
    month: 8,
    title: 'Prepare for arrival in Germany',
    description: 'While waiting for your visa, prepare practically for life in Germany.',
    action_items: [
      'Research accommodation in your target city',
      'Open a German bank account (N26 or Deutsche Bank) online',
      'Join Facebook groups and communities for Latin Americans in Germany',
    ],
  },
]

const demoRecommendations: Recommendation[] = [
  {
    name: 'Goethe Institut German Courses',
    type: 'course',
    description:
      'The gold standard for German language certification. Carlos needs B1 as his priority. Courses available online and in Colombia.',
    url: 'https://www.goethe.de',
  },
  {
    name: 'Make it in Germany — Ausbildung Portal',
    type: 'platform',
    description:
      'Official German government portal for international Ausbildung seekers. Lists thousands of open positions with English explanations.',
    url: 'https://www.make-it-in-germany.com',
  },
  {
    name: 'DAAD Scholarship Programs',
    type: 'organization',
    description:
      'German Academic Exchange Service — offers funded programs for Colombian and Brazilian students. Carlos may qualify for the Helmut Schmidt Programme.',
    url: 'https://www.daad.de',
  },
]

const score = 68
const dims = demoDimensionScores
const { label, emoji, sub } = scoreLabel(score)
const color = scoreColor(score)
const circumference = 2 * Math.PI * 54
const dashOffset = circumference * (1 - score / 100)

export default function DemoResultsPage() {
  return (
    <div style={{ background: '#0A0E1A', minHeight: '100vh' }}>
      {/* Demo banner */}
      <div style={{
        background: 'rgba(245,158,11,0.1)',
        borderBottom: '1px solid rgba(245,158,11,0.2)',
        paddingTop: '8px',
        paddingBottom: '8px',
        paddingLeft: '16px',
        paddingRight: '16px',
        textAlign: 'center',
        fontSize: '14px',
        color: '#F59E0B',
      }}>
        ⚡ This is a sample result.{' '}
        <Link href="/diagnostic" style={{ color: '#F59E0B', textDecoration: 'underline' }}>
          Start your free diagnostic
        </Link>
        {' '}to get your personalised score →
      </div>

      <div className="max-w-3xl mx-auto px-4 py-16">

        {/* Section 1 — Hero score */}
        <div className="text-center animate-fade-up" style={{ paddingBottom: '64px' }}>
          <p className="animate-fade-up" style={{ color: '#9CA3AF', fontSize: '1.125rem' }}>
            Here are your results, {demoStudent.name.split(' ')[0]}.
          </p>

          <div className="flex justify-center mt-8 animate-fade-up delay-1">
            <svg width="180" height="180" viewBox="0 0 120 120">
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3B82F6" />
                  <stop offset="100%" stopColor="#8B5CF6" />
                </linearGradient>
              </defs>
              <circle cx="60" cy="60" r="54" fill="none" stroke="#1F2937" strokeWidth="8" />
              <circle
                cx="60"
                cy="60"
                r="54"
                fill="none"
                stroke="url(#scoreGradient)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${circumference}`}
                strokeDashoffset={`${dashOffset}`}
                style={{ transform: 'rotate(-90deg)', transformOrigin: '60px 60px' }}
              />
              <text
                x="60"
                y="56"
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#F9FAFB"
                fontSize="22"
                fontWeight="700"
                fontFamily="system-ui"
              >
                {score}
              </text>
              <text
                x="60"
                y="74"
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#9CA3AF"
                fontSize="11"
                fontFamily="system-ui"
              >
                /100
              </text>
            </svg>
          </div>

          <div className="mt-4 animate-fade-up delay-2">
            <span className="text-2xl">{emoji}</span>
            <p className="font-bold text-2xl mt-2" style={{ color, letterSpacing: '-0.02em' }}>
              {label}
            </p>
            <p className="text-sm mt-1" style={{ color: '#9CA3AF' }}>
              {sub}
            </p>
          </div>

          <p
            className="mx-auto mt-6 leading-relaxed animate-fade-up delay-3"
            style={{ color: '#9CA3AF', fontSize: '1.0625rem', maxWidth: '560px' }}
          >
            Carlos has a strong educational background and a good fit for the Ausbildung pathway,
            particularly in healthcare and engineering sectors. His main focus for the next 3 months
            should be improving his German from A2 to B1, which will unlock the majority of
            Ausbildung positions in his target field.
          </p>
        </div>

        {/* Section 2 — Dimension scores */}
        <div style={{ paddingBottom: '64px' }}>
          <h2
            className="font-bold mb-8 animate-fade-up delay-2"
            style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
          >
            Your scores
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {DIMENSIONS.map(({ key, label: dimLabel, icon }, index) => {
              const val = dims[key] ?? 0
              const c = scoreColor(val)
              const delayClass = `delay-${index + 1}` as
                | 'delay-1'
                | 'delay-2'
                | 'delay-3'
                | 'delay-4'
                | 'delay-5'
                | 'delay-6'
              return (
                <div
                  key={key}
                  className={`glass rounded-2xl animate-fade-up ${delayClass}`}
                  style={{ padding: '24px' }}
                >
                  <span style={{ fontSize: '1.5rem' }}>{icon}</span>
                  <div className="font-bold mt-2" style={{ fontSize: '1.875rem', color: c }}>
                    {val}
                  </div>
                  <div className="text-sm mt-1" style={{ color: '#9CA3AF' }}>
                    {dimLabel}
                  </div>
                  <div
                    className="rounded-full overflow-hidden mt-3"
                    style={{ height: '6px', background: '#1F2937' }}
                  >
                    <div
                      style={
                        {
                          height: '100%',
                          borderRadius: '9999px',
                          background: c,
                          '--target-width': `${val}%`,
                          animation: `fillBar 1s ease forwards`,
                          animationDelay: `${0.3 + index * 0.1}s`,
                          width: '0%',
                        } as React.CSSProperties
                      }
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Section 3 — Roadmap */}
        <div style={{ paddingBottom: '64px' }}>
          <h2
            className="font-bold mb-2 animate-fade-up"
            style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
          >
            Your roadmap
          </h2>
          <p className="mb-8 animate-fade-up" style={{ color: '#9CA3AF' }}>
            Month by month, step by step.
          </p>

          <div style={{ position: 'relative' }}>
            {demoRoadmap.map((step, i) => (
              <div
                key={i}
                className={`animate-fade-up delay-${Math.min(i + 1, 8) as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8}`}
                style={{ position: 'relative', paddingLeft: '48px', paddingBottom: '32px' }}
              >
                {i < demoRoadmap.length - 1 && (
                  <div
                    style={{
                      position: 'absolute',
                      left: '15px',
                      top: '28px',
                      bottom: 0,
                      width: '2px',
                      background: '#1F2937',
                    }}
                  />
                )}

                <div
                  className="flex items-center justify-center font-bold"
                  style={{
                    position: 'absolute',
                    left: '4px',
                    top: '4px',
                    width: '24px',
                    height: '24px',
                    borderRadius: '9999px',
                    background: '#3B82F6',
                    color: 'white',
                    fontSize: '0.65rem',
                  }}
                >
                  {step.month}
                </div>

                <div className="glass rounded-xl" style={{ padding: '20px' }}>
                  <div
                    className="uppercase tracking-wider"
                    style={{ fontSize: '0.6875rem', color: '#6B7280', marginBottom: '4px' }}
                  >
                    Month {step.month}
                  </div>
                  <h3 className="font-semibold" style={{ color: '#F9FAFB', fontSize: '1.0625rem' }}>
                    {step.title}
                  </h3>
                  <p className="mt-2 leading-relaxed" style={{ color: '#9CA3AF', fontSize: '0.9375rem' }}>
                    {step.description}
                  </p>
                  {step.action_items.length > 0 && (
                    <ul className="mt-3 space-y-1">
                      {step.action_items.map((item, j) => (
                        <li key={j} className="flex gap-2 text-sm" style={{ color: '#9CA3AF' }}>
                          <span
                            style={{
                              width: '6px',
                              height: '6px',
                              borderRadius: '9999px',
                              background: '#3B82F6',
                              marginTop: '6px',
                              flexShrink: 0,
                            }}
                          />
                          {item}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4 — Recommendations */}
        <div style={{ paddingBottom: '64px' }}>
          <h2
            className="font-bold mb-8 animate-fade-up"
            style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
          >
            Recommended for you
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {demoRecommendations.map((rec, i) => (
              <div
                key={i}
                className={`glass rounded-2xl animate-fade-up delay-${Math.min(i + 1, 3) as 1 | 2 | 3}`}
                style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}
              >
                <span
                  className="rounded-full text-xs font-medium inline-block self-start mb-4"
                  style={{
                    background: 'rgba(59,130,246,0.1)',
                    color: '#3B82F6',
                    border: '1px solid rgba(59,130,246,0.2)',
                    padding: '3px 12px',
                  }}
                >
                  {rec.type}
                </span>
                <h3 className="font-semibold" style={{ color: '#F9FAFB', fontSize: '1rem' }}>
                  {rec.name}
                </h3>
                <p className="mt-2 leading-relaxed flex-1" style={{ color: '#9CA3AF', fontSize: '0.875rem' }}>
                  {rec.description}
                </p>
                {rec.url && (
                  <a
                    href={rec.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 block text-sm hover:underline"
                    style={{ color: '#3B82F6' }}
                  >
                    Visit →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Section 5 — CTA */}
        <div
          className="text-center animate-fade-up"
          style={{ paddingTop: '48px', paddingBottom: '48px' }}
        >
          <h2
            className="font-bold"
            style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
          >
            Ready to take the next step?
          </h2>
          <p className="mt-2 mb-6" style={{ color: '#9CA3AF' }}>
            Klar is in early access. Get your own personalised diagnostic in 3 minutes.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <ShareButton id="demo" />
            <a
              href="/diagnostic"
              className="font-semibold rounded-full transition-all"
              style={{
                background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                color: 'white',
                padding: '12px 24px',
              }}
            >
              Start my diagnostic →
            </a>
          </div>
        </div>

        <p className="text-xs text-center mt-8 pb-8" style={{ color: '#6B7280' }}>
          Results are reviewed by a human consultant and are for guidance only. Not legal or
          immigration advice.
        </p>
      </div>
    </div>
  )
}
