"use client"

import { useLicense } from "@/lib/providers/license-provider"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu"
import { 
  Shield, 
  Clock, 
  Users, 
  LogOut, 
  RefreshCw,
  Instagram,
  MessageSquare
} from "lucide-react"

export function LicenseStatus() {
  const { license, clearLicense, refreshLicense } = useLicense()

  if (!license) return null

  const formatExpiryDate = (expiresAt: string | null) => {
    if (!expiresAt) return "Never"
    return new Date(expiresAt).toLocaleDateString()
  }

  const getPlatformIcons = (platforms: string[]) => {
    return platforms.map(platform => {
      switch (platform) {
        case 'instagram':
          return <Instagram key={platform} className="w-4 h-4" />
        case 'threads':
          return <MessageSquare key={platform} className="w-4 h-4" />
        default:
          return null
      }
    })
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className="flex items-center gap-1 bg-white/90 text-gray-900 border-gray-300 hover:bg-white">
        <Users className="w-3 h-3" />
        {license.licenseType}
      </Badge>
      
      <Badge variant="outline" className="flex items-center gap-1 bg-white/90 text-gray-900 border-gray-300 hover:bg-white">
        <Clock className="w-3 h-3" />
        {formatExpiryDate(license.expiresAt)}
      </Badge>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="text-white hover:bg-white/10 hover:text-white">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={refreshLicense}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh License
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
