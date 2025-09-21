"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, X } from "lucide-react"

interface SuccessModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  message: string
  type?: "success" | "error" | "info"
}

export function SuccessModal({ 
  isOpen, 
  onClose, 
  title, 
  message, 
  type = "success" 
}: SuccessModalProps) {
  // Auto-close after 3 seconds
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        onClose()
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case "error":
        return <X className="w-6 h-6 text-red-500" />
      case "info":
        return <CheckCircle className="w-6 h-6 text-blue-500" />
      default:
        return <CheckCircle className="w-6 h-6 text-green-500" />
    }
  }

  const getIconBg = () => {
    switch (type) {
      case "success":
        return "bg-green-100"
      case "error":
        return "bg-red-100"
      case "info":
        return "bg-blue-100"
      default:
        return "bg-green-100"
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <Card className="relative z-10 w-full max-w-md mx-4 shadow-2xl border-0 bg-card">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-full ${getIconBg()}`}>
                {getIcon()}
              </div>
              <div>
                <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                <CardDescription className="text-sm text-muted-foreground">
                  {message}
                </CardDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 hover:bg-muted"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex justify-end">
            <Button onClick={onClose} className="min-w-[80px]">
              OK
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
