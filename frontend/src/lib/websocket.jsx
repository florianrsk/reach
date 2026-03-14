/**
 * WebSocket client for real-time notifications.
 * Manages connection to backend WebSocket endpoint and handles notifications.
 */

import { toast } from 'sonner';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const WS_URL = BACKEND_URL.replace('http', 'ws');

class WebSocketClient {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.isConnecting = false;
    this.messageHandlers = new Set();
    this.connectionHandlers = new Set();
    this.userId = null;
    this.accessToken = null;
  }

  /**
   * Initialize WebSocket connection with user authentication.
   * @param {string} accessToken - JWT access token for authentication
   * @param {string} userId - User ID for connection management
   */
  connect(accessToken, userId) {
    if (this.isConnecting || this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.accessToken = accessToken;
    this.userId = userId;
    this.isConnecting = true;

    try {
      // Construct WebSocket URL with authentication token
      const wsUrl = `${WS_URL}/api/ws?token=${encodeURIComponent(accessToken)}`;
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => this.handleOpen();
      this.socket.onmessage = (event) => this.handleMessage(event);
      this.socket.onclose = (event) => this.handleClose(event);
      this.socket.onerror = (error) => this.handleError(error);

    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket connection opened.
   */
  handleOpen() {
    console.log('WebSocket connected');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;

    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(true));

    // Send initial subscription message
    this.send({
      type: 'subscribe',
      channels: ['new_attempts', 'attempt_decisions', 'stats_updates']
    });
  }

  /**
   * Handle incoming WebSocket messages.
   * @param {MessageEvent} event - WebSocket message event
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      // Handle ping/pong
      if (data.type === 'ping') {
        this.send({ type: 'pong' });
        return;
      }

      // Notify all message handlers
      this.messageHandlers.forEach(handler => handler(data));

      // Handle specific notification types
      this.handleNotification(data);

    } catch (error) {
      console.error('Error parsing WebSocket message:', error, event.data);
    }
  }

  /**
   * Handle specific notification types and show UI updates.
   * @param {object} data - Notification data
   */
  handleNotification(data) {
    switch (data.type) {
      case 'new_attempt':
        this.handleNewAttemptNotification(data);
        break;
      
      case 'attempt_decision':
        this.handleDecisionNotification(data);
        break;
      
      case 'stats_update':
        this.handleStatsUpdateNotification(data);
        break;
      
      case 'connection_established':
        console.log('WebSocket connection established:', data.message);
        break;
      
      case 'error':
        console.error('WebSocket error:', data.message);
        break;
      
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  /**
   * Handle new reach attempt notification.
   * @param {object} data - Notification data with attempt details
   */
  handleNewAttemptNotification(data) {
    const { attempt, message } = data;
    const senderName = attempt.sender_email || 'Anonymous';
    
    // Show toast notification
    toast.info(message || `New request from ${senderName}`, {
      duration: 5000,
      action: {
        label: 'View',
        onClick: () => {
          // Navigate to attempts page
          window.location.href = '/attempts';
        }
      }
    });

    // Dispatch custom event for badge updates
    window.dispatchEvent(new CustomEvent('new-attempt', { detail: data }));
  }

  /**
   * Handle attempt decision notification.
   * @param {object} data - Notification data with decision details
   */
  handleDecisionNotification(data) {
    const { decision, message } = data;
    
    // Show toast notification for important decisions
    if (decision === 'deliver_to_human') {
      toast.success('Request approved and delivered', {
        duration: 3000
      });
    } else if (decision === 'reject') {
      toast.info('Request rejected', {
        duration: 3000
      });
    }

    // Dispatch custom event for UI updates
    window.dispatchEvent(new CustomEvent('attempt-decision', { detail: data }));
  }

  /**
   * Handle stats update notification.
   * @param {object} data - Notification data with updated stats
   */
  handleStatsUpdateNotification(data) {
    // Dispatch custom event for stats updates
    window.dispatchEvent(new CustomEvent('stats-update', { detail: data }));
  }

  /**
   * Handle WebSocket connection closed.
   * @param {CloseEvent} event - WebSocket close event
   */
  handleClose(event) {
    console.log(`WebSocket disconnected: ${event.code} ${event.reason}`);
    this.isConnecting = false;
    
    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(false));

    // Schedule reconnection if not a normal closure
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket error.
   * @param {Event} error - WebSocket error event
   */
  handleError(error) {
    console.error('WebSocket error:', error);
    this.isConnecting = false;
  }

  /**
   * Schedule reconnection attempt with exponential backoff.
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    
    // Exponential backoff with jitter
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    const jitter = Math.random() * 1000;
    const totalDelay = Math.min(delay + jitter, 30000); // Max 30 seconds

    console.log(`Scheduling reconnection in ${Math.round(totalDelay / 1000)} seconds (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (this.accessToken && this.userId) {
        this.connect(this.accessToken, this.userId);
      }
    }, totalDelay);
  }

  /**
   * Send data through WebSocket.
   * @param {object} data - Data to send
   */
  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify(data));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    }
  }

  /**
   * Close WebSocket connection.
   */
  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'User initiated disconnect');
      this.socket = null;
    }
    this.isConnecting = false;
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
    
    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler(false));
  }

  /**
   * Add message handler.
   * @param {function} handler - Function to handle incoming messages
   */
  addMessageHandler(handler) {
    this.messageHandlers.add(handler);
  }

  /**
   * Remove message handler.
   * @param {function} handler - Handler function to remove
   */
  removeMessageHandler(handler) {
    this.messageHandlers.delete(handler);
  }

  /**
   * Add connection status handler.
   * @param {function} handler - Function to handle connection status changes
   */
  addConnectionHandler(handler) {
    this.connectionHandlers.add(handler);
  }

  /**
   * Remove connection status handler.
   * @param {function} handler - Handler function to remove
   */
  removeConnectionHandler(handler) {
    this.connectionHandlers.delete(handler);
  }

  /**
   * Get current connection status.
   * @returns {string} Connection status
   */
  getStatus() {
    if (!this.socket) return 'disconnected';
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }

  /**
   * Check if WebSocket is connected.
   * @returns {boolean} True if connected
   */
  isConnected() {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
const websocketClient = new WebSocketClient();

export default websocketClient;