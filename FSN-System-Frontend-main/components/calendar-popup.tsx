"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react"

interface CalendarPopupProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedDate: Date | null
  onDateSelect: (date: Date) => void
}

export function CalendarPopup({ open, onOpenChange, selectedDate, onDateSelect }: CalendarPopupProps) {
  const [currentMonth, setCurrentMonth] = useState(selectedDate || new Date())

  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ]

  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    const days = []
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null)
    }
    
    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day))
    }
    
    return days
  }

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const handleDateClick = (date: Date) => {
    onDateSelect(date)
    onOpenChange(false)
  }

  const isToday = (date: Date) => {
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  const isSelected = (date: Date) => {
    if (!selectedDate) return false
    return date.toDateString() === selectedDate.toDateString()
  }

  const days = getDaysInMonth(currentMonth)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="!w-[500px] !h-[600px] !max-w-none !max-h-none bg-white rounded-2xl border-0 shadow-2xl flex flex-col"
        style={{ width: '500px', height: '600px', maxWidth: 'none', maxHeight: 'none' }}
      >
        <DialogHeader className="pb-4 flex-shrink-0">
          <DialogTitle className="flex items-center gap-2 text-xl font-bold">
            <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center shadow-xl">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-gray-900">Select Date</div>
              <div className="text-xs font-normal text-gray-500 mt-0.5">Choose a date to view logs</div>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl p-6 border border-gray-100 h-full">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="ghost"
                onClick={handlePrevMonth}
                className="h-10 w-10 p-0 rounded-lg hover:bg-gray-200"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <h3 className="text-lg font-semibold text-gray-900">
                {months[currentMonth.getMonth()]} {currentMonth.getFullYear()}
              </h3>
              
              <Button
                variant="ghost"
                onClick={handleNextMonth}
                className="h-10 w-10 p-0 rounded-lg hover:bg-gray-200"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>

            {/* Days of Week Header */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {daysOfWeek.map((day) => (
                <div key={day} className="h-8 flex items-center justify-center">
                  <span className="text-xs font-semibold text-gray-500">{day}</span>
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 gap-1">
              {days.map((date, index) => (
                <div key={index} className="h-10 flex items-center justify-center">
                  {date ? (
                    <Button
                      variant="ghost"
                      onClick={() => handleDateClick(date)}
                      className={`h-8 w-8 p-0 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isSelected(date)
                          ? "bg-black text-white hover:bg-gray-800"
                          : isToday(date)
                          ? "bg-blue-100 text-blue-600 hover:bg-blue-200"
                          : "hover:bg-gray-100 text-gray-700"
                      }`}
                    >
                      {date.getDate()}
                    </Button>
                  ) : (
                    <div className="h-8 w-8" />
                  )}
                </div>
              ))}
            </div>

            {/* Quick Date Selection */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Quick Select</h4>
              <div className="grid grid-cols-3 gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleDateClick(new Date())}
                  className="h-8 text-xs rounded-lg"
                >
                  Today
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    const yesterday = new Date()
                    yesterday.setDate(yesterday.getDate() - 1)
                    handleDateClick(yesterday)
                  }}
                  className="h-8 text-xs rounded-lg"
                >
                  Yesterday
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    const weekAgo = new Date()
                    weekAgo.setDate(weekAgo.getDate() - 7)
                    handleDateClick(weekAgo)
                  }}
                  className="h-8 text-xs rounded-lg"
                >
                  Week Ago
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
