/**
 * Global Platform Selection
 * - Persists to localStorage
 * - Readable by API client for header injection
 * - SSR-safe to prevent hydration mismatches
 */

export type Platform = 'all' | 'instagram' | 'threads'

const STORAGE_KEY = 'platform'

// SSR-safe default
const DEFAULT_PLATFORM: Platform = 'all'

export function getPlatform(): Platform {
  if (typeof window === 'undefined') {
    return DEFAULT_PLATFORM
  }
  
  const saved = window.localStorage.getItem(STORAGE_KEY) as Platform | null
  if (saved === 'all' || saved === 'instagram' || saved === 'threads') {
    return saved
  }
  
  return DEFAULT_PLATFORM
}

export function setPlatform(next: Platform): void {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, next)
    window.dispatchEvent(new CustomEvent('platform-changed', { detail: next }))
  }
}

// React hook to subscribe to platform changes
export function usePlatform(): [Platform, (p: Platform) => void] {
  // Lazy import to avoid react import at module top for non-React contexts
  const React = require('react') as typeof import('react')
  
  // Start with default to prevent hydration mismatch
  const [platform, update] = React.useState<Platform>(DEFAULT_PLATFORM)
  const [isHydrated, setIsHydrated] = React.useState(false)

  // Hydrate from localStorage after mount
  React.useEffect(() => {
    const saved = getPlatform()
    update(saved)
    setIsHydrated(true)
  }, [])

  React.useEffect(() => {
    if (!isHydrated) return
    
    const handler = (e: Event) => {
      // @ts-ignore
      const next = (e as CustomEvent).detail as Platform | undefined
      update(next ?? getPlatform())
    }
    window.addEventListener('platform-changed', handler as EventListener)
    return () => window.removeEventListener('platform-changed', handler as EventListener)
  }, [isHydrated])

  const set = React.useCallback((p: Platform) => {
    setPlatform(p)
    update(p)
  }, [])

  return [platform, set]
}


