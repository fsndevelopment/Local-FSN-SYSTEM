"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Smartphone, User, Clock, Play, AlertCircle } from "lucide-react"
import { Template, Device, Account } from "@/lib/types"

interface TemplateExecutionDialogProps {
  template: Template | null
  devices: Device[]
  accounts: Account[]
  isOpen: boolean
  onClose: () => void
  onExecute: (request: TemplateExecutionRequest) => void
}

interface TemplateExecutionRequest {
  device_id: number
  account_ids: number[]
  execution_mode: string
  start_delay: number
}

export function TemplateExecutionDialog({
  template,
  devices,
  accounts,
  isOpen,
  onClose,
  onExecute
}: TemplateExecutionDialogProps) {
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("")
  const [selectedAccountIds, setSelectedAccountIds] = useState<number[]>([])
  const [executionMode, setExecutionMode] = useState<string>("normal")
  const [startDelay, setStartDelay] = useState<number>(0)
  const [isExecuting, setIsExecuting] = useState(false)

  // Filter accounts by selected device
  const availableAccounts = selectedDeviceId 
    ? accounts.filter(account => account.device_id?.toString() === selectedDeviceId)
    : []

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setSelectedDeviceId("")
      setSelectedAccountIds([])
      setExecutionMode("normal")
      setStartDelay(0)
      setIsExecuting(false)
    }
  }, [isOpen])

  const handleAccountToggle = (accountId: number, checked: boolean) => {
    if (checked) {
      setSelectedAccountIds(prev => [...prev, accountId])
    } else {
      setSelectedAccountIds(prev => prev.filter(id => id !== accountId))
    }
  }

  const handleExecute = async () => {
    if (!selectedDeviceId || selectedAccountIds.length === 0) {
      return
    }

    setIsExecuting(true)
    
    const request: TemplateExecutionRequest = {
      device_id: parseInt(selectedDeviceId),
      account_ids: selectedAccountIds,
      execution_mode: executionMode,
      start_delay: startDelay
    }

    try {
      await onExecute(request)
      onClose()
    } catch (error) {
      console.error('Failed to execute template:', error)
    } finally {
      setIsExecuting(false)
    }
  }

  const canExecute = selectedDeviceId && selectedAccountIds.length > 0 && !isExecuting

  if (!template) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Play className="w-5 h-5" />
            Execute Template: {template.name}
          </DialogTitle>
          <DialogDescription>
            Configure and execute this template on a specific device with selected accounts
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Template Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Template Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label className="text-muted-foreground">Platform</Label>
                  <p className="font-medium capitalize">{template.platform}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Posts per Day</Label>
                  <p className="font-medium">{template.posts_per_day || 0}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Likes per Day</Label>
                  <p className="font-medium">{template.likes_per_day || 0}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Follows per Day</Label>
                  <p className="font-medium">{template.follows_per_day || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Device Selection */}
          <div className="space-y-2">
            <Label htmlFor="device">Select Device</Label>
            <Select value={selectedDeviceId} onValueChange={setSelectedDeviceId}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a device to execute on">
                  {selectedDeviceId && (() => {
                    const device = devices.find(d => d.id.toString() === selectedDeviceId)
                    return device ? (
                      <div className="flex items-center gap-2">
                        <Smartphone className="w-4 h-4" />
                        <span>{device.name}</span>
                        <Badge variant="outline">{device.status}</Badge>
                      </div>
                    ) : null
                  })()}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {devices.map(device => (
                  <SelectItem key={device.id} value={device.id.toString()}>
                    <div className="flex items-center gap-2">
                      <Smartphone className="w-4 h-4" />
                      <span>{device.name}</span>
                      <Badge variant="outline" className="ml-2">{device.status}</Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Account Selection */}
          {selectedDeviceId && (
            <div className="space-y-2">
              <Label>Select Accounts</Label>
              <div className="max-h-40 overflow-y-auto border rounded-md p-3 space-y-2">
                {availableAccounts.length > 0 ? (
                  availableAccounts.map(account => (
                    <div key={account.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={`account-${account.id}`}
                        checked={selectedAccountIds.includes(account.id)}
                        onCheckedChange={(checked) => 
                          handleAccountToggle(account.id, checked as boolean)
                        }
                      />
                      <Label 
                        htmlFor={`account-${account.id}`}
                        className="flex items-center gap-2 flex-1 cursor-pointer"
                      >
                        <User className="w-4 h-4" />
                        <span>{account.username || account.email}</span>
                        <Badge variant="secondary" className="text-xs">
                          {account.platform}
                        </Badge>
                      </Label>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                    <p>No accounts assigned to this device</p>
                    <p className="text-sm">Please assign accounts to this device first</p>
                  </div>
                )}
              </div>
              {selectedAccountIds.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  {selectedAccountIds.length} account(s) selected
                </p>
              )}
            </div>
          )}

          {/* Execution Configuration */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="execution-mode">Execution Mode</Label>
              <Select value={executionMode} onValueChange={setExecutionMode}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="safe">Safe (Slower)</SelectItem>
                  <SelectItem value="aggressive">Aggressive (Faster)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="start-delay">Start Delay (seconds)</Label>
              <Input
                id="start-delay"
                type="number"
                min="0"
                value={startDelay}
                onChange={(e) => setStartDelay(parseInt(e.target.value) || 0)}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose} disabled={isExecuting}>
              Cancel
            </Button>
            <Button 
              onClick={handleExecute} 
              disabled={!canExecute}
              className="min-w-[120px]"
            >
              {isExecuting ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Execute Template
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
