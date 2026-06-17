import ResultsContent, { type Diagnostic } from './ResultsContent'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const FETCH_TIMEOUT_MS = 8000

export default async function ResultsPage(props: {
  params: Promise<{ id: string }>
  searchParams: Promise<Record<string, string>>
}) {
  const { id } = await props.params
  const searchParams = await props.searchParams
  const paymentSuccess = searchParams.payment === 'success'
  const paymentProduct = searchParams.product

  let diagnostic: Diagnostic | null = null
  let notFound = false

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const res = await fetch(`${API_URL}/api/diagnostic/${id}/result`, {
      cache: 'no-store',
      signal: controller.signal,
    })
    if (!res.ok) {
      notFound = true
    } else {
      const data = await res.json()
      diagnostic =
        data.status === 'not_available'
          ? {
              id,
              status: 'rejected',
              overall_score: null,
              summary: null,
              dimension_scores: null,
              roadmap: null,
              recommendations: null,
              completed_steps: null,
              students: null,
            }
          : ({ id, ...data } as Diagnostic)
    }
  } catch {
    notFound = true
  } finally {
    clearTimeout(timer)
  }

  return (
    <ResultsContent
      diagnostic={diagnostic}
      id={id}
      notFound={notFound || !diagnostic}
      paymentSuccess={paymentSuccess}
      paymentProduct={paymentProduct}
    />
  )
}
