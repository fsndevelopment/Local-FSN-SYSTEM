"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

interface LineCompareProps {
  data: Array<{
    date: string
    [key: string]: string | number
  }>
  accounts: Array<{
    id: string
    username: string
    color: string
  }>
}

export function LineCompare({ data, accounts }: LineCompareProps) {
  const colors = ["#000", "#333", "#666", "#999", "#ccc"]

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            stroke="#666"
            fontSize={12}
            tickFormatter={(value) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          />
          <YAxis stroke="#666" fontSize={12} tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            }}
            labelFormatter={(label) =>
              new Date(label).toLocaleDateString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
              })
            }
          />
          <Legend />
          {accounts.map((account, index) => (
            <Line
              key={account.id}
              type="monotone"
              dataKey={account.id}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ fill: colors[index % colors.length], strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, fill: colors[index % colors.length] }}
              name={account.username}
              strokeDasharray={index > 0 ? "5,5" : "0"}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
