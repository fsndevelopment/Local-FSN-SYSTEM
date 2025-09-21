"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Calendar, Search } from "lucide-react"

interface TrackingFiltersProps {
  onFiltersChange: (filters: any) => void
}

export function TrackingFilters({ onFiltersChange }: TrackingFiltersProps) {
  const [dateRange, setDateRange] = useState("7")
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([])
  const [phase, setPhase] = useState("all")
  const [status, setStatus] = useState("all")
  const [useAccountTz, setUseAccountTz] = useState(false)
  const [comparePrevious, setComparePrevious] = useState(false)
  const [accountSearch, setAccountSearch] = useState("")

  const handleApply = () => {
    onFiltersChange({
      dateRange,
      selectedModels,
      selectedAccounts,
      phase,
      status,
      useAccountTz,
      comparePrevious,
    })
  }

  const handleReset = () => {
    setDateRange("7")
    setSelectedModels([])
    setSelectedAccounts([])
    setPhase("all")
    setStatus("all")
    setUseAccountTz(false)
    setComparePrevious(false)
    setAccountSearch("")
    onFiltersChange({
      dateRange: "7",
      selectedModels: [],
      selectedAccounts: [],
      phase: "all",
      status: "all",
      useAccountTz: false,
      comparePrevious: false,
    })
  }

  return (
    <Card className="sticky top-0 z-10 rounded-2xl shadow-sm border-0 bg-white/95 backdrop-blur-sm">
      <div className="p-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Date Range */}
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-500" />
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-32 rounded-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">7 days</SelectItem>
                <SelectItem value="14">14 days</SelectItem>
                <SelectItem value="30">30 days</SelectItem>
                <SelectItem value="90">90 days</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Model Filter */}
          <div className="flex items-center gap-2">
            <Label className="text-sm text-gray-600">Model:</Label>
            <Select>
              <SelectTrigger className="w-40 rounded-full">
                <SelectValue placeholder="All models" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All models</SelectItem>
                <SelectItem value="iphone-15">iPhone 15</SelectItem>
                <SelectItem value="iphone-14">iPhone 14</SelectItem>
                <SelectItem value="iphone-13">iPhone 13</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Account Search */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search accounts..."
                value={accountSearch}
                onChange={(e) => setAccountSearch(e.target.value)}
                className="pl-10 w-48 rounded-full"
              />
            </div>
          </div>

          {/* Phase Filter */}
          <div className="flex items-center gap-2">
            <Label className="text-sm text-gray-600">Phase:</Label>
            <Select value={phase} onValueChange={setPhase}>
              <SelectTrigger className="w-32 rounded-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="warmup">Warmup</SelectItem>
                <SelectItem value="posting">Posting</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Label className="text-sm text-gray-600">Status:</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-32 rounded-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Toggles */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                checked={useAccountTz}
                onCheckedChange={setUseAccountTz}
                className="data-[state=checked]:bg-black"
              />
              <Label className="text-sm text-gray-600">Account TZ</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={comparePrevious}
                onCheckedChange={setComparePrevious}
                className="data-[state=checked]:bg-black"
              />
              <Label className="text-sm text-gray-600">Compare vs previous</Label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 ml-auto">
            <Button variant="ghost" onClick={handleReset} className="rounded-full px-5 py-2.5">
              Reset
            </Button>
            <Button onClick={handleApply} className="bg-black text-white rounded-full px-5 py-2.5 hover:bg-gray-800">
              Apply
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
