export function getErrorMessage(err: unknown, context: string): string {
  // Network failure (fetch throws TypeError) or timeout (AbortError)
  if (err instanceof TypeError) {
    return 'Connection issue. Please check your internet and try again.'
  }
  if (err instanceof DOMException && err.name === 'AbortError') {
    return 'Connection issue. Please check your internet and try again.'
  }

  if (err instanceof Error) {
    // Parse "HTTP NNN: ..." format thrown on non-ok responses
    const match = err.message.match(/^HTTP (\d+)/)
    if (match) {
      const status = parseInt(match[1], 10)

      if (status === 422 && context === 'diagnostic') {
        return "Please check that you've agreed to the data sharing terms before submitting."
      }
      if (status === 429) {
        return "You've submitted several requests recently. Please wait a few minutes before trying again."
      }
      if (status === 502 && context === 'diagnostic') {
        return 'Our AI service is temporarily busy. Your answers are saved — please try again in a moment.'
      }
      if (status === 500 && context === 'documents') {
        return 'Document generation hit an issue. Please try again — it usually works on a second attempt.'
      }
      if (status === 500 && context === 'payment') {
        return 'Payment verified but we had trouble unlocking your content. Please refresh this page — if the issue persists, contact hello@kairosconsulting.co'
      }
    }

    // "Failed to fetch" surfaced as an Error (e.g. in some browser environments)
    const lower = err.message.toLowerCase()
    if (lower.includes('failed to fetch') || lower.includes('networkerror')) {
      return 'Connection issue. Please check your internet and try again.'
    }
  }

  return 'Something unexpected happened. Please try again or contact hello@kairosconsulting.co if this keeps occurring.'
}
