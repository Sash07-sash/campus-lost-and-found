/**
 * Campus Lost & Found - Interactive Frontend Utilities & AI Assistant
 */

// Helper to get CSRF cookie for AJAX requests
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Session ID for MongoDB conversation grouping
function getAiSessionId() {
  let sessId = sessionStorage.getItem('campus_ai_session_id');
  if (!sessId) {
    sessId = 'sess_' + Math.random().toString(36).substring(2, 12);
    sessionStorage.setItem('campus_ai_session_id', sessId);
  }
  return sessId;
}

// 1. Toggle AI Assistant Floating Chat Window
function toggleAssistantWidget() {
  const chatWindow = document.getElementById('aiChatWindow');
  if (chatWindow) {
    chatWindow.classList.toggle('d-none');
    if (!chatWindow.classList.contains('d-none')) {
      const input = document.getElementById('aiChatInput');
      if (input) input.focus();
      scrollChatToBottom();
    }
  }
}

// 2. Open Assistant with prefilled Error Code query
function openAssistantWithError(errorCode) {
  const chatWindow = document.getElementById('aiChatWindow');
  if (chatWindow && chatWindow.classList.contains('d-none')) {
    toggleAssistantWidget();
  }
  askAssistantQuestion(`What does error ${errorCode} mean and how can I resolve it on campus?`);
}

// 3. Ask Assistant question from chip or button
function askAssistantQuestion(questionText) {
  const chatWindow = document.getElementById('aiChatWindow');
  if (chatWindow && chatWindow.classList.contains('d-none')) {
    toggleAssistantWidget();
  }
  sendChatMessage(questionText);
}

// 4. Handle Chat form submit
function handleAssistantSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('aiChatInput');
  const message = input.value.trim();
  if (message) {
    sendChatMessage(message);
    input.value = '';
  }
}

// 5. Send message to /api/chat/ (MongoDB logged)
function sendChatMessage(message) {
  const chatBody = document.getElementById('aiChatBody');
  if (!chatBody) return;

  // Append user bubble
  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble chat-bubble-user';
  userBubble.textContent = message;
  chatBody.appendChild(userBubble);

  // Typing indicator bubble
  const typingBubble = document.createElement('div');
  typingBubble.className = 'chat-bubble chat-bubble-ai';
  typingBubble.id = 'aiTypingIndicator';
  typingBubble.innerHTML = '<span class="spinner-border spinner-border-sm text-primary me-2"></span> Searching SQL FAQs & error records...';
  chatBody.appendChild(typingBubble);
  scrollChatToBottom();

  const sessionId = getAiSessionId();

  fetch('/api/chat/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken') || ''
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId
    })
  })
  .then(res => res.json())
  .then(data => {
    // Remove typing indicator
    const indicator = document.getElementById('aiTypingIndicator');
    if (indicator) indicator.remove();

    // Create AI response bubble
    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-bubble chat-bubble-ai';

    let formattedAnswer = (data.answer || 'I am ready to help.')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');

    aiBubble.innerHTML = formattedAnswer;

    // If AI couldn't answer or offers a ticket, add 1-click button
    if (data.can_create_ticket) {
      const ticketBtn = document.createElement('div');
      ticketBtn.className = 'mt-2 pt-2 border-top';
      const errorCodeParam = data.error_code ? `&error=${encodeURIComponent(data.error_code)}` : '';
      ticketBtn.innerHTML = `
        <a href="/support/?session_id=${encodeURIComponent(sessionId)}${errorCodeParam}" class="btn btn-danger btn-sm fw-bold w-100" style="font-size: 0.8rem;">
          <i class="bi bi-ticket-perforated me-1"></i> Open Official Support Ticket
        </a>
      `;
      aiBubble.appendChild(ticketBtn);
    }

    chatBody.appendChild(aiBubble);
    scrollChatToBottom();
  })
  .catch(err => {
    console.error('Chat API Error:', err);
    const indicator = document.getElementById('aiTypingIndicator');
    if (indicator) indicator.remove();

    const errBubble = document.createElement('div');
    errBubble.className = 'chat-bubble chat-bubble-ai text-danger';
    errBubble.textContent = 'Temporary connection error. You can submit a support ticket via the Support Center.';
    chatBody.appendChild(errBubble);
    scrollChatToBottom();
  });
}

function scrollChatToBottom() {
  const chatBody = document.getElementById('aiChatBody');
  if (chatBody) {
    chatBody.scrollTop = chatBody.scrollHeight;
  }
}

// 6. Feedback Modal & MongoDB submission
function openFeedbackModal() {
  const modalEl = document.getElementById('aiFeedbackModal');
  if (modalEl && typeof bootstrap !== 'undefined') {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}

function handleFeedbackSubmit(e) {
  e.preventDefault();
  const rating = document.getElementById('feedbackRating').value;
  const comment = document.getElementById('feedbackComment').value.trim();
  const sessionId = getAiSessionId();

  fetch('/api/chat/feedback/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken') || ''
    },
    body: JSON.stringify({
      session_id: sessionId,
      rating: parseInt(rating),
      comment: comment
    })
  })
  .then(res => res.json())
  .then(data => {
    const modalEl = document.getElementById('aiFeedbackModal');
    if (modalEl) {
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }
    alert('Thank you! Your feedback rating has been stored in MongoDB.');
  })
  .catch(err => {
    console.error('Feedback submit error:', err);
    alert('Thank you! Feedback received.');
  });
}

// DOM Initialization
document.addEventListener('DOMContentLoaded', function () {
  // Initialize Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Auto-dismiss Alert banners after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert.alert-dismissible');
  autoAlerts.forEach(function (alertEl) {
    setTimeout(function () {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
        bsAlert.close();
      } catch (e) {}
    }, 6000);
  });

  // Image Upload Preview & File Size Checker
  const imageInput = document.getElementById('id_image');
  if (imageInput) {
    imageInput.addEventListener('change', function (e) {
      const file = this.files[0];
      const previewContainer = document.getElementById('image-preview-container');
      const previewImg = document.getElementById('image-preview');

      if (file) {
        if (file.size > 5 * 1024 * 1024) {
          alert('Warning: File size exceeds 5MB limit. Please select a smaller photo (Error CLF-1001).');
          this.value = '';
          if (previewContainer) previewContainer.classList.add('d-none');
          return;
        }

        if (previewImg && previewContainer) {
          const reader = new FileReader();
          reader.onload = function (event) {
            previewImg.src = event.target.result;
            previewContainer.classList.remove('d-none');
          };
          reader.readAsDataURL(file);
        }
      }
    });
  }

  // Dashboard Chart.js
  const chartCanvas = document.getElementById('campusStatsChart');
  if (chartCanvas && typeof Chart !== 'undefined') {
    const rawLabels = chartCanvas.getAttribute('data-labels');
    const rawCounts = chartCanvas.getAttribute('data-counts');

    let labels = [];
    let counts = [];

    try {
      labels = JSON.parse(rawLabels || '[]');
      counts = JSON.parse(rawCounts || '[]');
    } catch (e) {
      console.warn('Error parsing chart data', e);
    }

    if (labels.length > 0 && counts.length > 0) {
      new Chart(chartCanvas, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: counts,
            backgroundColor: [
              '#2563eb', '#0d9488', '#f59e0b', '#8b5cf6', '#ec4899', '#64748b'
            ],
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                boxWidth: 12,
                padding: 15,
                font: { family: 'Plus Jakarta Sans', size: 12 }
              }
            }
          },
          cutout: '65%'
        }
      });
    }
  }
});
