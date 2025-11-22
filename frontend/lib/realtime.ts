type EventHandler<T> = (payload: T) => void;

export interface MessageEventPayload {
  object: string;
  id: string;
  account_id: string;
  chat_id: string;
  chat_provider_id: string;
  provider_id: string;
  sender_id: string;
  sender_attendee_id: string;
  text: string | null;
  timestamp: string;
  is_sender: number;
  attachments: any[];
  reactions: any[];
  seen: number;
  seen_by: Record<string, any>;
  hidden: number;
  deleted: number;
  edited: number;
  is_event: number;
  delivered: number;
  behavior: number | null;
  original: string | null;
  quoted?: any;
  reply_to?: any;
  event_type?: number | null;
  replies?: number | null;
  reply_by?: string[] | null;
  parent?: string | null;
  subject?: string | null;
  message_type?: string | null;
  attendee_type?: string | null;
  attendee_distance?: number | null;
  sender_urn?: string | null;
  created_at: string;
}

interface RealtimeEvent<T = unknown> {
  type: string;
  payload: T;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_PATH = process.env.NEXT_PUBLIC_WS_PATH || "/ws/messages";

function buildWsUrl(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const url = new URL(API_BASE_URL);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = WS_PATH.startsWith("/") ? WS_PATH : `/${WS_PATH}`;
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch (error) {
    console.error("Invalid NEXT_PUBLIC_API_URL:", error);
    return null;
  }
}

class RealtimeClient {
  private socket: WebSocket | null = null;
  private listeners = new Map<string, Set<EventHandler<any>>>();
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;
  private manualClose = false;
  private endpoint: string | null = null;

  connect() {
    if (typeof window === "undefined") return;

    if (!this.endpoint) {
      this.endpoint = buildWsUrl();
    }

    if (!this.endpoint) {
      return;
    }

    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this.manualClose = false;
    this.open();
  }

  disconnect() {
    this.manualClose = true;
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  on<T = unknown>(eventType: string, handler: EventHandler<T>) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler as EventHandler<any>);
    this.connect();

    return () => this.off(eventType, handler);
  }

  private off<T>(eventType: string, handler: EventHandler<T>) {
    const handlers = this.listeners.get(eventType);
    if (!handlers) return;
    handlers.delete(handler as EventHandler<any>);
    if (handlers.size === 0) {
      this.listeners.delete(eventType);
    }
  }

  private open() {
    if (!this.endpoint) return;

    this.socket = new WebSocket(this.endpoint);

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const data: RealtimeEvent = JSON.parse(event.data);
        if (!data?.type) {
          return;
        }
        this.emit(data.type, data.payload);
      } catch (error) {
        console.error("Failed to parse realtime payload", error);
      }
    };

    this.socket.onclose = () => {
      this.socket = null;
      if (!this.manualClose) {
        this.scheduleReconnect();
      }
    };

    this.socket.onerror = () => {
      if (this.socket) {
        this.socket.close();
      }
    };
  }

  private scheduleReconnect() {
    if (typeof window === "undefined") return;

    const delay = Math.min(30000, 1000 * 2 ** this.reconnectAttempts);
    this.reconnectAttempts += 1;
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
    }
    this.reconnectTimer = window.setTimeout(() => {
      this.open();
    }, delay);
  }

  private emit<T>(eventType: string, payload: T) {
    const handlers = this.listeners.get(eventType);
    if (!handlers) return;
    handlers.forEach((handler) => {
      try {
        handler(payload);
      } catch (error) {
        console.error("Realtime handler error", error);
      }
    });
  }
}

export const realtimeClient = new RealtimeClient();


