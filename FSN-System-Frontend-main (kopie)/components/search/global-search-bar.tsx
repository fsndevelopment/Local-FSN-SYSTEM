"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, X, Clock, TrendingUp } from "lucide-react"
import { searchService, type SearchResult, type SearchFilters } from "@/lib/services/search-service"

interface GlobalSearchBarProps {
  className?: string
  placeholder?: string
}

export function GlobalSearchBar({ 
  className = "", 
  placeholder = "Search devices, accounts, jobs..." 
}: GlobalSearchBarProps) {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const [filters, setFilters] = useState<SearchFilters>({})
  
  const inputRef = useRef<HTMLInputElement>(null)
  const resultsRef = useRef<HTMLDivElement>(null)

  // Search service now loads data directly from local storage

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recent-searches')
    if (saved) {
      setRecentSearches(JSON.parse(saved))
    }
  }, [])

  // Search function with debouncing
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setSuggestions([])
      return
    }

    const timeoutId = setTimeout(() => {
      const searchResults = searchService.search(query, filters)
      const searchSuggestions = searchService.getSuggestions(query)
      
      setResults(searchResults)
      setSuggestions(searchSuggestions)
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [query, filters])

  // Handle search input
  const handleInputChange = (value: string) => {
    setQuery(value)
    setIsOpen(true)
  }

  // Handle result click
  const handleResultClick = (result: SearchResult) => {
    // Save to recent searches
    const newRecent = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5)
    setRecentSearches(newRecent)
    localStorage.setItem('recent-searches', JSON.stringify(newRecent))

    // Navigate to result
    router.push(result.url)
    setIsOpen(false)
    setQuery("")
  }

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    setIsOpen(true)
  }

  // Handle recent search click
  const handleRecentClick = (search: string) => {
    setQuery(search)
    setIsOpen(true)
  }

  // Clear search
  const clearSearch = () => {
    setQuery("")
    setResults([])
    setSuggestions([])
    setIsOpen(false)
    inputRef.current?.focus()
  }

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (resultsRef.current && !resultsRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  return (
    <div className={`relative ${className}`} ref={resultsRef}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          className="pl-10 pr-10 rounded-full border-border bg-background"
        />
        {query && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearSearch}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
          >
            <X className="w-3 h-3" />
          </Button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-2xl shadow-lg z-50 max-h-96 overflow-y-auto">
          {query ? (
            <>
              {/* Search Results */}
              {results.length > 0 ? (
                <div className="p-2">
                  <div className="text-xs text-muted-foreground mb-2 px-3">
                    {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
                  </div>
                  {results.map((result) => (
                    <button
                      key={`${result.type}-${result.id}`}
                      onClick={() => handleResultClick(result)}
                      className="w-full text-left p-3 hover:bg-muted/50 rounded-xl transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        {/* Profile picture for models, icon for others */}
                        {result.type === 'model' && result.metadata?.profilePhoto ? (
                          <div className="w-8 h-8 rounded-full overflow-hidden bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                            <img
                              src={result.metadata.profilePhoto}
                              alt={result.title}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        ) : (
                          <span className="text-lg">{result.icon}</span>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{result.title}</div>
                          <div className="text-xs text-muted-foreground truncate">{result.subtitle}</div>
                          <div className="text-xs text-muted-foreground truncate mt-1">{result.description}</div>
                        </div>
                        {result.status && (
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${
                              result.status === 'active' ? 'bg-green-100 text-green-800' :
                              result.status === 'error' || result.status === 'failed' ? 'bg-red-100 text-red-800' :
                              result.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {result.status}
                          </Badge>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-muted-foreground">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <div className="text-sm">No results found for "{query}"</div>
                </div>
              )}

              {/* Search Suggestions */}
              {suggestions.length > 0 && (
                <div className="border-t border-border p-2">
                  <div className="text-xs text-muted-foreground mb-2 px-3">Suggestions</div>
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left p-2 hover:bg-muted/50 rounded-lg transition-colors text-sm"
                    >
                      <TrendingUp className="w-3 h-3 inline mr-2" />
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            /* Recent Searches */
            <div className="p-2">
              <div className="text-xs text-muted-foreground mb-2 px-3">Recent searches</div>
              {recentSearches.length > 0 ? (
                recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => handleRecentClick(search)}
                    className="w-full text-left p-2 hover:bg-muted/50 rounded-lg transition-colors text-sm"
                  >
                    <Clock className="w-3 h-3 inline mr-2" />
                    {search}
                  </button>
                ))
              ) : (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  No recent searches
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

