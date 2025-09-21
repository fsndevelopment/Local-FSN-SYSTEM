"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle, X, AlertCircle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

interface SuccessToastProps {
  isVisible: boolean
  onClose: () => void
  title: string
  message?: string
  type?: "success" | "error" | "info"
  duration?: number
}

export function SuccessToast({ 
  isVisible, 
  onClose, 
  title, 
  message, 
  type = "success",
  duration = 4000
}: SuccessToastProps) {
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (isVisible) {
      // Small delay to ensure smooth animation
      setTimeout(() => setIsAnimating(true), 50)
      const timer = setTimeout(() => {
        setIsAnimating(false)
        setTimeout(onClose, 300) // Wait for animation to complete
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [isVisible, onClose, duration])

  if (!isVisible) return null

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-500" />
      case "info":
        return <Info className="w-5 h-5 text-blue-500" />
      default:
        return <CheckCircle className="w-5 h-5 text-green-500" />
    }
  }

  const getBorderColor = () => {
    switch (type) {
      case "success":
        return "border-l-green-500"
      case "error":
        return "border-l-red-500"
      case "info":
        return "border-l-blue-500"
      default:
        return "border-l-green-500"
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Toast */}
      <Card 
        className={cn(
          "relative z-10 w-80 shadow-2xl border-l-4 transition-all duration-300 ease-in-out",
          getBorderColor(),
          isAnimating 
            ? "scale-100 opacity-100" 
            : "scale-95 opacity-0"
        )}
      >
        <CardContent className="p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 mt-1">
              {getIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-lg font-semibold text-foreground mb-2">
                {title}
              </h4>
              {message && (
                <p className="text-sm text-muted-foreground mb-4">
                  {message}
                </p>
              )}
              <div className="flex justify-end">
                <Button 
                  onClick={onClose} 
                  className="min-w-[80px]"
                  size="sm"
                >
                  OK
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
