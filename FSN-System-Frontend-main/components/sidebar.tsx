"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState, useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import { Home, Smartphone, Users, FileText, LogOut, BarChart3, LayoutTemplate, Play, User2, Thermometer } from "lucide-react"
import { LogoutConfirmationDialog } from "@/components/logout-confirmation-dialog"
import { usePlatform } from "@/lib/platform"
import { usePlatformColors } from "@/lib/utils/platform-colors"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Templates", href: "/templates", icon: LayoutTemplate },
  { name: "Warmup", href: "/warmup", icon: Thermometer },
  { name: "Devices", href: "/devices", icon: Smartphone },
  { name: "Accounts", href: "/accounts", icon: Users },
  { name: "Models", href: "/models", icon: User2 },
  { name: "Running", href: "/running", icon: Play },
  { name: "Tracking", href: "/tracking", icon: BarChart3 },
  { name: "Logs", href: "/logs", icon: FileText },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isExpanded, setIsExpanded] = useState(false)
  const [showLogoutDialog, setShowLogoutDialog] = useState(false)
  const [currentPlatform] = usePlatform()
  const { colors } = usePlatformColors(currentPlatform)

  return (
    <div 
      className={cn(
        "fixed left-4 top-0 bottom-4 rounded-2xl flex flex-col py-6 shadow-lg z-50 transition-all duration-300",
        isExpanded ? "w-44" : "w-16"
      )}
    >
      {/* Threads background (always present) */}
      <div 
        className="absolute inset-0 rounded-2xl"
        style={{
          background: 'linear-gradient(180deg, rgb(17, 24, 39) 0%, rgb(0, 0, 0) 100%)',
        }}
      />
      
      {/* Instagram background (fades in/out) */}
      <div 
        className="absolute inset-0 rounded-2xl"
        style={{
          background: 'linear-gradient(180deg, rgb(88, 28, 135) 0%, rgb(157, 23, 77) 50%, rgb(194, 65, 12) 100%)',
          opacity: currentPlatform === 'instagram' ? 1 : 0,
          transition: 'opacity 1500ms cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        }}
      />
      
      {/* Content wrapper */}
      <div 
        className="relative z-10 flex flex-col h-full"
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
      >
      {/* Logo */}
      <div className="w-10 h-10 rounded-full flex items-center justify-center mb-8 transition-all duration-200 transform cursor-pointer mx-auto">
        <img 
          src="/fusion.png" 
          alt="FSN Appium Farm" 
          className="w-8 h-8 object-contain"
        />
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col space-y-4 w-full px-3">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <div key={item.name} className="relative flex items-center">
              <Link
                href={item.href}
                className={cn(
                  "relative flex items-center w-full group transition-all duration-700 rounded-full",
                  !isActive && (currentPlatform === 'instagram' 
                    ? "hover:bg-purple-600/20 hover:scale-105 transform" 
                    : "hover:bg-neutral-800 hover:scale-105 transform"),
                  isActive && isExpanded ? "bg-white" : ""
                )}
              >
                <div className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-700 group relative flex-shrink-0 z-10",
                  isActive && isExpanded ? "bg-transparent text-black" : 
                  isActive ? "bg-white text-black shadow-lg" : 
                  (currentPlatform === 'instagram' 
                    ? "text-white group-hover:bg-purple-600/30" 
                    : "text-white group-hover:bg-neutral-700")
                )}>
                  <item.icon className="w-5 h-5" />
                </div>
                <div className={cn(
                  "absolute left-0 top-0 h-10 rounded-full flex items-center overflow-hidden",
                  isExpanded && isActive ? "bg-white px-3 w-auto transition-all duration-300 ease-in-out" : "w-0 bg-transparent"
                )}>
                  <span className={cn(
                    "ml-10 font-medium whitespace-nowrap",
                    isExpanded && isActive ? "text-black opacity-100 transition-all duration-500 ease-in-out delay-150" : "text-white opacity-0"
                  )}>
                    {item.name}
                  </span>
                </div>
                <div className={cn(
                  "overflow-hidden transition-all duration-300 ease-in-out",
                  isExpanded && !isActive ? "w-28 opacity-100" : "w-0 opacity-0"
                )}>
                  <span className="ml-3 font-medium whitespace-nowrap text-white group-hover:text-neutral-300 transition-colors duration-200">
                    {item.name}
                  </span>
                </div>
              </Link>
            </div>
          )
        })}
      </nav>

        {/* Logout */}
        <div className="relative flex items-center px-3">
          <button 
            onClick={() => setShowLogoutDialog(true)}
            className="relative flex items-center w-full group transition-all duration-200 rounded-full hover:bg-neutral-800 hover:scale-105 transform"
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center text-white group-hover:bg-neutral-700 transition-all duration-200 flex-shrink-0">
              <LogOut className="w-5 h-5" />
            </div>
            {isExpanded && (
              <span className="ml-3 text-white font-medium whitespace-nowrap px-3 py-1 rounded-full group-hover:text-neutral-300 transition-colors duration-200">
                Logout
              </span>
            )}
          </button>
        </div>
      </div>

      <LogoutConfirmationDialog 
        open={showLogoutDialog} 
        onOpenChange={setShowLogoutDialog} 
      />
    </div>
  )
}
