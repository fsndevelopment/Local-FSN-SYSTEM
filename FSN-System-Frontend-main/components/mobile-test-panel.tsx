"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Smartphone, Tablet, Monitor, Check, X } from "lucide-react"

interface TestResult {
  device: string
  screen: string
  status: 'pass' | 'fail' | 'pending'
  issues: string[]
}

/**
 * Mobile Testing Panel Component
 * 
 * Provides a visual testing interface to verify mobile responsiveness
 * This helps ensure the UI works across different screen sizes
 */
export function MobileTestPanel() {
  const [testResults, setTestResults] = useState<TestResult[]>([
    { device: 'Phone1', screen: '393x852', status: 'pending', issues: [] },
    { device: 'Phone2', screen: '430x932', status: 'pending', issues: [] },
    { device: 'Phone3', screen: '360x780', status: 'pending', issues: [] },
    { device: 'Phone4', screen: '1024x1366', status: 'pending', issues: [] },
  ])

  const [currentTest, setCurrentTest] = useState<string | null>(null)

  const runTest = (deviceName: string) => {
    setCurrentTest(deviceName)
    
    // Simulate testing process
    setTimeout(() => {
      setTestResults(prev => prev.map(result => {
        if (result.device === deviceName) {
          // Mock test results - in real testing, this would check actual responsiveness
          const mockIssues = Math.random() > 0.7 ? ['Navigation overlaps content', 'Buttons too small'] : []
          return {
            ...result,
            status: mockIssues.length > 0 ? 'fail' : 'pass',
            issues: mockIssues
          }
        }
        return result
      }))
      setCurrentTest(null)
    }, 2000)
  }

  const runAllTests = () => {
    testResults.forEach((result, index) => {
      setTimeout(() => runTest(result.device), index * 500)
    })
  }

  const getDeviceIcon = (device: string) => {
    if (device.includes('Phone')) return <Smartphone className="w-4 h-4" />
    return <Monitor className="w-4 h-4" />
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pass':
        return <Badge className="bg-green-100 text-green-800"><Check className="w-3 h-3 mr-1" />Pass</Badge>
      case 'fail':
        return <Badge className="bg-red-100 text-red-800"><X className="w-3 h-3 mr-1" />Fail</Badge>
      default:
        return <Badge variant="outline">Pending</Badge>
    }
  }

  const passCount = testResults.filter(r => r.status === 'pass').length
  const failCount = testResults.filter(r => r.status === 'fail').length
  const pendingCount = testResults.filter(r => r.status === 'pending').length

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center">
              <Smartphone className="w-5 h-5 mr-2" />
              Mobile Responsiveness Testing
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Test UI across different device sizes and orientations
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">{passCount} Pass</Badge>
            <Badge variant="outline">{failCount} Fail</Badge>
            <Badge variant="outline">{pendingCount} Pending</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex space-x-2">
          <Button 
            onClick={runAllTests}
            disabled={currentTest !== null}
            className="bg-black text-white hover:bg-neutral-900"
          >
            Run All Tests
          </Button>
          <Button 
            variant="outline"
            onClick={() => setTestResults(prev => prev.map(r => ({ ...r, status: 'pending' as const, issues: [] })))}
          >
            Reset Tests
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {testResults.map((result) => (
            <div 
              key={result.device}
              className={`p-4 border rounded-lg transition-all ${
                currentTest === result.device ? 'border-blue-500 bg-blue-50' : 'border-border'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getDeviceIcon(result.device)}
                  <span className="font-medium text-sm">{result.device}</span>
                </div>
                {getStatusBadge(result.status)}
              </div>
              
              <div className="text-xs text-muted-foreground mb-3">
                Screen: {result.screen}
              </div>

              {result.issues.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-red-600 mb-1">Issues Found:</p>
                  <ul className="text-xs text-red-600 space-y-1">
                    {result.issues.map((issue, index) => (
                      <li key={index}>• {issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              <Button
                onClick={() => runTest(result.device)}
                disabled={currentTest !== null}
                variant="outline"
                size="sm"
                className="w-full"
              >
                {currentTest === result.device ? 'Testing...' : 'Test Device'}
              </Button>
            </div>
          ))}
        </div>

        {/* Testing Instructions */}
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <h4 className="font-medium mb-2">Manual Testing Instructions:</h4>
          <ol className="text-sm text-muted-foreground space-y-1">
            <li>1. Open browser developer tools (F12)</li>
            <li>2. Click the device toolbar icon (Ctrl+Shift+M)</li>
            <li>3. Select each device from the dropdown</li>
            <li>4. Navigate through all pages and test interactions</li>
            <li>5. Check for layout issues, overlapping elements, and touch targets</li>
            <li>6. Test both portrait and landscape orientations</li>
          </ol>
        </div>
      </CardContent>
    </Card>
  )
}
