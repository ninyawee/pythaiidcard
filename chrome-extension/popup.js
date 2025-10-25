/**
 * Popup UI logic for Thai ID Card Reader extension
 */

// UI Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const passcodeInput = document.getElementById('passcodeInput');
const connectButton = document.getElementById('connectButton');
const configSection = document.getElementById('configSection');
const cardDataSection = document.getElementById('cardDataSection');
const autoFillToggle = document.getElementById('autoFillToggle');
const serverUrlDisplay = document.getElementById('serverUrlDisplay');

// Card data elements
const cidValue = document.getElementById('cidValue');
const thaiNameValue = document.getElementById('thaiNameValue');
const englishNameValue = document.getElementById('englishNameValue');
const dobValue = document.getElementById('dobValue');
const addressValue = document.getElementById('addressValue');

// Buttons
const copyCidButton = document.getElementById('copyCidButton');
const copyThaiNameButton = document.getElementById('copyThaiNameButton');
const copyEnglishNameButton = document.getElementById('copyEnglishNameButton');
const copyAddressButton = document.getElementById('copyAddressButton');
const downloadButton = document.getElementById('downloadButton');
const triggerReadButton = document.getElementById('triggerReadButton');

// State
let currentCardData = null;

/**
 * Initialize popup
 */
async function initialize() {
  console.log('Popup initializing...');

  // Load settings
  const settings = await loadSettings();

  // Set passcode input
  if (settings.passcode) {
    passcodeInput.value = settings.passcode;
  }

  // Set auto-fill toggle
  autoFillToggle.checked = settings.autoFillEnabled !== false;

  // Set server URL display
  if (settings.serverUrl) {
    serverUrlDisplay.textContent = `Server: ${settings.serverUrl}`;
  }

  // Get current status from background
  try {
    const response = await chrome.runtime.sendMessage({ type: 'get_status' });
    updateStatus(response.status);

    // If connected, load card data
    if (response.hasCardData) {
      loadCardData();
    }
  } catch (error) {
    console.error('Failed to get status:', error);
  }

  // Setup event listeners
  setupEventListeners();
}

/**
 * Load settings from storage
 */
async function loadSettings() {
  const result = await chrome.storage.sync.get(['serverUrl', 'passcode', 'autoFillEnabled']);
  return {
    serverUrl: result.serverUrl || 'ws://localhost:8765/ws',
    passcode: result.passcode || '',
    autoFillEnabled: result.autoFillEnabled !== false,
  };
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Connect button
  connectButton.addEventListener('click', handleConnect);

  // Enter key in passcode input
  passcodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleConnect();
    }
  });

  // Auto-fill toggle
  autoFillToggle.addEventListener('change', async (e) => {
    const autoFillEnabled = e.target.checked;
    await chrome.storage.sync.set({ autoFillEnabled });
    await chrome.runtime.sendMessage({
      type: 'update_settings',
      settings: { autoFillEnabled }
    });
  });

  // Copy buttons
  copyCidButton.addEventListener('click', () => copyToClipboard(cidValue.textContent, 'CID'));
  copyThaiNameButton.addEventListener('click', () => copyToClipboard(thaiNameValue.textContent, 'Thai name'));
  copyEnglishNameButton.addEventListener('click', () => copyToClipboard(englishNameValue.textContent, 'English name'));
  copyAddressButton.addEventListener('click', () => copyToClipboard(addressValue.textContent, 'Address'));

  // Download button
  downloadButton.addEventListener('click', downloadCardData);

  // Trigger read button
  triggerReadButton.addEventListener('click', triggerCardRead);

  // Listen for messages from background
  chrome.runtime.onMessage.addListener((message) => {
    console.log('Message received in popup:', message.type);

    switch (message.type) {
      case 'connection_status':
        updateStatus(message.status);
        break;

      case 'card_data':
        displayCardData(message.data);
        break;

      case 'card_event':
        handleCardEvent(message.event);
        break;
    }
  });
}

/**
 * Handle connect button click
 */
async function handleConnect() {
  const passcode = passcodeInput.value.trim();

  if (!passcode) {
    alert('Please enter a passcode');
    return;
  }

  connectButton.disabled = true;
  connectButton.textContent = 'Connecting...';

  try {
    await chrome.runtime.sendMessage({
      type: 'connect',
      passcode: passcode
    });

    // Update status will be received via message
  } catch (error) {
    console.error('Connection failed:', error);
    alert('Failed to connect: ' + error.message);
  } finally {
    connectButton.disabled = false;
    connectButton.textContent = 'Connect';
  }
}

/**
 * Load card data from background
 */
async function loadCardData() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'get_card_data' });
    if (response.data) {
      displayCardData(response.data);
    }
  } catch (error) {
    console.error('Failed to load card data:', error);
  }
}

/**
 * Display card data in UI
 */
function displayCardData(data) {
  currentCardData = data;

  // Update values
  cidValue.textContent = data.cid || '-';
  thaiNameValue.textContent = data.thai_fullname || '-';
  englishNameValue.textContent = data.english_fullname || '-';
  dobValue.textContent = data.date_of_birth || '-';
  addressValue.textContent = data.address || '-';

  // Show card data section
  cardDataSection.style.display = 'block';
}

/**
 * Update connection status
 */
function updateStatus(status) {
  const statusConfig = {
    'connected': {
      text: 'Connected',
      color: '#4CAF50',
      showConfig: false
    },
    'connecting': {
      text: 'Connecting...',
      color: '#FFC107',
      showConfig: true
    },
    'disconnected': {
      text: 'Disconnected',
      color: '#9E9E9E',
      showConfig: true
    },
    'error': {
      text: 'Connection Error',
      color: '#F44336',
      showConfig: true
    },
    'auth_required': {
      text: 'Authentication Required',
      color: '#F44336',
      showConfig: true
    },
    'auth_failed': {
      text: 'Invalid Passcode',
      color: '#F44336',
      showConfig: true
    },
    'no_passcode': {
      text: 'Not Configured',
      color: '#9E9E9E',
      showConfig: true
    },
    'card_detected': {
      text: 'Card Detected',
      color: '#2196F3',
      showConfig: false
    }
  };

  const config = statusConfig[status] || statusConfig.disconnected;

  statusText.textContent = config.text;
  statusDot.style.backgroundColor = config.color;

  // Show/hide config section based on connection status
  configSection.style.display = config.showConfig ? 'block' : 'none';
}

/**
 * Handle card events
 */
function handleCardEvent(event) {
  if (event === 'inserted') {
    // Could show a notification or update UI
    console.log('Card inserted');
  } else if (event === 'removed') {
    // Could clear card data or update UI
    console.log('Card removed');
  }
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text, fieldName) {
  if (!text || text === '-') {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);

    // Show feedback
    const originalText = fieldName + ' copied!';
    statusText.textContent = originalText;

    setTimeout(() => {
      // Restore status after 2 seconds
      chrome.runtime.sendMessage({ type: 'get_status' }).then(response => {
        updateStatus(response.status);
      });
    }, 2000);
  } catch (error) {
    console.error('Failed to copy:', error);
    alert('Failed to copy to clipboard');
  }
}

/**
 * Download card data as JSON
 */
function downloadCardData() {
  if (!currentCardData) {
    alert('No card data available');
    return;
  }

  // Create JSON blob
  const json = JSON.stringify(currentCardData, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  // Create download link
  const a = document.createElement('a');
  a.href = url;
  a.download = `thai-id-card-${currentCardData.cid || 'data'}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Cleanup
  URL.revokeObjectURL(url);

  statusText.textContent = 'Downloaded!';
  setTimeout(() => {
    chrome.runtime.sendMessage({ type: 'get_status' }).then(response => {
      updateStatus(response.status);
    });
  }, 2000);
}

/**
 * Trigger manual card read
 */
async function triggerCardRead() {
  triggerReadButton.disabled = true;
  triggerReadButton.textContent = 'Reading...';

  try {
    const response = await chrome.runtime.sendMessage({ type: 'trigger_read' });

    if (response.success) {
      statusText.textContent = 'Reading card...';
    } else {
      alert('Failed to trigger read: ' + (response.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('Failed to trigger read:', error);
    alert('Failed to trigger card read');
  } finally {
    setTimeout(() => {
      triggerReadButton.disabled = false;
      triggerReadButton.textContent = 'Read Card Now';
    }, 1000);
  }
}

// Initialize when popup opens
initialize();
