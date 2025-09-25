"use client"

import { usePlatform } from "@/lib/platform"
import { useState, useEffect } from "react"
import Image from "next/image"

export function PlatformSwitch() {
  const [platform, setPlatform] = usePlatform()
  const [isAnimating, setIsAnimating] = useState(false)

  const platforms = [
    { id: 'instagram' as const, icon: '/instagram.png' },
    { id: 'threads' as const, icon: '/threads.png' }
  ]

  // If platform is 'all', default to 'instagram'
  const currentPlatform = platform === 'all' ? 'instagram' : platform
  const currentIndex = platforms.findIndex(p => p.id === currentPlatform)

  const handlePlatformSwitch = (newPlatform: 'instagram' | 'threads') => {
    if (newPlatform === currentPlatform) return
    
    setIsAnimating(true)
    setPlatform(newPlatform)
    
    // Reset animation after transition
    setTimeout(() => {
      setIsAnimating(false)
    }, 300)
  }

  return (
    <div className="relative bg-white/10 backdrop-blur-sm rounded-full px-3 py-1 border border-white/20 flex items-center">
      {/* Icons section with longer background */}
      <div className="relative bg-white/10 rounded-full p-1 mr-3">
        {/* Sliding background - covers individual icon */}
        <div 
          className={`absolute top-1 w-10 h-10 bg-white rounded-full shadow-md transition-all duration-300 ease-in-out ${
            isAnimating ? 'scale-95' : 'scale-100'
          }`}
          style={{
            left: currentIndex === 0 ? '4px' : '44px',
            transform: isAnimating ? 'scale(0.95)' : 'scale(1)'
          }}
        />
        
        {/* Platform buttons */}
        <div className="relative flex">
          {platforms.map((p, index) => (
            <button
              key={p.id}
              onClick={() => handlePlatformSwitch(p.id)}
              className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 ${
                currentPlatform === p.id
                  ? "text-black"
                  : "text-white hover:text-gray-200"
              }`}
            >
              <Image
                src={p.icon}
                alt={p.id}
                width={20}
                height={20}
                className={`transition-all duration-200 ${
                  currentPlatform === p.id ? 'opacity-100' : 'opacity-70 hover:opacity-90'
                }`}
              />
            </button>
          ))}
        </div>
      </div>
      
      {/* Dividing line */}
      <div className="w-px h-6 bg-white/30 mr-3"></div>
      
      {/* Connected status */}
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
        <span className="text-white text-xs font-medium">Connected</span>
      </div>
    </div>
  )
}
