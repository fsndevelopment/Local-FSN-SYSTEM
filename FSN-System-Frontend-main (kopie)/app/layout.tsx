import type React from "react"
import type { Metadata } from "next"
import { Suspense } from "react"
import { QueryProvider } from "@/lib/providers/query-provider"
import { WebSocketProvider } from "@/lib/providers/websocket-provider"
import { LicenseProvider } from "@/lib/providers/license-provider"
import { LicenseGuard } from "@/components/license-guard"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/error-boundary"
import { RemoveNextJSLogo } from "@/app/remove-nextjs-logo"
import "./globals.css"

export const metadata: Metadata = {
  title: "FSN Appium Farm",
  description: "Appium device farm control panel",
  generator: "v0.app",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/fusion.png", type: "image/png" }
    ],
    shortcut: "/favicon.ico",
    apple: "/fusion.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/fusion.png" type="image/png" />
        <link rel="apple-touch-icon" href="/fusion.png" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Immediate removal script
              (function() {
                function removeNextJSLogo() {
                  // Remove by data attribute
                  document.querySelectorAll('[data-next-mark-loading]').forEach(el => el.remove());
                  
                  // Remove SVG elements
                  document.querySelectorAll('svg[width="40"][height="40"]').forEach(svg => {
                    if (svg.getAttribute('viewBox') === '0 0 40 40') {
                      svg.remove();
                    }
                  });
                  
                  // Remove parent containers
                  document.querySelectorAll('button, div, span').forEach(el => {
                    const svg = el.querySelector('svg[width="40"][height="40"]');
                    if (svg) {
                      el.remove();
                    }
                  });
                }
                
                // Run immediately
                removeNextJSLogo();
                
                // Run when DOM is ready
                if (document.readyState === 'loading') {
                  document.addEventListener('DOMContentLoaded', removeNextJSLogo);
                }
                
                // Run periodically
                setInterval(removeNextJSLogo, 50);
                
                // Watch for new elements
                const observer = new MutationObserver(removeNextJSLogo);
                if (document.body && document.body instanceof Node) {
                  observer.observe(document.body, { childList: true, subtree: true });
                }
              })();
            `,
          }}
        />
      </head>
      <body className="font-sans antialiased">
        <ErrorBoundary>
          <LicenseProvider>
            <LicenseGuard>
              <QueryProvider>
                <WebSocketProvider>
                  <Suspense fallback={null}>{children}</Suspense>
                  <Toaster />
                  <RemoveNextJSLogo />
                </WebSocketProvider>
              </QueryProvider>
            </LicenseGuard>
          </LicenseProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
