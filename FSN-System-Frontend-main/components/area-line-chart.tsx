"use client"

import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis, Tooltip, ReferenceDot } from "recharts"

const data = [
  { name: "Mon", hours: 0, label: "0h" },
  { name: "Tue", hours: 1.5, label: "1.5h" },
  { name: "Wed", hours: 2.5, label: "2.5h" },
  { name: "Thu", hours: 1, label: "1h" },
  { name: "Fri", hours: 3, label: "3h" },
  { name: "Sat", hours: 2, label: "2h" },
  { name: "Sun", hours: 4, label: "4h" },
]

export function AreaLineChart() {
  return (
    <div className="h-32 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0a0a0a" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#0a0a0a" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} />
          <YAxis hide />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return <div className="bg-black text-white px-2 py-1 rounded text-xs">{payload[0].payload.label}</div>
              }
              return null
            }}
          />
          <Area type="monotone" dataKey="hours" stroke="#0a0a0a" strokeWidth={2} fill="url(#colorHours)" />
          {data.map((entry, index) => (
            <ReferenceDot
              key={index}
              x={entry.name}
              y={entry.hours}
              r={3}
              fill="#0a0a0a"
              stroke="#ffffff"
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
