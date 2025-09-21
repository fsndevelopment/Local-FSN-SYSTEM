"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

interface Account {
  id: string
  username: string
  role: string
  status: string
}

interface Schedule {
  id: string
  name: string
}

interface AssignPlanModalProps {
  isOpen: boolean
  onClose: () => void
  accounts: Account[]
  schedules: Schedule[]
  onAssign: (accountIds: string[], scheduleId: string) => void
}

export function AssignPlanModal({ isOpen, onClose, accounts, schedules, onAssign }: AssignPlanModalProps) {
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([])
  const [selectedSchedule, setSelectedSchedule] = useState<string>("")

  const handleAccountToggle = (accountId: string) => {
    setSelectedAccounts((prev) =>
      prev.includes(accountId) ? prev.filter((id) => id !== accountId) : [...prev, accountId],
    )
  }

  const handleAssign = () => {
    if (selectedAccounts.length > 0 && selectedSchedule) {
      onAssign(selectedAccounts, selectedSchedule)
      setSelectedAccounts([])
      setSelectedSchedule("")
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-2xl shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Assign Schedule</h2>
          <Button variant="outline" size="icon" onClick={onClose} className="rounded-full bg-transparent">
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="font-medium mb-4">Select Accounts</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center space-x-3 p-3 bg-muted/30 rounded-xl hover:bg-muted/50 transition-colors"
                >
                  <Checkbox
                    checked={selectedAccounts.includes(account.id)}
                    onCheckedChange={() => handleAccountToggle(account.id)}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{account.username}</div>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {account.role}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {account.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-medium mb-4">Select Schedule</h3>
            <Select value={selectedSchedule} onValueChange={setSelectedSchedule}>
              <SelectTrigger className="rounded-full">
                <SelectValue placeholder="Choose a schedule..." />
              </SelectTrigger>
              <SelectContent>
                {schedules.map((schedule) => (
                  <SelectItem key={schedule.id} value={schedule.id}>
                    {schedule.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex space-x-3 pt-4">
            <Button variant="outline" onClick={onClose} className="flex-1 rounded-full bg-transparent">
              Cancel
            </Button>
            <Button
              onClick={handleAssign}
              disabled={selectedAccounts.length === 0 || !selectedSchedule}
              className="flex-1 bg-black text-white hover:bg-neutral-900 rounded-full disabled:opacity-50"
            >
              Assign to {selectedAccounts.length} account{selectedAccounts.length !== 1 ? "s" : ""}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
