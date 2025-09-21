// Fix device storage keys in localStorage
const licenseKey = '87D5A12367B44F2AB92128FAABF5F020';
const wrongKey = `${licenseKey}_${licenseKey}_savedDevices`;
const correctKey = `${licenseKey}_savedDevices`;

// Get devices from wrong key
const devices = localStorage.getItem(wrongKey);
if (devices) {
  console.log('Found devices in wrong key:', devices);
  // Move to correct key
  localStorage.setItem(correctKey, devices);
  localStorage.removeItem(wrongKey);
  console.log('Moved devices to correct key');
} else {
  console.log('No devices found in wrong key');
}

// Also clean up old non-license keys
const oldDevices = localStorage.getItem('savedDevices');
if (oldDevices) {
  console.log('Found devices in old key:', oldDevices);
  // If correct key is empty, move old devices there
  if (!localStorage.getItem(correctKey)) {
    localStorage.setItem(correctKey, oldDevices);
    console.log('Moved old devices to correct license key');
  }
  localStorage.removeItem('savedDevices');
}

console.log('Device storage cleanup complete');
