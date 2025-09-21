"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  useAvailableAccounts, 
  useLaunchApp, 
  useOpenSwitcher, 
  useSwitchAccount 
} from "@/lib/hooks/use-account-switching"
import { 
  Smartphone, 
  Users, 
  RefreshCw, 
  Play, 
  ChevronDown, 
  CheckCircle, 
  AlertCircle,
  Loader2
} from "lucide-react"
import type { Device } from "@/lib/api/devices"

interface AccountSwitcherProps {
  device: Device
  platform: 'instagram' | 'threads'
}

export function AccountSwitcher({ device, platform }: AccountSwitcherProps) {
  const [selectedAccount, setSelectedAccount] = useState<string>("")
  const [isSwitching, setIsSwitching] = useState(false)

  // Queries and mutations
  const { 
    data: accountsData, 
    isLoading: accountsLoading, 
    error: accountsError, 
    refetch: refetchAccounts 
  } = useAvailableAccounts(device.udid, platform, false) // Disabled by default

  const launchAppMutation = useLaunchApp()
  const openSwitcherMutation = useOpenSwitcher()
  const switchAccountMutation = useSwitchAccount()

  const accounts = accountsData?.data?.accounts || []
  const isLoading = accountsLoading || launchAppMutation.isPending || openSwitcherMutation.isPending || switchAccountMutation.isPending

  const handleLaunchApp = async () => {
    try {
      await launchAppMutation.mutateAsync({
        device_udid: device.udid,
        platform
      })
      // After launching, get available accounts
      refetchAccounts()
    } catch (error) {
      console.error('Failed to launch app:', error)
    }
  }

  const handleOpenSwitcher = async () => {
    try {
      await openSwitcherMutation.mutateAsync({
        device_udid: device.udid,
        platform
      })
      // After opening switcher, get available accounts
      refetchAccounts()
    } catch (error) {
      console.error('Failed to open switcher:', error)
    }
  }

  const handleSwitchAccount = async () => {
    if (!selectedAccount) return

    setIsSwitching(true)
    try {
      await switchAccountMutation.mutateAsync({
        device_udid: device.udid,
        platform,
        target_username: selectedAccount
      })
      setSelectedAccount("")
    } catch (error) {
      console.error('Failed to switch account:', error)
    } finally {
      setIsSwitching(false)
    }
  }

  const handleCompleteFlow = async () => {
    if (!selectedAccount) return

    setIsSwitching(true)
    try {
      // Complete flow: launch -> open switcher -> switch account
      await launchAppMutation.mutateAsync({
        device_udid: device.udid,
        platform
      })
      
      await openSwitcherMutation.mutateAsync({
        device_udid: device.udid,
        platform
      })
      
      await switchAccountMutation.mutateAsync({
        device_udid: device.udid,
        platform,
        target_username: selectedAccount
      })
      
      setSelectedAccount("")
    } catch (error) {
      console.error('Failed to complete account switch flow:', error)
    } finally {
      setIsSwitching(false)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Account Switching - {platform.charAt(0).toUpperCase() + platform.slice(1)}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Device Info */}
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <Smartphone className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium">{device.name}</span>
          <Badge variant="outline">{device.udid}</Badge>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 flex-wrap">
          <Button
            onClick={handleLaunchApp}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            {launchAppMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            Launch App
          </Button>

          <Button
            onClick={handleOpenSwitcher}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            {openSwitcherMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <ChevronDown className="w-4 h-4 mr-2" />
            )}
            Open Switcher
          </Button>

          <Button
            onClick={() => refetchAccounts()}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Available Accounts */}
        {accountsError && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Failed to load accounts: {accountsError.message}
            </AlertDescription>
          </Alert>
        )}

        {accounts.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Available Accounts ({accounts.length})</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {accounts.map((account, index) => (
                <div
                  key={account.username}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedAccount === account.username
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedAccount(account.username)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm">{account.username}</div>
                      <div className="text-xs text-gray-500 truncate">
                        {account.full_name}
                      </div>
                    </div>
                    {selectedAccount === account.username && (
                      <CheckCircle className="w-4 h-4 text-blue-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Switch Actions */}
        {selectedAccount && (
          <div className="space-y-2">
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="text-sm font-medium text-blue-900">
                Selected: {selectedAccount}
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                onClick={handleSwitchAccount}
                disabled={isSwitching}
                size="sm"
                className="flex-1"
              >
                {isSwitching ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Users className="w-4 h-4 mr-2" />
                )}
                Switch Account
              </Button>

              <Button
                onClick={handleCompleteFlow}
                disabled={isSwitching}
                size="sm"
                className="flex-1"
                variant="default"
              >
                {isSwitching ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Complete Flow
              </Button>
            </div>
          </div>
        )}

        {/* Status Messages */}
        {launchAppMutation.isSuccess && (
          <Alert>
            <CheckCircle className="w-4 h-4" />
            <AlertDescription>
              App launched successfully and navigated to profile tab
            </AlertDescription>
          </Alert>
        )}

        {openSwitcherMutation.isSuccess && (
          <Alert>
            <CheckCircle className="w-4 h-4" />
            <AlertDescription>
              Account switcher opened successfully
            </AlertDescription>
          </Alert>
        )}

        {switchAccountMutation.isSuccess && (
          <Alert>
            <CheckCircle className="w-4 h-4" />
            <AlertDescription>
              Successfully switched to {switchAccountMutation.data?.data?.target_username || selectedAccount}
            </AlertDescription>
          </Alert>
        )}

        {/* Error Messages */}
        {launchAppMutation.isError && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Launch failed: {launchAppMutation.error?.message}
            </AlertDescription>
          </Alert>
        )}

        {openSwitcherMutation.isError && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Open switcher failed: {openSwitcherMutation.error?.message}
            </AlertDescription>
          </Alert>
        )}

        {switchAccountMutation.isError && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Switch failed: {switchAccountMutation.error?.message}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
