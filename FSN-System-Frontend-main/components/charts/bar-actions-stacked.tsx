"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

interface BarActionsStackedProps {
  data: Array<{
    date: string
    likes: number | null
    follows: number | null
    comments: number | null
    stories: number | null
    posts: number | null
  }>
}

export function BarActionsStacked({ data }: BarActionsStackedProps) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            stroke="#666"
            fontSize={12}
            tickFormatter={(value) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          />
          <YAxis stroke="#666" fontSize={12} />
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
          <Bar dataKey="likes" stackId="a" fill="#000" name="Likes" />
          <Bar dataKey="follows" stackId="a" fill="#333" name="Follows" />
          <Bar dataKey="comments" stackId="a" fill="#666" name="Comments" />
          <Bar dataKey="stories" stackId="a" fill="#999" name="Stories" />
          <Bar dataKey="posts" stackId="a" fill="#ccc" name="Posts" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
