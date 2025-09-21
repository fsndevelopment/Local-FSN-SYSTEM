"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { SuccessPopup, ErrorPopup, WarningPopup, InfoPopup, ConfirmPopup } from "@/components/ui/unified-popup"

export default function TestPopupPage() {
  const [showSuccess, setShowSuccess] = useState(false)
  const [showError, setShowError] = useState(false)
  const [showWarning, setShowWarning] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  return (
    <div className="p-8 space-y-4">
      <h1 className="text-2xl font-bold">Popup Test Page</h1>
      
      <div className="space-x-2">
        <Button onClick={() => setShowSuccess(true)}>Test Success Popup</Button>
        <Button onClick={() => setShowError(true)} variant="destructive">Test Error Popup</Button>
        <Button onClick={() => setShowWarning(true)} variant="outline">Test Warning Popup</Button>
        <Button onClick={() => setShowInfo(true)} variant="secondary">Test Info Popup</Button>
        <Button onClick={() => setShowConfirm(true)} variant="outline">Test Confirm Popup</Button>
      </div>

      {/* Success Popup */}
      <SuccessPopup
        isOpen={showSuccess}
        onClose={() => setShowSuccess(false)}
        title="Success!"
        message="This is a success popup test."
        autoClose={true}
        duration={3000}
      />

      {/* Error Popup */}
      <ErrorPopup
        isOpen={showError}
        onClose={() => setShowError(false)}
        title="Error!"
        message="This is an error popup test."
        autoClose={true}
        duration={3000}
      />

      {/* Warning Popup */}
      <WarningPopup
        isOpen={showWarning}
        onClose={() => setShowWarning(false)}
        title="Warning!"
        message="This is a warning popup test."
        autoClose={true}
        duration={3000}
      />

      {/* Info Popup */}
      <InfoPopup
        isOpen={showInfo}
        onClose={() => setShowInfo(false)}
        title="Info"
        message="This is an info popup test."
        autoClose={true}
        duration={3000}
      />

      {/* Confirm Popup */}
      <ConfirmPopup
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={() => {
          alert("Confirmed!")
          setShowConfirm(false)
        }}
        title="Confirm Action"
        message="Are you sure you want to proceed?"
        confirmText="Yes"
        cancelText="No"
      />
    </div>
  )
}
