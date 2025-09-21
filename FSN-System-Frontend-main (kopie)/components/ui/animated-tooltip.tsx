"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface AnimatedTooltipProps {
  children: React.ReactNode
  content: string
  side?: "right" | "left" | "top" | "bottom"
  delay?: number
  className?: string
}

export function AnimatedTooltip({ 
  children, 
  content, 
  side = "right",
  delay = 200,
  className 
}: AnimatedTooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const timeoutRef = useRef<NodeJS.Timeout>()
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  const updatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let x = 0
    let y = 0

    switch (side) {
      case "right":
        x = triggerRect.right + 12
        y = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        break
      case "left":
        x = triggerRect.left - tooltipRect.width - 12
        y = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        break
      case "top":
        x = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
        y = triggerRect.top - tooltipRect.height - 12
        break
      case "bottom":
        x = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
        y = triggerRect.bottom + 12
        break
    }

    // Keep tooltip within viewport
    if (x < 8) x = 8
    if (x + tooltipRect.width > viewportWidth - 8) {
      x = viewportWidth - tooltipRect.width - 8
    }
    if (y < 8) y = 8
    if (y + tooltipRect.height > viewportHeight - 8) {
      y = viewportHeight - tooltipRect.height - 8
    }

    setPosition({ x, y })
  }

  useEffect(() => {
    if (isVisible) {
      updatePosition()
    }
  }, [isVisible, side])

  useEffect(() => {
    const handleScroll = () => {
      if (isVisible) {
        updatePosition()
      }
    }

    const handleResize = () => {
      if (isVisible) {
        updatePosition()
      }
    }

    window.addEventListener("scroll", handleScroll, true)
    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("scroll", handleScroll, true)
      window.removeEventListener("resize", handleResize)
    }
  }, [isVisible])

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        className="relative"
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={cn(
            "fixed z-[9999] pointer-events-none",
            "opacity-0 translate-x-[-20px] animate-[slideInRight_200ms_ease-out_forwards]",
            side === "left" && "translate-x-[20px] animate-[slideInLeft_200ms_ease-out_forwards]",
            side === "top" && "translate-y-[20px] translate-x-0 animate-[slideInTop_200ms_ease-out_forwards]",
            side === "bottom" && "translate-y-[-20px] translate-x-0 animate-[slideInBottom_200ms_ease-out_forwards]",
            className
          )}
          style={{
            left: position.x,
            top: position.y,
          }}
        >
          <div className="bg-black text-white text-sm font-medium px-3 py-2 rounded-lg shadow-lg border border-neutral-700">
            {content}
            {/* Arrow */}
            <div
              className={cn(
                "absolute w-2 h-2 bg-black border border-neutral-700 rotate-45",
                side === "right" && "-left-1 top-1/2 -translate-y-1/2 border-r-0 border-b-0",
                side === "left" && "-right-1 top-1/2 -translate-y-1/2 border-l-0 border-t-0",
                side === "top" && "-bottom-1 left-1/2 -translate-x-1/2 border-t-0 border-r-0",
                side === "bottom" && "-top-1 left-1/2 -translate-x-1/2 border-b-0 border-l-0"
              )}
            />
          </div>
        </div>
      )}
    </>
  )
}
