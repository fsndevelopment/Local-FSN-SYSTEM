"use client"

import { motion } from "framer-motion"

interface LoadingAnimationProps {
  text?: string
  size?: "sm" | "md" | "lg"
  variant?: "spinner" | "dots" | "pulse" | "wave"
}

export function LoadingAnimation({ 
  text = "Loading...", 
  size = "md", 
  variant = "wave" 
}: LoadingAnimationProps) {
  
  const sizeClasses = {
    sm: { container: "w-8 h-8", icon: "w-4 h-4", text: "text-sm" },
    md: { container: "w-12 h-12", icon: "w-6 h-6", text: "text-base" },
    lg: { container: "w-16 h-16", icon: "w-8 h-8", text: "text-lg" }
  }

  const currentSize = sizeClasses[size]

  const renderSpinner = () => (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className={`${currentSize.container} border-4 border-gray-200 border-t-black rounded-full`}
    />
  )

  const renderDots = () => (
    <div className="flex items-center space-x-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{ scale: [1, 1.2, 1], opacity: [0.4, 1, 0.4] }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.2,
            ease: "easeInOut"
          }}
          className="w-2 h-2 bg-black rounded-full"
        />
      ))}
    </div>
  )

  const renderPulse = () => (
    <motion.div
      animate={{ scale: [1, 1.1, 1], opacity: [0.7, 1, 0.7] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      className={`${currentSize.container} bg-black rounded-2xl flex items-center justify-center`}
    >
      <img 
        src="/fusion.png" 
        alt="FSN" 
        className={`${currentSize.icon} object-contain opacity-80`}
      />
    </motion.div>
  )

  const renderWave = () => (
    <div className="flex items-center space-x-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <motion.div
          key={i}
          animate={{ 
            scaleY: [1, 2, 1],
            opacity: [0.3, 1, 0.3]
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.1,
            ease: "easeInOut"
          }}
          className="w-1 h-6 bg-black rounded-full"
        />
      ))}
    </div>
  )

  const renderAnimation = () => {
    switch (variant) {
      case "spinner":
        return renderSpinner()
      case "dots":
        return renderDots()
      case "pulse":
        return renderPulse()
      case "wave":
      default:
        return renderWave()
    }
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        {renderAnimation()}
      </motion.div>
      
      {text && (
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className={`${currentSize.text} font-medium text-gray-600`}
        >
          {text}
        </motion.p>
      )}
    </div>
  )
}

// Full screen loading overlay
export function FullScreenLoading({ text = "Loading..." }: { text?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center"
    >
      <div className="text-center space-y-6">
        {/* Animated Logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="relative"
        >
          <div className="w-20 h-20 bg-black rounded-3xl flex items-center justify-center shadow-2xl mx-auto">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            >
              <img 
                src="/fusion.png" 
                alt="FSN" 
                className="w-12 h-12 object-contain"
              />
            </motion.div>
          </div>
          
          {/* Animated Ring */}
          <motion.div
            animate={{ 
              scale: [1, 1.3, 1], 
              opacity: [0.3, 0.1, 0.3],
              rotate: [0, 180, 360]
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inset-0 w-20 h-20 border-2 border-black rounded-3xl mx-auto"
          />
        </motion.div>

        {/* Loading Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="space-y-3"
        >
          <h3 className="text-2xl font-bold text-gray-900">{text}</h3>
          
          {/* Wave Animation */}
          <div className="flex items-center justify-center space-x-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                animate={{ 
                  scaleY: [1, 2.5, 1],
                  opacity: [0.4, 1, 0.4]
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: "easeInOut"
                }}
                className="w-1 h-8 bg-black rounded-full"
              />
            ))}
          </div>
        </motion.div>

        {/* Progress Indicator */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: "100%" }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="w-64 h-1 bg-gray-200 rounded-full mx-auto overflow-hidden"
        >
          <motion.div
            animate={{ x: ["-100%", "100%"] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            className="h-full w-1/2 bg-gradient-to-r from-transparent via-black to-transparent rounded-full"
          />
        </motion.div>
      </div>
    </motion.div>
  )
}
