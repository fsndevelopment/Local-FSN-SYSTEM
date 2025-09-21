"use client"

import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"

interface ExportCsvButtonProps {
  data: any[]
  filename?: string
  onExport?: () => void
}

export function ExportCsvButton({ data, filename = "tracking-data", onExport }: ExportCsvButtonProps) {
  const handleExport = () => {
    if (onExport) {
      onExport()
    }

    // Convert data to CSV
    if (data.length === 0) return

    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(","),
      ...data.map((row) =>
        headers
          .map((header) => {
            const value = row[header]
            // Escape commas and quotes in CSV
            if (typeof value === "string" && (value.includes(",") || value.includes('"'))) {
              return `"${value.replace(/"/g, '""')}"`
            }
            return value
          })
          .join(","),
      ),
    ].join("\n")

    // Create and download file
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    const url = URL.createObjectURL(blob)
    link.setAttribute("href", url)
    link.setAttribute("download", `${filename}.csv`)
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <Button onClick={handleExport} className="bg-black text-white rounded-full px-5 py-2.5 hover:bg-gray-800">
      <Download className="h-4 w-4 mr-2" />
      Export CSV
    </Button>
  )
}
