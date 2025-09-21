export function getPostingDay(postingStartAt: string | null): number | null {
  if (!postingStartAt) return null

  const startDate = new Date(postingStartAt)
  const today = new Date()
  const diffTime = Math.abs(today.getTime() - startDate.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  return diffDays
}

export function formatPhase(account: { warmupDay?: number; posting_start_at?: string | null }): string {
  if (account.posting_start_at) {
    const postingDay = getPostingDay(account.posting_start_at)
    return `Posting · Day ${postingDay || 1}`
  }

  return `Warmup · Day ${account.warmupDay || 1}`
}

export function humanizeDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now.getTime() - date.getTime())
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return "today"
  if (diffDays === 1) return "1 day ago"
  return `${diffDays} days ago`
}
