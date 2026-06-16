import ResultsContent, { type Diagnostic } from './ResultsContent'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default async function ResultsPage(props: PageProps<'/results/[id]'>) {
  const { id } = await props.params

  let diagnostic: Diagnostic | null = null
  let notFound = false

  try {
    const res = await fetch(`${API_URL}/api/diagnostic/${id}/result`, {
      cache: 'no-store',
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
  }

  return (
    <ResultsContent
      diagnostic={diagnostic}
      id={id}
      notFound={notFound || !diagnostic}
    />
  )
}
