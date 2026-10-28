/**
 * Modern Campus Lost & Found AI Assistant Widget
 * Integrates Google Gemini AI, Campus SQL FAQs, Error Catalog,
 * SQL Support Tickets, and MongoDB Atlas logging & feedback.
 */

(function () {
  if (window.__clf_assistant_loaded) return;
  window.__clf_assistant_loaded = true;

  const SESSION_KEY = 'clf_assistant_session';
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = 'clf_sess_' + Math.random().toString(36).substring(2, 12);
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  // Retrieve Django CSRF Cookie
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
  const csrftoken = getCookie('csrftoken') || '';

  // Ensure DOM container exists
  let container = document.getElementById('fc-widget');
  if (!container) {
    container = document.createElement('div');
    container.id = 'fc-widget';
    document.body.appendChild(container);
  }

  container.innerHTML = `
    <!-- Floating Capsule Launcher -->
    <button class="as-launcher" id="as-launcher-btn" type="button" aria-expanded="false" aria-label="Ask Campus AI Assistant">
      <span class="as-launcher-avatar">
        <span class="ms">auto_awesome</span>
      </span>
      <span class="as-launcher-label">Ask Campus AI</span>
      <span class="as-launcher-dot"></span>
    </button>

    <!-- Main Chat Window Panel -->
    <div class="as-panel" id="as-panel" role="dialog" aria-label="Campus Lost & Found AI Assistant" aria-hidden="true">
      <!-- Header -->
      <div class="as-head">
        <div class="as-head-brand">
          <div class="as-head-avatar">
            <span class="ms">smart_toy</span>
            <span class="as-status-pulse" title="AI Assistant Online"></span>
          </div>
          <div class="as-head-text">
            <div class="as-head-title-row">
              <h2 class="as-head-title">Campus Assistant</h2>
              <span class="as-head-gemini-pill">
                <span class="ms" style="font-size: 14px;">bolt</span> Gemini AI
              </span>
            </div>
            <p class="as-head-sub">Instant answers for lost property, claims &amp; FAQs</p>
          </div>
        </div>
        <button class="as-head-close" id="as-close-btn" type="button" aria-label="Close assistant">
          <span class="ms">close</span>
        </button>
      </div>

      <!-- Messages Body -->
      <div class="as-body" id="as-msg-list" role="log" aria-live="polite">
        <div class="as-empty">
          <div class="as-empty-crest">
            <span class="ms">psychology</span>
          </div>
          <h3 class="as-empty-title">Hi there! How can I help you?</h3>
          <p class="as-empty-desc">I can guide you through reporting lost or found items, verifying ownership claims, campus handover spots, or resolving campus system error codes.</p>
          
          <div class="as-suggest-heading">Popular Questions</div>
          <div class="as-suggest" id="as-suggestions">
            <button type="button" class="as-suggest-chip" data-prompt="How do I report a lost calculator or ID card?">
              <span class="ms">search</span> Report a lost item
            </button>
            <button type="button" class="as-suggest-chip" data-prompt="How do recovery claims and verification work?">
              <span class="ms">verified</span> How claims work
            </button>
            <button type="button" class="as-suggest-chip" data-prompt="Where are campus lost and found security desks located?">
              <span class="ms">location_on</span> Handover desks
            </button>
            <button type="button" class="as-suggest-chip" data-prompt="What does error 404 mean and what should I do?">
              <span class="ms">help_outline</span> Explain error 404
            </button>
          </div>
        </div>
      </div>

      <!-- Footer Input Form -->
      <form class="as-foot" id="as-form">
        <div class="as-input-wrap">
          <input type="text" id="as-input" placeholder="Ask about lost items, claims, or errors…" autocomplete="off" aria-label="Your question" />
        </div>
        <button class="as-send" id="as-send-btn" type="submit" aria-label="Send question">
          <span class="ms">arrow_upward</span>
        </button>
      </form>
    </div>
  `;

  const launcher = document.getElementById('as-launcher-btn');
  const panel = document.getElementById('as-panel');
  const closeBtn = document.getElementById('as-close-btn');
  const msgList = document.getElementById('as-msg-list');
  const form = document.getElementById('as-form');
  const input = document.getElementById('as-input');
  const suggestions = document.getElementById('as-suggestions');

  let isOpen = false;
  let isSending = false;

  function togglePanel(openState) {
    isOpen = typeof openState === 'boolean' ? openState : !isOpen;
    if (isOpen) {
      panel.classList.add('is-active');
      launcher.classList.add('is-open');
      launcher.setAttribute('aria-expanded', 'true');
      panel.setAttribute('aria-hidden', 'false');
      setTimeout(() => input.focus(), 120);
    } else {
      panel.classList.remove('is-active');
      launcher.classList.remove('is-open');
      launcher.setAttribute('aria-expanded', 'false');
      panel.setAttribute('aria-hidden', 'true');
    }
  }

  launcher.addEventListener('click', () => togglePanel());
  closeBtn.addEventListener('click', () => togglePanel(false));

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen) {
      togglePanel(false);
    }
  });

  // Suggestion chips
  if (suggestions) {
    suggestions.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-prompt]');
      if (btn) {
        sendMessage(btn.getAttribute('data-prompt'));
      }
    });
  }

  // Global event triggers (e.g. from error pages or helper buttons)
  window.addEventListener('foley:assistant-open', (ev) => {
    togglePanel(true);
    if (ev.detail && typeof ev.detail === 'string') {
      sendMessage(ev.detail);
    }
  });

  // Handle data-ask buttons across all templates
  document.addEventListener('click', (ev) => {
    const askBtn = ev.target.closest('[data-ask]');
    if (askBtn) {
      const q = askBtn.getAttribute('data-ask');
      togglePanel(true);
      if (q) sendMessage(q);
    }
  });

  // Form Submission
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const txt = input.value.trim();
    if (!txt || isSending) return;
    input.value = '';
    sendMessage(txt);
  });

  function appendUserMessage(text) {
    const empty = msgList.querySelector('.as-empty');
    if (empty) empty.style.display = 'none';

    const div = document.createElement('div');
    div.className = 'as-msg as-msg--user';
    div.textContent = text;
    msgList.appendChild(div);
    msgList.scrollTop = msgList.scrollHeight;
  }

  function appendTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'as-typing';
    div.id = 'as-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    msgList.appendChild(div);
    msgList.scrollTop = msgList.scrollHeight;
  }

  function removeTypingIndicator() {
    const el = document.getElementById('as-typing');
    if (el) el.remove();
  }

  function appendModelResponse(data) {
    const block = document.createElement('div');
    block.className = 'as-block';

    const msg = document.createElement('div');
    msg.className = 'as-msg as-msg--model';

    let raw = data.reply || data.answer || '';
    let geminiModelName = null;

    // Detect Gemini signature: *(Answered by Google Gemini AI - <model>)*
    const geminiMatch = raw.match(/\*\(Answered by Google Gemini AI - (.*?)\)\*/);
    if (geminiMatch) {
      geminiModelName = geminiMatch[1];
      raw = raw.replace(/\*\(Answered by Google Gemini AI - (.*?)\)\*/, '').trim();
    }

    // Format Markdown to clean HTML
    let formatted = raw
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n• /g, '<br>&bull; ')
      .replace(/\n- /g, '<br>&bull; ');

    msg.innerHTML = formatted;

    // If Gemini model detected, append elegant pill badge
    if (geminiModelName) {
      const badge = document.createElement('div');
      badge.className = 'as-gemini-tag';
      badge.innerHTML = `
        <span class="ms">auto_awesome</span>
        <span>Google Gemini AI</span>
        <span class="as-gemini-model">${geminiModelName}</span>
      `;
      msg.appendChild(badge);
    }

    block.appendChild(msg);

    // Verified FAQ notice
    if (data.source === 'faq' || data.matched_faq_id) {
      const notice = document.createElement('div');
      notice.className = 'as-faq-tag';
      notice.innerHTML = '<span class="ms">check_circle</span> Verified Campus FAQ &bull; <a href="/faq/">Browse All</a>';
      block.appendChild(notice);
    }

    // Support Ticket Escalation Card (Styled, elegant, student-friendly)
    if (data.ticket && data.ticket.reference) {
      const ticketCard = document.createElement('div');
      ticketCard.className = 'as-ticket-card';
      ticketCard.innerHTML = `
        <div class="as-ticket-top">
          <div class="as-ticket-badge">
            <span class="ms">confirmation_number</span>
            <span>Campus Support Ticket</span>
          </div>
          <span class="as-ticket-ref">${data.ticket.reference}</span>
        </div>
        <p class="as-ticket-desc">A support ticket has been queued with campus administration.</p>
        ${data.ticket.emailSaved ? 
          '<div class="as-ticket-saved"><span class="ms">check_circle</span> Email saved. Our IT helpdesk will follow up.</div>' : 
          `<form class="as-ticket-row" onsubmit="window.saveTicketEmail(event, '${data.ticket.reference}')">
             <input type="email" id="email-${data.ticket.reference}" placeholder="Your email for updates…" required />
             <button type="submit" class="as-ticket-save-btn">Save</button>
           </form>`
        }
      `;
      block.appendChild(ticketCard);
    }

    // Feedback rating buttons (dual write to MongoDB Atlas)
    const fb = document.createElement('div');
    fb.className = 'as-fb';
    fb.innerHTML = `
      <span class="as-fb-label">Helpful?</span>
      <button type="button" class="as-fb-btn" aria-label="Helpful" onclick="window.submitAssistantFeedback(this, 5)">
        <span class="ms">thumb_up</span> Yes
      </button>
      <button type="button" class="as-fb-btn" aria-label="Not helpful" onclick="window.submitAssistantFeedback(this, 1)">
        <span class="ms">thumb_down</span> No
      </button>
    `;
    block.appendChild(fb);

    msgList.appendChild(block);
    msgList.scrollTop = msgList.scrollHeight;
  }

  async function sendMessage(text) {
    appendUserMessage(text);
    appendTypingIndicator();
    isSending = true;

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionId
        })
      });

      removeTypingIndicator();
      if (!res.ok) {
        throw new Error('Server returned HTTP ' + res.status);
      }
      const data = await res.json();
      appendModelResponse(data);
    } catch (err) {
      removeTypingIndicator();
      const errBlock = document.createElement('div');
      errBlock.className = 'as-block';
      errBlock.innerHTML = `
        <div class="as-msg as-msg--model" style="border-color: #f87171; background: #fff5f5;">
          <strong style="color: #991b1b;">Connection Notice:</strong> The assistant was momentarily unable to connect. You can try asking again or <a href="/support/" style="color: #2e7d32; font-weight: bold; text-decoration: underline;">visit Support</a>.
        </div>
      `;
      msgList.appendChild(errBlock);
    } finally {
      isSending = false;
    }
  }

  // Global helper to save ticket email
  window.saveTicketEmail = async function (e, reference) {
    e.preventDefault();
    const inputEl = document.getElementById('email-' + reference);
    if (!inputEl) return;
    const email = inputEl.value.trim();
    if (!email) return;

    try {
      const res = await fetch('/api/tickets/email/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ reference, email })
      });
      if (res.ok) {
        const formRow = e.target;
        formRow.outerHTML = '<div class="as-ticket-saved"><span class="ms">check_circle</span> Email saved! We will update you at ' + email + '.</div>';
      }
    } catch (err) {
      console.error('Error saving ticket email:', err);
    }
  };

  // Global helper for MongoDB chat feedback
  window.submitAssistantFeedback = async function (btn, rating) {
    const parent = btn.closest('.as-fb');
    parent.querySelectorAll('button').forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');

    try {
      await fetch('/api/chat/feedback/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
          session_id: sessionId,
          rating: rating,
          comment: rating >= 4 ? 'Positive experience' : 'Needs improvement'
        })
      });
      parent.innerHTML = '<span class="as-fb-thanks"><span class="ms">check_circle</span> Thanks for your feedback!</span>';
    } catch (err) {
      console.error('Error recording chat feedback:', err);
    }
  };
})();
