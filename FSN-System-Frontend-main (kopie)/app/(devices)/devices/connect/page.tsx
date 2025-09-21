"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Copy, Check, Smartphone, Wifi, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function ConnectDevicePage() {
  const [connectionCode, setConnectionCode] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const generateConnectionCode = () => {
    setIsLoading(true);
    
    // Generate a simple connection code
    const code = Math.random().toString(36).substr(2, 8).toUpperCase();
    setConnectionCode(code);
    
    toast({
      title: "Connection code generated",
      description: "Use this code with your Python agent to connect your device.",
    });
    
    setIsLoading(false);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast({
        title: "Copied to clipboard",
        description: "Connection code copied successfully.",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Connect Your Device</h1>
          <p className="text-muted-foreground">
            Connect your Mac with iPhone to the FSN system
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Connection Code Generation */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                Generate Connection Code
              </CardTitle>
              <CardDescription>
                Create a code to connect your Python agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button 
                onClick={generateConnectionCode} 
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? "Generating..." : "Generate Connection Code"}
              </Button>

              {connectionCode && (
                <div>
                  <Label htmlFor="connection-code">Connection Code</Label>
                  <div className="flex gap-2">
                    <Input
                      id="connection-code"
                      value={connectionCode}
                      readOnly
                      className="font-mono text-lg"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => copyToClipboard(connectionCode)}
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wifi className="h-5 w-5" />
                How to Connect
              </CardTitle>
              <CardDescription>
                Follow these steps to connect your device
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3 list-decimal list-inside">
                <li>
                  <strong>Download the Python agent:</strong> Download <code className="bg-muted px-1 rounded">fsn_agent.py</code> to your Mac
                </li>
                <li>
                  <strong>Run the agent:</strong> Open Terminal and run:
                  <div className="bg-muted p-2 rounded mt-2 font-mono text-sm">
                    python3 fsn_agent.py
                  </div>
                </li>
                <li>
                  <strong>Your device will appear:</strong> It will automatically show up in your device list
                </li>
                <li>
                  <strong>Start automation:</strong> Use the frontend to start automation jobs
                </li>
              </ol>
            </CardContent>
          </Card>
        </div>

        {/* Status */}
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
            <CardDescription>
              Monitor your device connection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>No token needed!</strong> The Python agent will automatically connect your device. 
                Just run the Python file and your iPhone will appear in the device list.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}