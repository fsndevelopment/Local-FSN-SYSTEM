// FSN Client Frontend Update
// This automatically detects if the client is running the local backend

// Auto-detect local backend
const detectLocalBackend = async () => {
    const localIPs = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://192.168.1.100:8000',  // Common home network IP
        'http://192.168.0.100:8000',  // Common home network IP
        'http://10.0.0.100:8000',     // Common home network IP
    ];
    
    for (const url of localIPs) {
        try {
            const response = await fetch(`${url}/health`);
            if (response.ok) {
                console.log(`✅ Found local FSN backend at: ${url}`);
                return url;
            }
        } catch (error) {
            // Continue to next URL
        }
    }
    
    // Fallback to cloud backend
    console.log('🌐 Using cloud backend');
    return 'https://fsn-system-backend.onrender.com';
};

// Update your frontend API calls to use this:
const getBackendURL = async () => {
    const backendURL = await detectLocalBackend();
    return backendURL;
};

// Example usage in your frontend:
const apiCall = async (endpoint) => {
    const baseURL = await getBackendURL();
    const response = await fetch(`${baseURL}${endpoint}`);
    return response.json();
};

// Export for use in your frontend
window.FSNClient = {
    getBackendURL,
    apiCall
};
