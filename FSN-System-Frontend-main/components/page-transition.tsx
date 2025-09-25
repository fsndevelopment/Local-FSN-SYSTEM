"use client"

import { usePathname } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { useEffect, useState } from "react"

interface PageTransitionProps {
  children: React.ReactNode
}

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname()
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [displayChildren, setDisplayChildren] = useState(children)

  useEffect(() => {
    setIsTransitioning(true)
    
    // Wait for exit animation to complete, then update content
    const timer = setTimeout(() => {
      setDisplayChildren(children)
      setIsTransitioning(false)
    }, 150) // Half the total transition time

    return () => clearTimeout(timer)
  }, [pathname, children])

  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatePresence mode="wait">
        {!isTransitioning ? (
          <motion.div
            key={pathname}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ 
              duration: 0.15,
              ease: "easeInOut"
            }}
            className="min-h-screen"
          >
            {displayChildren}
          </motion.div>
        ) : (
          <motion.div
            key="transitioning"
            initial={{ opacity: 1 }}
            animate={{ opacity: 0 }}
            transition={{ 
              duration: 0.15,
              ease: "easeInOut"
            }}
            className="min-h-screen"
          >
            {displayChildren}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Simple loading overlay for specific components
export function SmoothLoader({ isLoading, children }: { isLoading: boolean, children: React.ReactNode }) {
  return (
    <div className="relative">
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex items-center justify-center rounded-xl"
          >
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-gray-300 border-t-black rounded-full animate-spin"></div>
              <span className="text-sm text-gray-600">Loading...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <motion.div
        animate={{ opacity: isLoading ? 0.3 : 1 }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    </div>
  )
}
