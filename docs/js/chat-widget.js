/**
 * Rex Marks The Spot - Feedback Chat Widget
 * Embeddable chat widget for visitor feedback and AI assistance
 */

(function() {
  'use strict';

  // Configuration - update this URL after deploying the worker
  const CONFIG = {
    apiUrl: 'https://feedback-chat.YOUR_SUBDOMAIN.workers.dev',
    // apiUrl: 'http://localhost:8787', // Uncomment for local dev
  };

  // Widget state
  let isOpen = false;
  let isMinimized = false;
  let chatHistory = [];
  let widgetContainer = null;

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    createWidget();
    attachEventListeners();
  }

  function createWidget() {
    // Inject styles
    const styles = document.createElement('style');
    styles.textContent = `
      .rex-chat-widget {
        --rex-primary: #8b5cf6;
        --rex-primary-dark: #7c3aed;
        --rex-bg: #1a1a2e;
        --rex-bg-light: #252542;
        --rex-text: #e2e8f0;
        --rex-text-muted: #94a3b8;
        --rex-border: #3d3d5c;
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }

      .rex-chat-button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--rex-primary), var(--rex-primary-dark));
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
        transition: transform 0.2s, box-shadow 0.2s;
      }

      .rex-chat-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(139, 92, 246, 0.5);
      }

      .rex-chat-button svg {
        width: 28px;
        height: 28px;
        fill: white;
      }

      .rex-chat-button.open .rex-icon-chat { display: none; }
      .rex-chat-button:not(.open) .rex-icon-close { display: none; }

      .rex-chat-window {
        display: none;
        position: absolute;
        bottom: 70px;
        right: 0;
        width: 380px;
        height: 520px;
        background: var(--rex-bg);
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        overflow: hidden;
        flex-direction: column;
        border: 1px solid var(--rex-border);
      }

      .rex-chat-window.open {
        display: flex;
      }

      .rex-chat-header {
        background: linear-gradient(135deg, var(--rex-primary), var(--rex-primary-dark));
        color: white;
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .rex-chat-avatar {
        width: 40px;
        height: 40px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
      }

      .rex-chat-title {
        flex: 1;
      }

      .rex-chat-title h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }

      .rex-chat-title span {
        font-size: 12px;
        opacity: 0.8;
      }

      .rex-chat-tabs {
        display: flex;
        background: var(--rex-bg-light);
        border-bottom: 1px solid var(--rex-border);
      }

      .rex-chat-tab {
        flex: 1;
        padding: 12px;
        background: none;
        border: none;
        color: var(--rex-text-muted);
        cursor: pointer;
        font-size: 14px;
        transition: color 0.2s, border-color 0.2s;
        border-bottom: 2px solid transparent;
      }

      .rex-chat-tab:hover {
        color: var(--rex-text);
      }

      .rex-chat-tab.active {
        color: var(--rex-primary);
        border-bottom-color: var(--rex-primary);
      }

      .rex-chat-content {
        flex: 1;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }

      .rex-chat-panel {
        display: none;
        flex-direction: column;
        height: 100%;
      }

      .rex-chat-panel.active {
        display: flex;
      }

      .rex-chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .rex-message {
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.4;
      }

      .rex-message.bot {
        align-self: flex-start;
        background: var(--rex-bg-light);
        color: var(--rex-text);
        border-bottom-left-radius: 4px;
      }

      .rex-message.user {
        align-self: flex-end;
        background: var(--rex-primary);
        color: white;
        border-bottom-right-radius: 4px;
      }

      .rex-message.typing {
        display: flex;
        gap: 4px;
        padding: 14px 18px;
      }

      .rex-message.typing span {
        width: 8px;
        height: 8px;
        background: var(--rex-text-muted);
        border-radius: 50%;
        animation: rex-typing 1.4s infinite;
      }

      .rex-message.typing span:nth-child(2) { animation-delay: 0.2s; }
      .rex-message.typing span:nth-child(3) { animation-delay: 0.4s; }

      @keyframes rex-typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-4px); opacity: 1; }
      }

      .rex-chat-input {
        display: flex;
        padding: 12px;
        gap: 8px;
        border-top: 1px solid var(--rex-border);
        background: var(--rex-bg-light);
      }

      .rex-chat-input input,
      .rex-chat-input textarea {
        flex: 1;
        padding: 10px 14px;
        border: 1px solid var(--rex-border);
        border-radius: 20px;
        background: var(--rex-bg);
        color: var(--rex-text);
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s;
        resize: none;
      }

      .rex-chat-input input:focus,
      .rex-chat-input textarea:focus {
        border-color: var(--rex-primary);
      }

      .rex-chat-input button {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--rex-primary);
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
      }

      .rex-chat-input button:hover {
        background: var(--rex-primary-dark);
      }

      .rex-chat-input button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .rex-chat-input button svg {
        width: 18px;
        height: 18px;
        fill: white;
      }

      /* Feedback form */
      .rex-feedback-form {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        overflow-y: auto;
      }

      .rex-form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .rex-form-group label {
        font-size: 13px;
        color: var(--rex-text-muted);
      }

      .rex-form-group input,
      .rex-form-group textarea,
      .rex-form-group select {
        padding: 10px 12px;
        border: 1px solid var(--rex-border);
        border-radius: 8px;
        background: var(--rex-bg-light);
        color: var(--rex-text);
        font-size: 14px;
        outline: none;
      }

      .rex-form-group textarea {
        min-height: 80px;
        resize: vertical;
      }

      .rex-form-group input:focus,
      .rex-form-group textarea:focus,
      .rex-form-group select:focus {
        border-color: var(--rex-primary);
      }

      .rex-submit-btn {
        padding: 12px 20px;
        background: var(--rex-primary);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
      }

      .rex-submit-btn:hover {
        background: var(--rex-primary-dark);
      }

      .rex-submit-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .rex-success-message {
        text-align: center;
        padding: 40px 20px;
        color: var(--rex-text);
      }

      .rex-success-message svg {
        width: 60px;
        height: 60px;
        fill: #10b981;
        margin-bottom: 16px;
      }

      .rex-success-message h4 {
        margin: 0 0 8px;
        font-size: 18px;
      }

      .rex-success-message p {
        margin: 0;
        color: var(--rex-text-muted);
        font-size: 14px;
      }

      @media (max-width: 480px) {
        .rex-chat-window {
          width: calc(100vw - 20px);
          height: calc(100vh - 100px);
          right: 10px;
          bottom: 80px;
        }
      }
    `;
    document.head.appendChild(styles);

    // Create widget HTML
    widgetContainer = document.createElement('div');
    widgetContainer.className = 'rex-chat-widget';
    widgetContainer.innerHTML = `
      <div class="rex-chat-window">
        <div class="rex-chat-header">
          <div class="rex-chat-avatar">🦖</div>
          <div class="rex-chat-title">
            <h3>Rex Assistant</h3>
            <span>Ask about the movie!</span>
          </div>
        </div>

        <div class="rex-chat-tabs">
          <button class="rex-chat-tab active" data-tab="chat">💬 Chat</button>
          <button class="rex-chat-tab" data-tab="feedback">📝 Feedback</button>
        </div>

        <div class="rex-chat-content">
          <!-- Chat Panel -->
          <div class="rex-chat-panel active" data-panel="chat">
            <div class="rex-chat-messages" id="rex-messages">
              <div class="rex-message bot">
                Hi! I'm Rex, your guide to "Fairy Dinosaur Date Night" 🎬 Ask me anything about the movie or leave feedback!
              </div>
            </div>
            <div class="rex-chat-input">
              <input type="text" id="rex-chat-input" placeholder="Type a message..." />
              <button id="rex-send-btn">
                <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
              </button>
            </div>
          </div>

          <!-- Feedback Panel -->
          <div class="rex-chat-panel" data-panel="feedback">
            <form class="rex-feedback-form" id="rex-feedback-form">
              <div class="rex-form-group">
                <label>Name (optional)</label>
                <input type="text" name="name" placeholder="Your name" />
              </div>
              <div class="rex-form-group">
                <label>Email (optional)</label>
                <input type="email" name="email" placeholder="your@email.com" />
              </div>
              <div class="rex-form-group">
                <label>Type</label>
                <select name="type">
                  <option value="general">General Feedback</option>
                  <option value="suggestion">Suggestion</option>
                  <option value="bug">Bug Report</option>
                  <option value="praise">Praise</option>
                </select>
              </div>
              <div class="rex-form-group">
                <label>Message *</label>
                <textarea name="message" placeholder="Tell us what you think..." required></textarea>
              </div>
              <button type="submit" class="rex-submit-btn">Submit Feedback</button>
            </form>
            <div class="rex-success-message" style="display: none;" id="rex-feedback-success">
              <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
              <h4>Thank you!</h4>
              <p>Your feedback has been submitted successfully.</p>
            </div>
          </div>
        </div>
      </div>

      <button class="rex-chat-button" id="rex-toggle-btn">
        <svg class="rex-icon-chat" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
        <svg class="rex-icon-close" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
      </button>
    `;
    document.body.appendChild(widgetContainer);
  }

  function attachEventListeners() {
    // Toggle button
    const toggleBtn = document.getElementById('rex-toggle-btn');
    toggleBtn.addEventListener('click', toggleWidget);

    // Tab switching
    const tabs = widgetContainer.querySelectorAll('.rex-chat-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Chat input
    const chatInput = document.getElementById('rex-chat-input');
    const sendBtn = document.getElementById('rex-send-btn');

    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    sendBtn.addEventListener('click', sendMessage);

    // Feedback form
    const feedbackForm = document.getElementById('rex-feedback-form');
    feedbackForm.addEventListener('submit', submitFeedback);
  }

  function toggleWidget() {
    isOpen = !isOpen;
    const window = widgetContainer.querySelector('.rex-chat-window');
    const btn = document.getElementById('rex-toggle-btn');

    window.classList.toggle('open', isOpen);
    btn.classList.toggle('open', isOpen);

    if (isOpen) {
      document.getElementById('rex-chat-input').focus();
    }
  }

  function switchTab(tabName) {
    // Update tabs
    widgetContainer.querySelectorAll('.rex-chat-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update panels
    widgetContainer.querySelectorAll('.rex-chat-panel').forEach(panel => {
      panel.classList.toggle('active', panel.dataset.panel === tabName);
    });
  }

  async function sendMessage() {
    const input = document.getElementById('rex-chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addMessage(message, 'user');
    input.value = '';
    input.disabled = true;

    // Add to history
    chatHistory.push({ role: 'user', content: message });

    // Show typing indicator
    const messagesContainer = document.getElementById('rex-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'rex-message bot typing';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
      const response = await fetch(`${CONFIG.apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history: chatHistory.slice(-10)
        })
      });

      const data = await response.json();

      // Remove typing indicator
      typingDiv.remove();

      if (data.error) {
        addMessage('Sorry, something went wrong. Please try again.', 'bot');
      } else {
        addMessage(data.response, 'bot');
        chatHistory.push({ role: 'assistant', content: data.response });
      }

    } catch (error) {
      console.error('Chat error:', error);
      typingDiv.remove();
      addMessage('Sorry, I couldn\'t connect. Please try again later.', 'bot');
    }

    input.disabled = false;
    input.focus();
  }

  function addMessage(content, type) {
    const messagesContainer = document.getElementById('rex-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `rex-message ${type}`;
    messageDiv.textContent = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async function submitFeedback(e) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('.rex-submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    const formData = new FormData(form);
    const data = {
      name: formData.get('name'),
      email: formData.get('email'),
      type: formData.get('type'),
      message: formData.get('message'),
      page: window.location.pathname,
      chatHistory: chatHistory
    };

    try {
      const response = await fetch(`${CONFIG.apiUrl}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (result.success) {
        form.style.display = 'none';
        document.getElementById('rex-feedback-success').style.display = 'block';

        // Reset after 3 seconds
        setTimeout(() => {
          form.reset();
          form.style.display = 'flex';
          document.getElementById('rex-feedback-success').style.display = 'none';
          submitBtn.disabled = false;
          submitBtn.textContent = 'Submit Feedback';
        }, 3000);
      } else {
        throw new Error(result.error);
      }

    } catch (error) {
      console.error('Feedback error:', error);
      alert('Failed to submit feedback. Please try again.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Feedback';
    }
  }

  // Expose for external control if needed
  window.RexChat = {
    open: () => { if (!isOpen) toggleWidget(); },
    close: () => { if (isOpen) toggleWidget(); },
    toggle: toggleWidget
  };

})();
