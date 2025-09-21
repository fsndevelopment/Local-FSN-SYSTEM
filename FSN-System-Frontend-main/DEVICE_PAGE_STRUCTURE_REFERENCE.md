# DEVICE PAGE STRUCTURE REFERENCE
## The ONLY CORRECT Structure for All Pages with Dark Headers

This document defines the EXACT structure that must be replicated on ALL pages with dark headers (Models, Templates, Accounts, Dashboard, Warmup, Running).

## OVERALL PAGE STRUCTURE

```jsx
<LicenseBlocker action="access [page-specific action]">
  <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
    {/* Main Header Section - Dark Background */}
    <div className="relative overflow-hidden bg-gradient-to-r from-black via-gray-900 to-black">
      {/* SVG Pattern Overlay */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')] opacity-10"></div>
      
      {/* Header Container */}
      <div className="relative px-6 py-12">
        <div className="max-w-7xl mx-auto">
          {/* MAIN HEADER CONTENT */}
          <div className="flex items-center justify-between">
            {/* LEFT SIDE - Title, Description, Status */}
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                {/* Icon Container */}
                <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-2xl">
                  <[ICON_COMPONENT] className="w-6 h-6 text-black" />
                </div>
                {/* Title and Description */}
                <div>
                  <h1 className="text-4xl font-bold text-white tracking-tight">[PAGE_TITLE]</h1>
                  <p className="text-gray-300 text-lg mt-1">[PAGE_DESCRIPTION]</p>
                </div>
              </div>
              
              {/* Live Status Indicator */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                  <div className="relative">
                    <div className="w-2 h-2 bg-[COLOR]-400 rounded-full animate-pulse"></div>
                    <div className="absolute inset-0 w-2 h-2 bg-[COLOR]-400 rounded-full animate-ping opacity-75"></div>
                  </div>
                  <span className="text-white text-sm font-medium">[STATUS_TEXT]</span>
                </div>
                
                <div className="text-white/60 text-sm">
                  Last updated: {new Date().toLocaleTimeString()}
                </div>
              </div>
            </div>
            
            {/* RIGHT SIDE - Action Buttons Container */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
              <div className="flex items-center space-x-4">
                {/* Action Buttons - Customize per page */}
                <Button 
                  variant="outline"
                  onClick={handleRefresh}
                  disabled={isLoading}
                  className="bg-white/10 text-white border-white/20 hover:bg-white/20 rounded-2xl px-4 py-2"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <Button 
                  onClick={() => router.push('/[page]/add')}
                  className="bg-white text-black hover:bg-gray-100 font-semibold px-6 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] border-0"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Add [ITEM]
                </Button>
                {/* Additional buttons as needed */}
              </div>
            </div>
          </div>
          
          {/* SEARCH BAR AND PLATFORM SWITCHER SECTION */}
          <div className="mt-8">
            <div className="flex items-center justify-between">
              {/* Search Bar */}
              <div className="flex-1 max-w-md">
                <GlobalSearchBar placeholder="Search [items]..." />
              </div>

              {/* Platform Switcher */}
              <div className="flex items-center space-x-4">
                <PlatformSwitch />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* MAIN CONTENT AREA */}
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Page-specific content goes here */}
    </div>
  </div>
</LicenseBlocker>
```

## CRITICAL STRUCTURAL REQUIREMENTS

### 1. HEADER CONTAINER SIZING
- **Outer Container**: `px-6 py-12` - Provides padding around the entire header
- **Inner Container**: `max-w-7xl mx-auto` - Centers content and limits width
- **Main Flex Container**: `flex items-center justify-between` - Creates left/right layout

### 2. SEARCH BAR POSITIONING
- **MUST BE OUTSIDE** the main `flex items-center justify-between` container
- **MUST BE INSIDE** the `max-w-7xl mx-auto` container
- **Uses**: `mt-8` for spacing from the main header content
- **Structure**: `flex items-center justify-between` for search bar and platform switcher

### 3. COLOR SCHEMES PER PAGE
- **Dashboard**: `bg-green-400` (green dots)
- **Models**: `bg-pink-400` (pink dots)
- **Templates**: `bg-blue-400` (blue dots)
- **Accounts**: `bg-purple-400` (purple dots)
- **Devices**: `bg-blue-400` (blue dots)
- **Warmup**: `bg-orange-400` (orange dots)
- **Running**: `bg-green-400` (green dots)

### 4. ICON COMPONENTS PER PAGE
- **Dashboard**: `BarChart3`
- **Models**: `User`
- **Templates**: `LayoutTemplate`
- **Accounts**: `Users`
- **Devices**: `Smartphone`
- **Warmup**: `Thermometer`
- **Running**: `Play`

### 5. BUTTON STRUCTURES
- **Primary Action Button**: White background, black text, rounded-2xl, shadow effects
- **Secondary Action Buttons**: Semi-transparent white background, white text, rounded-2xl
- **Button Spacing**: `space-x-4` between buttons in the button container

### 6. STATUS INDICATORS
- **Container**: `bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20`
- **Dot**: `w-2 h-2` with pulse and ping animations
- **Text**: `text-white text-sm font-medium`

## COMMON MISTAKES TO AVOID

1. **DON'T** put search bar inside the main `flex items-center justify-between` container
2. **DON'T** use different container widths or padding
3. **DON'T** change the button styling or positioning
4. **DON'T** modify the status indicator structure
5. **DON'T** change the header background or pattern overlay

## IMPLEMENTATION CHECKLIST

For each page, ensure:
- [ ] Header uses exact same container structure
- [ ] Search bar is positioned OUTSIDE main flex container but INSIDE max-w-7xl container
- [ ] Button container uses exact same styling
- [ ] Status indicator uses correct color for the page
- [ ] Icon component matches the page type
- [ ] Page-specific content goes in the main content area with `max-w-7xl mx-auto px-6 py-8`
