"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, X, AlertCircle, Info, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

export type PopupType = "success" | "error" | "warning" | "info" | "confirm"

interface UnifiedPopupProps {
  isOpen: boolean
  onClose: () => void
  onConfirm?: () => void
  title: string
  message?: string
  type?: PopupType
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  autoClose?: boolean
  duration?: number
}

export function UnifiedPopup({ 
  isOpen, 
  onClose, 
  onConfirm,
  title, 
  message, 
  type = "info",
  confirmText = "OK",
  cancelText = "Cancel",
  showCancel = false,
  autoClose = true,
  duration = 4000
}: UnifiedPopupProps) {
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure smooth animation
      setTimeout(() => setIsAnimating(true), 50)
      
      if (autoClose && type !== "confirm") {
        const timer = setTimeout(() => {
          setIsAnimating(false)
          setTimeout(onClose, 300) // Wait for animation to complete
        }, duration)
        return () => clearTimeout(timer)
      }
    }
  }, [isOpen, onClose, duration, autoClose, type])

  if (!isOpen) return null

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case "error":
        return <AlertCircle className="w-6 h-6 text-red-500" />
      case "warning":
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />
      case "info":
        return <Info className="w-6 h-6 text-blue-500" />
      case "confirm":
        return <AlertCircle className="w-6 h-6 text-orange-500" />
      default:
        return <Info className="w-6 h-6 text-blue-500" />
    }
  }

  const getIconBg = () => {
    switch (type) {
      case "success":
        return "bg-green-100"
      case "error":
        return "bg-red-100"
      case "warning":
        return "bg-yellow-100"
      case "info":
        return "bg-blue-100"
      case "confirm":
        return "bg-orange-100"
      default:
        return "bg-blue-100"
    }
  }

  const getBorderColor = () => {
    switch (type) {
      case "success":
        return "border-l-green-500"
      case "error":
        return "border-l-red-500"
      case "warning":
        return "border-l-yellow-500"
      case "info":
        return "border-l-blue-500"
      case "confirm":
        return "border-l-orange-500"
      default:
        return "border-l-blue-500"
    }
  }

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm()
    }
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={type === "confirm" ? undefined : onClose}
      />
      
      {/* Popup */}
      <Card 
        className={cn(
          "relative z-10 w-full max-w-md mx-4 shadow-2xl border-l-4 transition-all duration-300 ease-in-out",
          getBorderColor(),
          isAnimating 
            ? "scale-100 opacity-100" 
            : "scale-95 opacity-0"
        )}
      >
        <CardContent className="p-6">
          <div className="flex items-start space-x-4">
            <div className={`flex-shrink-0 p-2 rounded-full ${getIconBg()}`}>
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
              <div className="flex justify-end space-x-2">
                {showCancel && (
                  <Button 
                    variant="outline" 
                    onClick={onClose}
                    size="sm"
                  >
                    {cancelText}
                  </Button>
                )}
                <Button 
                  onClick={handleConfirm}
                  size="sm"
                  className="min-w-[80px]"
                >
                  {confirmText}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Convenience components for common use cases
export function SuccessPopup(props: Omit<UnifiedPopupProps, 'type'>) {
  return <UnifiedPopup {...props} type="success" />
}

export function ErrorPopup(props: Omit<UnifiedPopupProps, 'type'>) {
  return <UnifiedPopup {...props} type="error" />
}

export function WarningPopup(props: Omit<UnifiedPopupProps, 'type'>) {
  return <UnifiedPopup {...props} type="warning" />
}

export function InfoPopup(props: Omit<UnifiedPopupProps, 'type'>) {
  return <UnifiedPopup {...props} type="info" />
}

export function ConfirmPopup(props: Omit<UnifiedPopupProps, 'type' | 'showCancel'>) {
  return <UnifiedPopup {...props} type="confirm" showCancel={true} autoClose={false} />
}
