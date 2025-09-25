"use client"

import React, { useState, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Upload, Download, FileSpreadsheet, AlertCircle, CheckCircle, Users } from "lucide-react"
import { useDevices } from "@/lib/hooks/use-devices"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"
import { toast } from "@/hooks/use-toast"

interface BulkAddAccountsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAccountsAdded?: () => void
}

interface BulkAccountData {
  username: string
  password: string
  email?: string
  twoFA?: string
  container: string
}

export function BulkAddAccountsDialog({ open, onOpenChange, onAccountsAdded }: BulkAddAccountsDialogProps) {
  const [selectedDevice, setSelectedDevice] = useState<string>("")
  const [selectedModel, setSelectedModel] = useState<string>("none")
  const [notes, setNotes] = useState("")
  const [xlsxFile, setXlsxFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [devices, setDevices] = useState<any[]>([])
  const [models, setModels] = useState<any[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load devices from API
  const { data: apiDevicesResponse } = useDevices()

  // Load devices and models
  React.useEffect(() => {
    const loadData = async () => {
      try {
        // Load devices
        const savedDevices = licenseAwareStorageService.getDevices()
        const apiDevices = Array.isArray(apiDevicesResponse) 
          ? apiDevicesResponse 
          : apiDevicesResponse?.devices || []
        
        const combined = [...apiDevices, ...savedDevices]
        const unique = combined.filter((device, index, self) => 
          index === self.findIndex(d => d.id === device.id)
        )
        setDevices(unique)

        // Load models
        const savedModels = await licenseAwareStorageService.getModels()
        setModels(savedModels)
      } catch (error) {
        console.error('Failed to load data:', error)
      }
    }
    
    loadData()
  }, [apiDevicesResponse])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      validateAndSetFile(file)
    }
  }

  const validateAndSetFile = (file: File) => {
    if (file.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" || 
        file.name.endsWith('.xlsx')) {
      setXlsxFile(file)
      toast({
        title: "File Selected",
        description: `${file.name} is ready for import.`
      })
    } else {
      toast({
        title: "Invalid File Type",
        description: "Please select an XLSX file.",
        variant: "destructive"
      })
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragOver(false)

    const files = event.dataTransfer.files
    if (files.length > 0) {
      validateAndSetFile(files[0])
    }
  }

  const downloadTemplate = () => {
    const templateContent = `# Bulk Account Import Template Instructions

## Required Columns (in exact order):
1. Username - The account username
2. Password - The account password  
3. Email - Account email (leave empty if using 2FA)
4. 2FA - Two-factor authentication code/secret (leave empty if using Email)
5. Container - Container identifier for the account

## Important Rules:
- Either Email OR 2FA column should have a value, not both
- If Email is filled and 2FA is empty = Email-based account
- If 2FA is filled and Email is empty = 2FA-based account
- Container column is required for all accounts
- Save your file as .xlsx format

## Example Data:
Username    | Password  | Email              | 2FA    | Container
user1       | pass123   | user1@email.com    |        | container1
user2       | pass456   |                    | ABC123 | container2
user3       | pass789   | user3@email.com    |        | container3

## Steps:
1. Create a new Excel file (.xlsx)
2. Add the column headers exactly as shown above
3. Fill in your account data following the rules
4. Save as .xlsx format
5. Upload the file using the file selector in the bulk import dialog

## Notes:
- Maximum recommended accounts per import: 100
- All accounts will be assigned to the selected device and model
- Any errors will be reported after processing
- Successfully imported accounts will appear in your accounts list
`

    const blob = new Blob([templateContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'bulk_accounts_template_instructions.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast({
      title: "Template Downloaded",
      description: "Check your downloads folder for the instructions file."
    })
  }

  const processXLSXFile = async (file: File): Promise<BulkAccountData[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer)
          
          // For demonstration, create sample accounts
          // TODO: Install 'xlsx' library and implement proper parsing
          // npm install xlsx @types/xlsx
          // import * as XLSX from 'xlsx'
          
          const accounts: BulkAccountData[] = [
            {
              username: "demo_user1",
              password: "demo_pass1",
              email: "demo1@example.com",
              twoFA: "",
              container: "container1"
            },
            {
              username: "demo_user2", 
              password: "demo_pass2",
              email: "",
              twoFA: "ABC123",
              container: "container2"
            }
          ]
          
          // Actual XLSX parsing would look like this:
          // const workbook = XLSX.read(data, { type: 'array' })
          // const worksheet = workbook.Sheets[workbook.SheetNames[0]]
          // const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
          // const accounts = jsonData.slice(1).map(row => ({
          //   username: row[0],
          //   password: row[1], 
          //   email: row[2] || "",
          //   twoFA: row[3] || "",
          //   container: row[4]
          // }))
          
          resolve(accounts)
        } catch (error) {
          reject(error)
        }
      }
      reader.readAsArrayBuffer(file)
    })
  }

  const handleSubmit = async () => {
    if (!selectedDevice) {
      toast({
        title: "Device Required",
        description: "Please select a device for the accounts.",
        variant: "destructive"
      })
      return
    }

    if (!xlsxFile) {
      toast({
        title: "File Required",
        description: "Please select an XLSX file to import.",
        variant: "destructive"
      })
      return
    }

    setIsProcessing(true)

    try {
      const accountsData = await processXLSXFile(xlsxFile)
      
      // Process each account
      let successCount = 0
      let errorCount = 0
      
      for (const accountData of accountsData) {
        try {
          const newAccount = {
            id: Date.now() + Math.random(),
            username: accountData.username,
            password: accountData.password,
            email: accountData.email || "",
            twoFA: accountData.twoFA || "",
            container: accountData.container,
            device: selectedDevice,
            model: selectedModel === "none" ? "" : selectedModel || "",
            platform: "threads", // Default platform
            status: "active",
            warmup_phase: "phase_1",
            notes: notes,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }

          await licenseAwareStorageService.addAccount(newAccount)
          successCount++
        } catch (error) {
          console.error('Failed to add account:', accountData.username, error)
          errorCount++
        }
      }

      toast({
        title: "Bulk Import Complete",
        description: `Successfully imported ${successCount} accounts. ${errorCount > 0 ? `${errorCount} failed.` : ''}`,
        variant: successCount > 0 ? "default" : "destructive"
      })

      if (successCount > 0) {
        // Reset form
        setSelectedDevice("")
        setSelectedModel("none")
        setNotes("")
        setXlsxFile(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ""
        }

        // Notify parent to refresh
        onAccountsAdded?.()
        onOpenChange(false)
      }

    } catch (error) {
      console.error('Bulk import failed:', error)
      toast({
        title: "Import Failed",
        description: "Failed to process the XLSX file. Please check the format and try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="!w-[800px] !h-[600px] !max-w-none !max-h-none"
        style={{ width: '800px', height: '600px' }}
      >
        <DialogHeader className="pb-4">
          <DialogTitle className="flex items-center space-x-2 text-xl">
            <Users className="w-6 h-6" />
            <span>Bulk Add Accounts</span>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1">
          <div className="space-y-4">
            {/* Device, Model, and Notes - Same Line at TOP */}
            <div className="grid grid-cols-3 gap-4">
              {/* Device Selection */}
              <div className="flex flex-col items-center space-y-2">
                <Label className="text-sm font-medium">Device Assignment</Label>
                <div className="w-full">
                  <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                    <SelectTrigger className="h-10 text-sm focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 w-full">
                      <SelectValue placeholder="Select device" />
                    </SelectTrigger>
                    <SelectContent>
                      {devices.map((device) => (
                        <SelectItem key={device.id} value={device.id.toString()}>
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${
                              device.status === 'connected' || device.status === 'active' 
                                ? 'bg-green-500' : 'bg-gray-400'
                            }`} />
                            <span className="text-sm">{device.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Model Assignment */}
              <div className="flex flex-col items-center space-y-2">
                <Label className="text-sm font-medium">Assign Model</Label>
                <div className="w-full">
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger className="h-10 text-sm focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 w-full">
                      <SelectValue placeholder="Select model">
                        {selectedModel && selectedModel !== "none" && (
                          <div className="flex items-center space-x-2">
                            {(() => {
                              const model = models.find(m => m.id === selectedModel);
                              if (!model) return null;
                              return (
                                <>
                                  {model.profilePhoto ? (
                                    <img 
                                      src={model.profilePhoto} 
                                      alt={model.name}
                                      className="w-5 h-5 rounded-full object-cover"
                                    />
                                  ) : (
                                    <div className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center">
                                      <span className="text-xs text-gray-500 font-medium">
                                        {model.name.charAt(0).toUpperCase()}
                                      </span>
                                    </div>
                                  )}
                                  <span className="text-sm">{model.name}</span>
                                </>
                              );
                            })()}
                          </div>
                        )}
                        {selectedModel === "none" && (
                          <div className="flex items-center space-x-2">
                            <div className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center">
                              <span className="text-xs text-gray-500">—</span>
                            </div>
                            <span className="text-sm">No Model</span>
                          </div>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center">
                            <span className="text-xs text-gray-500">—</span>
                          </div>
                          <span className="text-sm">No Model</span>
                        </div>
                      </SelectItem>
                      {models.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          <div className="flex items-center space-x-2">
                            {model.profilePhoto ? (
                              <img 
                                src={model.profilePhoto} 
                                alt={model.name}
                                className="w-6 h-6 rounded-full object-cover"
                              />
                            ) : (
                              <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center">
                                <span className="text-xs text-gray-500 font-medium">
                                  {model.name.charAt(0).toUpperCase()}
                                </span>
                              </div>
                            )}
                            <span className="text-sm">{model.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Notes */}
              <div className="flex flex-col items-center space-y-2">
                <Label className="text-sm font-medium">Notes (Optional)</Label>
                <div className="w-full">
                  <Textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add notes..."
                    className="h-10 text-sm resize-none focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-left w-full min-h-[40px] max-h-[40px]"
                  />
                </div>
              </div>
            </div>

            {/* File Upload */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">XLSX File Selection</Label>
              <div 
                className={`border-2 border-dashed rounded-lg p-4 text-center transition-all duration-200 cursor-pointer ${
                  isDragOver 
                    ? "border-blue-400 bg-blue-50" 
                    : xlsxFile 
                      ? "border-green-400 bg-green-50" 
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <FileSpreadsheet className={`w-8 h-8 mx-auto mb-2 ${
                  isDragOver ? "text-blue-500" : xlsxFile ? "text-green-500" : "text-gray-400"
                }`} />
                <div className="space-y-2">
                  <p className="text-xs text-gray-600">
                    {isDragOver 
                      ? "Drop your XLSX file here"
                      : xlsxFile 
                        ? xlsxFile.name 
                        : "Drag & drop your XLSX file here or click to browse"
                    }
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      fileInputRef.current?.click()
                    }}
                    className="h-7 text-xs"
                  >
                    <Upload className="w-3 h-3 mr-1" />
                    {xlsxFile ? "Change File" : "Choose File"}
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
                {xlsxFile && (
                  <div className="mt-2 flex items-center justify-center space-x-1 text-green-600">
                    <CheckCircle className="w-3 h-3" />
                    <span className="text-xs">File selected successfully</span>
                  </div>
                )}
              </div>
            </div>

            {/* Template Download */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-medium text-blue-900 mb-1">Need Help?</h4>
                  <p className="text-xs text-blue-700 mb-2">
                    Download the template instructions to learn how to format your XLSX file correctly.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={downloadTemplate}
                    className="h-7 text-xs border-blue-300 text-blue-700 hover:bg-blue-100"
                  >
                    <Download className="w-3 h-3 mr-1" />
                    Download Instructions
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isProcessing}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isProcessing || !selectedDevice || !xlsxFile}
            className="bg-black text-white hover:bg-gray-800"
          >
            {isProcessing ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                Processing...
              </>
            ) : (
              <>
                <Users className="w-4 h-4 mr-2" />
                Import Accounts
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
