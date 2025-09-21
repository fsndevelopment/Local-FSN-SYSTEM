"use client"

import type React from "react"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { PhaseBadge } from "@/components/phase-badge"
import { StatusBadge } from "@/components/status-badge"
import { ChevronUp, ChevronDown } from "lucide-react"

interface TopGainer {
  id: string
  account: string
  startFollowers: number | null
  endFollowers: number | null
  deltaFollowers: number | null
  avgViews: number | null
  phase: string
  phaseDay: number
  status: "active" | "paused" | "error"
}

interface TopGainersTableProps {
  data: TopGainer[]
}

type SortField = "account" | "startFollowers" | "endFollowers" | "deltaFollowers" | "avgViews"
type SortDirection = "asc" | "desc"

export function TopGainersTable({ data }: TopGainersTableProps) {
  const [sortField, setSortField] = useState<SortField>("deltaFollowers")
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc")

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("desc")
    }
  }

  const sortedData = [...data].sort((a, b) => {
    const aValue = a[sortField]
    const bValue = b[sortField]

    // Handle null values - put them at the end
    if (aValue === null && bValue === null) return 0
    if (aValue === null) return 1
    if (bValue === null) return -1

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortDirection === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue)
    }

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDirection === "asc" ? aValue - bValue : bValue - aValue
    }

    return 0
  })

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <Button
      variant="ghost"
      onClick={() => handleSort(field)}
      className="h-auto p-0 font-medium text-gray-900 hover:text-black"
    >
      <span className="flex items-center gap-1">
        {children}
        {sortField === field &&
          (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
      </span>
    </Button>
  )

  return (
    <Card className="rounded-2xl shadow-sm border-0 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Top Gainers</h3>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-2">
                <SortButton field="account">Account</SortButton>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="startFollowers">Start</SortButton>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="endFollowers">End</SortButton>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="deltaFollowers">Δ Followers</SortButton>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="avgViews">7d Avg Views</SortButton>
              </th>
              <th className="text-left py-3 px-2">Phase</th>
              <th className="text-left py-3 px-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((item) => (
              <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-25">
                <td className="py-3 px-2">
                  <div className="font-medium text-gray-900">{item.account}</div>
                </td>
                <td className="py-3 px-2 text-right text-gray-600">{item.startFollowers?.toLocaleString() || "NA"}</td>
                <td className="py-3 px-2 text-right text-gray-900 font-medium">{item.endFollowers?.toLocaleString() || "NA"}</td>
                <td className="py-3 px-2 text-right">
                  <span className={`font-medium ${item.deltaFollowers && item.deltaFollowers > 0 ? "text-green-600" : "text-red-600"}`}>
                    {item.deltaFollowers ? (item.deltaFollowers > 0 ? "+" : "") : ""}
                    {item.deltaFollowers?.toLocaleString() || "NA"}
                  </span>
                </td>
                <td className="py-3 px-2 text-right text-gray-600">{item.avgViews?.toLocaleString() || "NA"}</td>
                <td className="py-3 px-2">
                  <PhaseBadge account={item} />
                </td>
                <td className="py-3 px-2">
                  <StatusBadge status={item.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
