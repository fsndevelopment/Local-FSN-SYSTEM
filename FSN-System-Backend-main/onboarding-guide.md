# Client Onboarding Guide (for FSN)

1) **Sign in** at fsndevelopment.com with your license.
2) Go to **Connect Device** → click **Generate Pair Code**.
3) **Download FSN Device Agent** for macOS and open it.
4) In Agent, click **Pair**, paste the code (or scan QR).
5) Connect your iPhone via USB, enable **Developer Mode**, trust the Mac.
6) (First time only) Open Xcode → run **WebDriverAgent** on the iPhone (Team + Bundle ID).
7) In FSN web, go to **Devices** and fill:
   - UDID, Appium port, WDA port, MJPEG port, WDA bundle ID.
8) In **Running**, your device should show **Online**. Click **Start** to run your template.
