/**
 * Content script for Thai ID Card Reader extension
 * Handles form detection and auto-filling on PeakAccount pages
 */

console.log('Thai ID Card Reader content script loaded');

// Form field mappings - maps card data fields to form field patterns
const FIELD_PATTERNS = {
  // Citizen ID patterns
  cid: [
    /citizen.*id/i,
    /id.*card/i,
    /national.*id/i,
    /^cid$/i,
    /เลขประจำตัว/i,
    /เลขบัตรประชาชน/i,
  ],

  // Thai name patterns
  thai_name: [
    /thai.*name/i,
    /name.*thai/i,
    /ชื่อ.*ไทย/i,
    /ชื่อ.*นามสกุล/i,
  ],

  // Thai first name
  thai_first_name: [
    /thai.*first/i,
    /first.*thai/i,
    /ชื่อ$/i,
    /ชื่อจริง/i,
  ],

  // Thai last name
  thai_last_name: [
    /thai.*last/i,
    /last.*thai/i,
    /นามสกุล/i,
    /สกุล$/i,
  ],

  // English name patterns
  english_name: [
    /english.*name/i,
    /name.*english/i,
    /^name$/i,
    /full.*name/i,
  ],

  // English first name
  english_first_name: [
    /^first.*name$/i,
    /given.*name/i,
  ],

  // English last name
  english_last_name: [
    /^last.*name$/i,
    /family.*name/i,
    /surname/i,
  ],

  // Address patterns
  address: [
    /^address$/i,
    /ที่อยู่/i,
    /full.*address/i,
  ],

  // Date of birth patterns
  date_of_birth: [
    /birth.*date/i,
    /date.*birth/i,
    /dob/i,
    /วันเกิด/i,
    /^birthday$/i,
  ],
};

/**
 * Find form fields that match Thai ID card data
 */
function detectFormFields() {
  const fields = {
    cid: null,
    thai_name: null,
    thai_first_name: null,
    thai_last_name: null,
    english_name: null,
    english_first_name: null,
    english_last_name: null,
    address: null,
    date_of_birth: null,
  };

  // Get all input, select, and textarea elements
  const allInputs = document.querySelectorAll('input, select, textarea');

  console.log(`Found ${allInputs.length} form fields to check`);

  allInputs.forEach((input) => {
    // Skip hidden fields, buttons, submit inputs
    if (
      input.type === 'hidden' ||
      input.type === 'submit' ||
      input.type === 'button' ||
      input.disabled
    ) {
      return;
    }

    // Get identifiable attributes
    const id = input.id || '';
    const name = input.name || '';
    const placeholder = input.placeholder || '';
    const label = getFieldLabel(input);
    const ariaLabel = input.getAttribute('aria-label') || '';

    // Combine all text we can use for matching
    const searchText = `${id} ${name} ${placeholder} ${label} ${ariaLabel}`.toLowerCase();

    // Try to match against each field pattern
    for (const [fieldKey, patterns] of Object.entries(FIELD_PATTERNS)) {
      if (!fields[fieldKey]) {
        for (const pattern of patterns) {
          if (pattern.test(searchText)) {
            fields[fieldKey] = input;
            console.log(`Matched ${fieldKey} to`, {
              tag: input.tagName,
              type: input.type,
              id,
              name,
              label,
            });
            break;
          }
        }
      }
    }
  });

  return fields;
}

/**
 * Get the label text for a form field
 */
function getFieldLabel(input) {
  // Try to find associated label by 'for' attribute
  if (input.id) {
    const label = document.querySelector(`label[for="${input.id}"]`);
    if (label) {
      return label.textContent.trim();
    }
  }

  // Try to find parent label
  const parentLabel = input.closest('label');
  if (parentLabel) {
    return parentLabel.textContent.replace(input.value || '', '').trim();
  }

  // Try to find previous sibling label
  let prev = input.previousElementSibling;
  while (prev) {
    if (prev.tagName === 'LABEL') {
      return prev.textContent.trim();
    }
    prev = prev.previousElementSibling;
  }

  return '';
}

/**
 * Auto-fill form with card data
 */
function autoFillForm(cardData) {
  console.log('Auto-filling form with card data:', {
    cid: cardData.cid,
    thai_name: cardData.thai_fullname,
    english_name: cardData.english_fullname,
  });

  // Detect form fields
  const fields = detectFormFields();

  // Track filled fields
  const filled = [];

  // Fill CID
  if (fields.cid && cardData.cid) {
    setFieldValue(fields.cid, cardData.cid);
    filled.push('Citizen ID');
  }

  // Fill Thai name
  if (fields.thai_name && cardData.thai_fullname) {
    setFieldValue(fields.thai_name, cardData.thai_fullname);
    filled.push('Thai name');
  } else {
    // Try separate first/last name fields
    if (fields.thai_first_name && cardData.thai_name?.first_name) {
      setFieldValue(fields.thai_first_name, cardData.thai_name.first_name);
      filled.push('Thai first name');
    }
    if (fields.thai_last_name && cardData.thai_name?.last_name) {
      setFieldValue(fields.thai_last_name, cardData.thai_name.last_name);
      filled.push('Thai last name');
    }
  }

  // Fill English name
  if (fields.english_name && cardData.english_fullname) {
    setFieldValue(fields.english_name, cardData.english_fullname);
    filled.push('English name');
  } else {
    // Try separate first/last name fields
    if (fields.english_first_name && cardData.english_name?.first_name) {
      setFieldValue(fields.english_first_name, cardData.english_name.first_name);
      filled.push('English first name');
    }
    if (fields.english_last_name && cardData.english_name?.last_name) {
      setFieldValue(fields.english_last_name, cardData.english_name.last_name);
      filled.push('English last name');
    }
  }

  // Fill address
  if (fields.address && cardData.address) {
    setFieldValue(fields.address, cardData.address);
    filled.push('Address');
  }

  // Fill date of birth
  if (fields.date_of_birth && cardData.date_of_birth) {
    // Format date based on field type
    let dateValue = cardData.date_of_birth;

    // If it's a date input, use ISO format
    if (fields.date_of_birth.type === 'date') {
      dateValue = cardData.date_of_birth; // Already in YYYY-MM-DD format from API
    }

    setFieldValue(fields.date_of_birth, dateValue);
    filled.push('Date of birth');
  }

  // Show notification
  if (filled.length > 0) {
    showNotification(`Auto-filled ${filled.length} field(s): ${filled.join(', ')}`);
  } else {
    showNotification('No matching fields found to auto-fill', 'warning');
  }

  console.log(`Auto-fill complete. Filled fields:`, filled);
}

/**
 * Set value of a form field
 */
function setFieldValue(field, value) {
  // Set the value
  field.value = value;

  // Trigger events to ensure the change is detected by the page's JavaScript
  field.dispatchEvent(new Event('input', { bubbles: true }));
  field.dispatchEvent(new Event('change', { bubbles: true }));
  field.dispatchEvent(new Event('blur', { bubbles: true }));

  // Highlight the field briefly
  highlightField(field);
}

/**
 * Highlight a field to show it was auto-filled
 */
function highlightField(field) {
  const originalBorder = field.style.border;
  const originalBackground = field.style.backgroundColor;

  field.style.border = '2px solid #4CAF50';
  field.style.backgroundColor = '#E8F5E9';

  setTimeout(() => {
    field.style.border = originalBorder;
    field.style.backgroundColor = originalBackground;
  }, 2000);
}

/**
 * Show a notification on the page
 */
function showNotification(message, type = 'success') {
  // Remove existing notification
  const existing = document.getElementById('thai-id-card-notification');
  if (existing) {
    existing.remove();
  }

  // Create notification element
  const notification = document.createElement('div');
  notification.id = 'thai-id-card-notification';
  notification.textContent = message;

  // Style based on type
  const colors = {
    success: { bg: '#4CAF50', text: 'white' },
    warning: { bg: '#FFC107', text: 'black' },
    error: { bg: '#F44336', text: 'white' },
  };

  const color = colors[type] || colors.success;

  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${color.bg};
    color: ${color.text};
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    max-width: 400px;
    animation: slideIn 0.3s ease-out;
  `;

  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);

  // Add to page
  document.body.appendChild(notification);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    notification.style.animation = 'slideIn 0.3s ease-out reverse';
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 5000);
}

/**
 * Listen for messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message.type);

  if (message.type === 'auto_fill' && message.data) {
    autoFillForm(message.data);
    sendResponse({ success: true });
  }

  return true;
});

// Log when script is ready
console.log('Thai ID Card Reader ready for auto-fill on', window.location.href);

// Detect fields on page load (for debugging)
if (window.location.href.includes('peakaccount.com')) {
  setTimeout(() => {
    const fields = detectFormFields();
    console.log('Detected form fields:', fields);
  }, 2000);
}
