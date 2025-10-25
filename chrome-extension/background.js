/**
 * Background service worker for Thai ID Card Reader extension
 * Manages WebSocket connection to local card reader server
 */

// Configuration
const DEFAULT_SERVER_URL = 'ws://localhost:8765/ws';
const RECONNECT_DELAY = 5000; // 5 seconds
const HEARTBEAT_INTERVAL = 30000; // 30 seconds

// State
let socket = null;
let reconnectTimer = null;
let heartbeatTimer = null;
let connectionStatus = 'disconnected';
let lastCardData = null;
let serverUrl = DEFAULT_SERVER_URL;
let passcode = '';

/**
 * Initialize the extension
 */
async function initialize() {
  console.log('Thai ID Card Reader extension initializing...');

  // Load settings from storage
  const settings = await loadSettings();
  serverUrl = settings.serverUrl || DEFAULT_SERVER_URL;
  passcode = settings.passcode || '';

  // Restore last card data if available
  const stored = await chrome.storage.local.get(['cardData']);
  if (stored.cardData) {
    lastCardData = stored.cardData;
  }

  // Connect to server if passcode is configured
  if (passcode) {
    connectToServer();
  } else {
    updateStatus('no_passcode');
    console.warn('No passcode configured. Please set up pairing in the extension popup.');
  }
}

/**
 * Load settings from chrome.storage
 */
async function loadSettings() {
  const result = await chrome.storage.sync.get(['serverUrl', 'passcode', 'autoFillEnabled']);
  return {
    serverUrl: result.serverUrl || DEFAULT_SERVER_URL,
    passcode: result.passcode || '',
    autoFillEnabled: result.autoFillEnabled !== false, // Default true
  };
}

/**
 * Save settings to chrome.storage
 */
async function saveSettings(settings) {
  await chrome.storage.sync.set(settings);
  console.log('Settings saved:', settings);
}

/**
 * Connect to the card reader WebSocket server
 */
function connectToServer() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    console.log('Already connected to server');
    return;
  }

  if (!passcode) {
    console.error('Cannot connect: No passcode configured');
    updateStatus('no_passcode');
    return;
  }

  console.log(`Connecting to ${serverUrl} with passcode authentication...`);
  updateStatus('connecting');

  try {
    // Create WebSocket with custom headers (passcode authentication)
    // Note: WebSocket API doesn't support custom headers directly
    // We'll need to use a query parameter instead
    const authUrl = `${serverUrl}?passcode=${encodeURIComponent(passcode)}`;
    socket = new WebSocket(authUrl);

    socket.onopen = onSocketOpen;
    socket.onmessage = onSocketMessage;
    socket.onerror = onSocketError;
    socket.onclose = onSocketClose;

  } catch (error) {
    console.error('Failed to create WebSocket:', error);
    updateStatus('error');
    scheduleReconnect();
  }
}

/**
 * Handle WebSocket open event
 */
function onSocketOpen(event) {
  console.log('WebSocket connected successfully');
  updateStatus('connected');

  // Clear reconnect timer
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  // Start heartbeat
  startHeartbeat();

  // Notify popup
  chrome.runtime.sendMessage({
    type: 'connection_status',
    status: 'connected'
  }).catch(() => {}); // Ignore if popup is not open
}

/**
 * Handle WebSocket message event
 */
function onSocketMessage(event) {
  try {
    const message = JSON.parse(event.data);
    console.log('WebSocket message received:', message.type);

    switch (message.type) {
      case 'connected':
        console.log('Server acknowledged connection:', message.message);
        break;

      case 'card_inserted':
        console.log('Card inserted');
        updateStatus('card_detected');
        notifyCardEvent('inserted');
        break;

      case 'card_read':
        console.log('Card data received');
        handleCardData(message.data);
        break;

      case 'card_removed':
        console.log('Card removed');
        updateStatus('connected');
        notifyCardEvent('removed');
        break;

      case 'auth_required':
        console.error('Authentication required:', message.message);
        updateStatus('auth_required');
        disconnect();
        break;

      case 'auth_failed':
        console.error('Authentication failed:', message.message);
        updateStatus('auth_failed');
        disconnect();
        break;

      case 'pong':
        // Heartbeat response
        break;

      default:
        console.warn('Unknown message type:', message.type);
    }
  } catch (error) {
    console.error('Error parsing WebSocket message:', error);
  }
}

/**
 * Handle card data received from server
 */
async function handleCardData(data) {
  lastCardData = data;

  // Store in local storage
  await chrome.storage.local.set({ cardData: data });

  console.log('Card data stored:', {
    cid: data.cid,
    thai_fullname: data.thai_fullname,
    english_fullname: data.english_fullname
  });

  // Notify popup
  chrome.runtime.sendMessage({
    type: 'card_data',
    data: data
  }).catch(() => {});

  // Check if we should auto-fill
  const settings = await loadSettings();
  if (settings.autoFillEnabled) {
    // Send to active tab's content script
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url && tab.url.includes('peakaccount.com')) {
        chrome.tabs.sendMessage(tab.id, {
          type: 'auto_fill',
          data: data
        }).catch(err => console.warn('Cannot send to content script:', err));
      }
    } catch (error) {
      console.warn('Auto-fill notification failed:', error);
    }
  }

  // Show notification
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'Card Read Successfully',
    message: `CID: ${data.cid}\nName: ${data.thai_fullname}`
  });
}

/**
 * Handle WebSocket error event
 */
function onSocketError(event) {
  console.error('WebSocket error:', event);
  updateStatus('error');
}

/**
 * Handle WebSocket close event
 */
function onSocketClose(event) {
  console.log('WebSocket closed:', event.code, event.reason);

  // Stop heartbeat
  stopHeartbeat();

  // Update status
  if (event.code === 1008) {
    // Authentication error
    updateStatus('auth_failed');
  } else {
    updateStatus('disconnected');
  }

  // Schedule reconnect if not intentionally closed
  if (event.code !== 1000) {
    scheduleReconnect();
  }
}

/**
 * Disconnect from server
 */
function disconnect() {
  if (socket) {
    socket.close(1000, 'Client disconnect');
    socket = null;
  }

  stopHeartbeat();

  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  updateStatus('disconnected');
}

/**
 * Schedule automatic reconnection
 */
function scheduleReconnect() {
  if (reconnectTimer) {
    return; // Already scheduled
  }

  console.log(`Reconnecting in ${RECONNECT_DELAY / 1000} seconds...`);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    if (passcode) {
      connectToServer();
    }
  }, RECONNECT_DELAY);
}

/**
 * Start heartbeat ping to keep connection alive
 */
function startHeartbeat() {
  stopHeartbeat();

  heartbeatTimer = setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'ping' }));
    }
  }, HEARTBEAT_INTERVAL);
}

/**
 * Stop heartbeat
 */
function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

/**
 * Update connection status
 */
function updateStatus(status) {
  connectionStatus = status;

  // Update badge
  const badgeConfig = {
    'connected': { text: '✓', color: '#4CAF50' },
    'connecting': { text: '...', color: '#FFC107' },
    'disconnected': { text: '✗', color: '#9E9E9E' },
    'error': { text: '!', color: '#F44336' },
    'auth_required': { text: '🔒', color: '#F44336' },
    'auth_failed': { text: '🔒', color: '#F44336' },
    'no_passcode': { text: '⚙', color: '#9E9E9E' },
    'card_detected': { text: '📇', color: '#2196F3' },
  };

  const config = badgeConfig[status] || badgeConfig.disconnected;
  chrome.action.setBadgeText({ text: config.text });
  chrome.action.setBadgeBackgroundColor({ color: config.color });

  console.log('Status updated:', status);
}

/**
 * Notify about card events
 */
function notifyCardEvent(event) {
  chrome.runtime.sendMessage({
    type: 'card_event',
    event: event
  }).catch(() => {});
}

/**
 * Handle messages from popup and content scripts
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Message received:', message.type);

  switch (message.type) {
    case 'get_status':
      sendResponse({
        status: connectionStatus,
        hasCardData: !!lastCardData,
        serverUrl: serverUrl
      });
      break;

    case 'get_card_data':
      sendResponse({ data: lastCardData });
      break;

    case 'connect':
      passcode = message.passcode;
      saveSettings({ passcode: passcode });
      connectToServer();
      sendResponse({ success: true });
      break;

    case 'disconnect':
      disconnect();
      sendResponse({ success: true });
      break;

    case 'update_settings':
      if (message.settings.passcode !== undefined) {
        passcode = message.settings.passcode;
        disconnect();
        if (passcode) {
          connectToServer();
        }
      }
      if (message.settings.serverUrl !== undefined) {
        serverUrl = message.settings.serverUrl;
      }
      saveSettings(message.settings);
      sendResponse({ success: true });
      break;

    case 'trigger_read':
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'read_card' }));
        sendResponse({ success: true });
      } else {
        sendResponse({ success: false, error: 'Not connected' });
      }
      break;

    default:
      sendResponse({ error: 'Unknown message type' });
  }

  return true; // Keep channel open for async response
});

// Initialize on installation or update
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed/updated');
  initialize();
});

// Initialize when service worker starts
initialize();

console.log('Background service worker loaded');
