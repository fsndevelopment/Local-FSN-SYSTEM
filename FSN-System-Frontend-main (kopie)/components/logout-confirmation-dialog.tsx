"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LogOut, AlertTriangle } from "lucide-react"
import { useLicense } from "@/lib/providers/license-provider"

interface LogoutConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function LogoutConfirmationDialog({ open, onOpenChange }: LogoutConfirmationDialogProps) {
  const { clearLicense } = useLicense()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await clearLicense()
      onOpenChange(false)
    } catch (error) {
      console.error('Error clearing license:', error)
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <DialogTitle>Clear License & Logout</DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                This will clear your current license and log you out of the system.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        
        <div className="py-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-yellow-800">Are you sure you want to logout?</p>
                <p className="text-yellow-700 mt-1">
                  This action will:
                </p>
                <ul className="list-disc list-inside text-yellow-700 mt-2 space-y-1">
                  <li>Clear your current license from this device</li>
                  <li>Remove all locally stored data</li>
                  <li>Log you out of the system</li>
                </ul>
                <p className="text-yellow-700 mt-2">
                  You'll need to enter your license key again to access the system.
                </p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoggingOut}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="w-full sm:w-auto"
          >
            {isLoggingOut ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Logging out...
              </>
            ) : (
              <>
                <LogOut className="w-4 h-4 mr-2" />
                Yes, Logout
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
