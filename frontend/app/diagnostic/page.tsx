'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useLanguage } from '@/lib/LanguageContext'

type QuestionType = 'text' | 'email' | 'choice'

type ChoiceOption = {
  value: string
  label: string
  description?: string
  emoji: string
}

type Question = {
  id: string
  type: QuestionType
  question: string
  placeholder?: string
  required: boolean
  hint?: string | null
  options?: ChoiceOption[]
}

type Answers = Record<string, string>

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function buildQuestions(f: ReturnType<typeof useLanguage>['t']['form']): Question[] {
  return [
    {
      id: 'name',
      type: 'text',
      question: f.step1Q,
      placeholder: 'Your full name',
      required: true,
      hint: f.step1Hint,
    },
    {
      id: 'email',
      type: 'email',
      question: f.step2Q,
      placeholder: 'your@email.com',
      required: true,
      hint: f.step2Hint,
    },
    {
      id: 'country',
      type: 'text',
      question: f.step3Q,
      placeholder: 'e.g. Colombia, Brazil, Mexico...',
      required: true,
      hint: null,
    },
    {
      id: 'pathway',
      type: 'choice',
      question: f.pathwayQ,
      required: true,
      options: [
        {
          value: 'university',
          label: 'Study at university',
          description: "Bachelor's, Master's, or PhD programs",
          emoji: '🎓',
        },
        {
          value: 'ausbildung',
          label: 'Ausbildung',
          description: 'Vocational training · €700–1,200/month salary',
          emoji: '🔧',
        },
        {
          value: 'work_visa',
          label: 'Work in Germany',
          description: 'Skilled worker visa or Blue Card',
          emoji: '💼',
        },
      ],
    },
    {
      id: 'german_level',
      type: 'choice',
      question: f.germanQ,
      required: true,
      hint: f.germanHint,
      options: [
        { value: 'none', label: 'None', description: "I don't speak German yet", emoji: '😅' },
        { value: 'A1', label: 'A1', description: 'Just started', emoji: '🌱' },
        { value: 'A2', label: 'A2', description: 'Basic conversations', emoji: '💬' },
        { value: 'B1', label: 'B1', description: 'Intermediate', emoji: '📈' },
        { value: 'B2', label: 'B2', description: 'Upper intermediate', emoji: '⭐' },
        { value: 'C1', label: 'C1', description: 'Advanced', emoji: '🔥' },
        { value: 'C2', label: 'C2', description: 'Mastery', emoji: '🏆' },
      ],
    },
    {
      id: 'education_level',
      type: 'choice',
      question: f.educationQ,
      required: true,
      options: [
        { value: 'high_school', label: 'High School', emoji: '📚' },
        { value: 'vocational', label: 'Vocational Training', emoji: '🛠️' },
        { value: 'bachelor', label: "Bachelor's Degree", emoji: '🎓' },
        { value: 'master', label: "Master's Degree", emoji: '📜' },
        { value: 'phd', label: 'PhD', emoji: '🔬' },
      ],
    },
    {
      id: 'field_of_study',
      type: 'text',
      question: f.fieldQ,
      placeholder: 'e.g. Nursing, Software Engineering, Business...',
      required: false,
      hint: f.fieldHint,
    },
    {
      id: 'work_experience_years',
      type: 'choice',
      question: f.experienceQ,
      required: true,
      options: [
        { value: '0', label: 'None yet', emoji: '🎒' },
        { value: '1', label: '1–2 years', emoji: '📅' },
        { value: '3', label: '3–5 years', emoji: '💪' },
        { value: '5', label: '5+ years', emoji: '🚀' },
      ],
    },
    {
      id: 'timeline',
      type: 'choice',
      question: f.timelineQ,
      required: true,
      options: [
        { value: '6_months', label: 'Within 6 months', description: 'I am ready to move fast', emoji: '⚡' },
        { value: '1_year', label: 'Within 1 year', description: 'I have time to prepare properly', emoji: '📆' },
        { value: '2_years_plus', label: 'In 2+ years', description: 'I am planning ahead', emoji: '🔭' },
      ],
    },
    {
      id: 'financial_situation',
      type: 'choice',
      question: f.financialQ,
      required: true,
      hint: f.financialHint,
      options: [
        {
          value: 'I have savings to cover initial costs (10,000+ EUR)',
          label: 'I have savings',
          description: '10,000+ EUR available',
          emoji: '💰',
        },
        {
          value: 'I have some savings but need funded options',
          label: 'Some savings',
          description: 'Looking for scholarships or funding',
          emoji: '🔍',
        },
        {
          value: 'I need fully funded or paid pathways',
          label: 'Need full funding',
          description: 'Ausbildung salary or scholarships only',
          emoji: '🙏',
        },
      ],
    },
    {
      id: 'english_level',
      type: 'choice',
      question: f.englishQ,
      required: false,
      options: [
        { value: 'Basic', label: 'Basic', emoji: '🌱' },
        { value: 'Intermediate', label: 'Intermediate', emoji: '💬' },
        { value: 'Advanced', label: 'Advanced', emoji: '⭐' },
        { value: 'Fluent', label: 'Fluent', emoji: '🔥' },
      ],
    },
  ]
}

export default function DiagnosticPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const f = t.form

  const questions = buildQuestions(f)

  const loadingMessages = [
    f.loading1,
    f.loading2,
    f.loading3,
    f.loading4,
    f.loading5,
    f.loading6,
  ]

  const [currentQ, setCurrentQ] = useState(0)
  const [answers, setAnswers] = useState<Answers>({})
  const [textInput, setTextInput] = useState('')
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0)
  const [error, setError] = useState('')

  const question = questions[currentQ]
  const progressPct = (currentQ / questions.length) * 100

  useEffect(() => {
    if (question.type === 'text' || question.type === 'email') {
      setTextInput(answers[question.id] ?? '')
    }
  }, [currentQ, question.id, question.type, answers])

  useEffect(() => {
    if (!isLoading) return
    const interval = setInterval(() => {
      setLoadingMessageIndex((i) => (i + 1) % loadingMessages.length)
    }, 2500)
    return () => clearInterval(interval)
  }, [isLoading, loadingMessages.length])

  const advance = useCallback(
    (value?: string) => {
      const id = question.id
      const val = value ?? textInput

      if (question.required && !val) return

      setAnswers((prev) => ({ ...prev, [id]: val }))
      setDirection('forward')

      if (currentQ < questions.length - 1) {
        setCurrentQ((q) => q + 1)
      } else {
        submit({ ...answers, [id]: val })
      }
    },
    [currentQ, question, textInput, answers] // eslint-disable-line react-hooks/exhaustive-deps
  )

  const goBack = () => {
    if (currentQ === 0) return
    setDirection('backward')
    setCurrentQ((q) => q - 1)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') advance()
  }

  const handleChoiceSelect = (value: string) => {
    setTimeout(() => advance(value), 400)
    setAnswers((prev) => ({ ...prev, [question.id]: value }))
  }

  async function submit(finalAnswers: Answers) {
    setIsLoading(true)
    setError('')

    const payload = {
      name: finalAnswers.name,
      email: finalAnswers.email,
      country: finalAnswers.country,
      pathway: finalAnswers.pathway,
      german_level: finalAnswers.german_level,
      english_level: finalAnswers.english_level || 'Intermediate',
      education_level: finalAnswers.education_level,
      field_of_study: finalAnswers.field_of_study || '',
      work_experience_years: parseInt(finalAnswers.work_experience_years || '0'),
      timeline: finalAnswers.timeline,
      financial_situation: finalAnswers.financial_situation,
      current_location: '',
      additional_info: '',
    }

    try {
      const res = await fetch(`${API_URL}/api/diagnostic/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const errBody = await res.text()
        throw new Error(`HTTP ${res.status}: ${errBody}`)
      }
      const data = await res.json()
      if (data.progress_token) {
        sessionStorage.setItem(
          `klar_progress_token_${data.diagnostic_id}`,
          data.progress_token
        )
      }
      router.push(`/results/${data.diagnostic_id}`)
    } catch (err) {
      console.error('Submission error:', err)
      setError(`Error: ${err instanceof Error ? err.message : JSON.stringify(err)}`)
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center px-4 text-center"
        style={{ background: '#0A0E1A' }}
      >
        <div className="pulsing-logo font-bold text-3xl mb-8" style={{ letterSpacing: '-0.03em' }}>
          Klar 🇩🇪
        </div>

        <svg width="80" height="80" viewBox="0 0 80 80">
          <defs>
            <linearGradient id="spinGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#8B5CF6" />
            </linearGradient>
          </defs>
          <circle cx="40" cy="40" r="34" fill="none" stroke="#1F2937" strokeWidth="6" />
          <circle
            cx="40"
            cy="40"
            r="34"
            fill="none"
            stroke="url(#spinGradient)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray="53 160"
            style={{
              transformOrigin: '40px 40px',
              animation: 'spin 1.2s linear infinite',
            }}
          />
        </svg>

        <p className="text-lg mt-6" style={{ color: '#9CA3AF' }}>
          {loadingMessages[loadingMessageIndex]}
        </p>
        <p className="text-sm mt-3" style={{ color: '#6B7280' }}>
          {f.loadingSub}
        </p>

        {error && (
          <div
            className="mt-6 rounded-xl p-4 text-sm"
            style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)',
              color: '#EF4444',
              maxWidth: '400px',
            }}
          >
            {error}
            <button
              onClick={() => setIsLoading(false)}
              className="block mt-2 underline text-sm"
              style={{ color: '#EF4444' }}
            >
              {f.backBtn}
            </button>
          </div>
        )}
      </div>
    )
  }

  const isLastQuestion = currentQ === questions.length - 1
  const selectedValue = answers[question.id]

  const getQuestionText = () => {
    if (currentQ === 4 && answers.name) {
      return f.germanQPersonal.replace('{name}', answers.name.split(' ')[0])
    }
    return question.question
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: '#0A0E1A' }}
    >
      {/* Progress bar */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          height: '3px',
          width: `${progressPct}%`,
          background: 'linear-gradient(90deg, #3B82F6, #8B5CF6)',
          transition: 'width 0.4s ease',
          zIndex: 100,
        }}
      />

      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'fixed',
            top: '16px',
            right: '16px',
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <button
            onClick={() => {
              const demoAnswers = {
                name: 'Sofia Ramirez',
                email: 'sofia.demo@klar.app',
                country: 'Brazil',
                pathway: 'ausbildung',
                german_level: 'B1',
                education_level: 'bachelor',
                field_of_study: 'Mechanical Engineering',
                work_experience_years: '3',
                timeline: '1_year',
                financial_situation: 'I have some savings but need funded options',
                english_level: 'Advanced',
              }
              setAnswers(demoAnswers)
              setCurrentQ(questions.length - 1)
            }}
            style={{
              background: 'rgba(139, 92, 246, 0.15)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              color: '#C4B5FD',
              fontSize: '12px',
              padding: '6px 14px',
              borderRadius: '9999px',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            ⚡ Demo Fill
          </button>
          <button
            onClick={() => {
              const demoAnswers = {
                name: 'Sofia Ramirez',
                email: 'sofia.demo@klar.app',
                country: 'Brazil',
                pathway: 'ausbildung',
                german_level: 'B1',
                education_level: 'bachelor',
                field_of_study: 'Mechanical Engineering',
                work_experience_years: '3',
                timeline: '1_year',
                financial_situation: 'I have some savings but need funded options',
                english_level: 'Advanced',
              }
              setAnswers(demoAnswers)
              submit(demoAnswers)
            }}
            style={{
              background: 'rgba(59, 130, 246, 0.15)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              color: '#93C5FD',
              fontSize: '12px',
              padding: '6px 14px',
              borderRadius: '9999px',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            ⚡⚡ Demo Fill + Submit
          </button>
        </div>
      )}

      <div style={{ width: '100%', maxWidth: '640px' }}>
        <div
          key={`${currentQ}-${direction}`}
          className={direction === 'forward' ? 'slide-in-right' : 'slide-in-left'}
        >
          {/* Counter */}
          <p className="text-sm mb-4" style={{ color: '#6B7280' }}>
            {currentQ + 1} / {questions.length}
          </p>

          {/* Question */}
          <h2
            className="font-bold mb-2"
            style={{
              fontSize: 'clamp(1.75rem, 5vw, 2.75rem)',
              letterSpacing: '-0.02em',
              color: '#F9FAFB',
              lineHeight: 1.15,
            }}
          >
            {getQuestionText()}
          </h2>

          {/* Hint */}
          {question.hint && (
            <p className="mb-6 text-sm" style={{ color: '#6B7280' }}>
              {question.hint}
            </p>
          )}

          {/* Text / email input */}
          {(question.type === 'text' || question.type === 'email') && (
            <div className={question.hint ? '' : 'mt-6'}>
              <input
                type={question.type}
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={question.placeholder}
                autoFocus
                style={{
                  background: 'transparent',
                  border: 'none',
                  borderBottom: '2px solid #1F2937',
                  color: '#F9FAFB',
                  fontSize: '1.5rem',
                  padding: '12px 0',
                  width: '100%',
                  maxWidth: '480px',
                  outline: 'none',
                  letterSpacing: '-0.01em',
                  display: 'block',
                }}
                onFocus={(e) => (e.target.style.borderBottomColor = '#3B82F6')}
                onBlur={(e) => (e.target.style.borderBottomColor = '#1F2937')}
              />
              <style>{`input::placeholder { color: #4B5563; }`}</style>
              {question.id === 'email' && textInput.includes('@') && textInput.includes('.') && (
                <div style={{
                  marginTop: '12px',
                  padding: '10px 16px',
                  background: 'rgba(13,148,136,0.1)',
                  border: '1px solid rgba(13,148,136,0.25)',
                  borderRadius: '8px',
                  fontSize: '13px',
                  color: '#5EEAD4',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  maxWidth: '480px',
                }}>
                  <span>✓</span>
                  <span>We&apos;ll send your results to <strong>{textInput}</strong></span>
                </div>
              )}
              <p className="mt-3 text-xs" style={{ color: '#6B7280' }}>
                {f.pressEnter}
              </p>
            </div>
          )}

          {/* Choice options */}
          {question.type === 'choice' && question.options && (
            <div
              className="grid gap-3 mt-6"
              style={{
                gridTemplateColumns:
                  question.options.length === 2 ? 'repeat(2, 1fr)' : '1fr',
                maxWidth: '560px',
              }}
            >
              {question.options.map((opt) => {
                const isSelected = selectedValue === opt.value
                return (
                  <button
                    key={opt.value}
                    onClick={() => handleChoiceSelect(opt.value)}
                    className="glass rounded-xl text-left transition-all"
                    style={{
                      padding: '16px',
                      border: isSelected
                        ? '1px solid #3B82F6'
                        : '1px solid rgba(255,255,255,0.08)',
                      background: isSelected
                        ? 'rgba(59,130,246,0.12)'
                        : 'rgba(255,255,255,0.04)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      width: '100%',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) {
                        const el = e.currentTarget as HTMLButtonElement
                        el.style.borderColor = 'rgba(59,130,246,0.5)'
                        el.style.background = 'rgba(59,130,246,0.08)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) {
                        const el = e.currentTarget as HTMLButtonElement
                        el.style.borderColor = 'rgba(255,255,255,0.08)'
                        el.style.background = 'rgba(255,255,255,0.04)'
                      }
                    }}
                  >
                    <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{opt.emoji}</span>
                    <div style={{ flex: 1 }}>
                      <div className="font-semibold" style={{ color: '#F9FAFB' }}>
                        {opt.label}
                      </div>
                      {opt.description && (
                        <div className="text-sm mt-0.5" style={{ color: '#9CA3AF' }}>
                          {opt.description}
                        </div>
                      )}
                    </div>
                    {isSelected && (
                      <span className="text-sm font-bold" style={{ color: '#3B82F6', flexShrink: 0 }}>
                        ✓
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          )}

          {/* Final email reminder */}
          {isLastQuestion && answers.email && (
            <div style={{
              marginTop: '16px',
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px',
              fontSize: '13px',
              color: '#9CA3AF',
              maxWidth: '560px',
            }}>
              📧 Results will be sent to <strong style={{ color: '#F9FAFB' }}>{answers.email}</strong> once reviewed by our consultant.
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-10" style={{ maxWidth: '560px' }}>
            {currentQ > 0 ? (
              <button
                onClick={goBack}
                className="text-sm transition-colors"
                style={{ color: '#9CA3AF' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#F9FAFB')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#9CA3AF')}
              >
                {f.backBtn}
              </button>
            ) : (
              <div />
            )}

            {(question.type === 'text' || question.type === 'email') && (
              <>
                {isLastQuestion ? (
                  <button
                    onClick={() => advance()}
                    disabled={question.required && !textInput}
                    className="w-full font-semibold rounded-xl transition-all"
                    style={{
                      background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                      color: 'white',
                      padding: '16px',
                      fontSize: '1.125rem',
                      opacity: question.required && !textInput ? 0.4 : 1,
                      cursor: question.required && !textInput ? 'not-allowed' : 'pointer',
                      maxWidth: '560px',
                    }}
                  >
                    {f.submitBtn}
                  </button>
                ) : (
                  <button
                    onClick={() => advance()}
                    disabled={question.required && !textInput}
                    className="glass rounded-xl text-sm font-semibold transition-all"
                    style={{
                      padding: '10px 20px',
                      border: '1px solid rgba(59,130,246,0.4)',
                      color: '#3B82F6',
                      opacity: question.required && !textInput ? 0.4 : 1,
                      cursor: question.required && !textInput ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {f.continueBtn}
                  </button>
                )}
              </>
            )}

            {question.type === 'choice' && isLastQuestion && (
              <button
                onClick={() => advance(selectedValue)}
                disabled={!selectedValue}
                className="font-semibold rounded-xl transition-all"
                style={{
                  background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                  color: 'white',
                  padding: '14px 28px',
                  fontSize: '1rem',
                  opacity: !selectedValue ? 0.4 : 1,
                  cursor: !selectedValue ? 'not-allowed' : 'pointer',
                }}
              >
                {f.submitBtn}
              </button>
            )}
          </div>

          {error && (
            <div
              className="mt-6 rounded-xl p-4 text-sm"
              style={{
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.3)',
                color: '#EF4444',
                maxWidth: '560px',
              }}
            >
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
