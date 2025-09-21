"use client"

import { useEffect } from 'react'

export function RemoveNextJSLogo() {
  useEffect(() => {
    // Function to remove Next.js logo
    const removeNextJSLogo = () => {
      // Remove by data attribute
      const elements = document.querySelectorAll('[data-next-mark-loading]')
      elements.forEach(el => {
        el.remove()
      })

      // Remove by SVG attributes
      const svgs = document.querySelectorAll('svg[width="40"][height="40"]')
      svgs.forEach(svg => {
        if (svg.getAttribute('viewBox') === '0 0 40 40') {
          svg.remove()
        }
      })

      // Remove any element containing Next.js gradients
      const gradientElements = document.querySelectorAll('[id*="next_logo_paint"]')
      gradientElements.forEach(el => {
        el.parentElement?.remove()
      })

      // Remove circular buttons with SVG
      const buttons = document.querySelectorAll('button, div')
      buttons.forEach(button => {
        const svg = button.querySelector('svg[width="40"][height="40"]')
        if (svg) {
          button.remove()
        }
      })
    }

    // Run immediately
    removeNextJSLogo()

    // Run on DOM changes - wait for body to be available
    const observer = new MutationObserver(removeNextJSLogo)
    
    const startObserver = () => {
      if (document.body && document.body instanceof Node) {
        observer.observe(document.body, {
          childList: true,
          subtree: true
        })
        return true
      }
      return false
    }
    
    // Try to start immediately
    if (!startObserver()) {
      // If body not ready, wait for it
      const checkBody = () => {
        if (startObserver()) {
          return
        }
        // Keep checking every 10ms
        setTimeout(checkBody, 10)
      }
      checkBody()
    }

    // Run periodically as backup
    const interval = setInterval(removeNextJSLogo, 100)

    return () => {
      observer.disconnect()
      clearInterval(interval)
    }
  }, [])

  return null
}


