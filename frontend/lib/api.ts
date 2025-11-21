/**
 * API client for authentication endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface User {
  username: string;
  email: string;
  full_name?: string;
  disabled: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Login with username and password
 */
export async function login(
  credentials: LoginCredentials
): Promise<AuthTokens> {
  // OAuth2 password flow requires form data
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login failed" }));
    throw new ApiError(response.status, error.detail || "Login failed");
  }

  return response.json();
}

/**
 * Register a new user
 */
export async function register(data: RegisterData): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Registration failed" }));
    throw new ApiError(response.status, error.detail || "Registration failed");
  }

  return response.json();
}

/**
 * Get current user information
 */
export async function getCurrentUser(token: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch user" }));
    throw new ApiError(response.status, error.detail || "Failed to fetch user");
  }

  return response.json();
}

/**
 * Logout (client-side token removal)
 */
export async function logout(): Promise<void> {
  // Since JWT is stateless, we just clear the client-side token
  // Optionally call the server logout endpoint for logging purposes
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
    });
  } catch (error) {
    // Ignore logout endpoint errors
    console.error("Logout endpoint error:", error);
  }
}

/**
 * Chat API Types and Functions (from persistence layer)
 */
export interface Chat {
  id: string;
  account_id: string;
  account_type: string;
  provider_id: string;
  name: string | null;
  timestamp: string | null;
  unread_count: number;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatListResponse {
  items: Chat[];
  total: number;
  limit: number;
  offset: number;
}

export interface ChatFilters {
  is_read?: boolean;
  account_id?: string;
  limit?: number;
  offset?: number;
}

/**
 * Fetch all chats from persistence layer
 */
export async function getChats(filters?: ChatFilters): Promise<ChatListResponse> {
  const params = new URLSearchParams();
  
  if (filters?.is_read !== undefined) {
    params.append('is_read', String(filters.is_read));
  }
  if (filters?.account_id) {
    params.append('account_id', filters.account_id);
  }
  if (filters?.limit) {
    params.append('limit', String(filters.limit));
  }
  if (filters?.offset) {
    params.append('offset', String(filters.offset));
  }

  const url = `${API_BASE_URL}/api/chats${params.toString() ? '?' + params.toString() : ''}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch chats' }));
    throw new ApiError(response.status, error.detail || 'Failed to fetch chats');
  }

  return response.json();
}

/**
 * Mark a chat as read
 */
export async function markChatAsRead(chatId: string): Promise<Chat> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/mark-read`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to mark chat as read' }));
    throw new ApiError(response.status, error.detail || 'Failed to mark chat as read');
  }

  return response.json();
}

/**
 * Attendee API Types
 */
export interface Attendee {
  id: string;
  provider_id: string;
  name: string;
  picture_url: string | null;
  profile_url: string | null;
  is_self: number;
}

/**
 * Get attendee information including profile picture
 */
export async function getChatAttendee(
  chatId: string,
  providerId: string
): Promise<Attendee> {
  const response = await fetch(
    `${API_BASE_URL}/api/chats/${chatId}/attendee/${providerId}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch attendee' }));
    throw new ApiError(response.status, error.detail || 'Failed to fetch attendee');
  }

  return response.json();
}

/**
 * Message API Types and Functions
 */
export interface Reaction {
  value: string;
  sender_id: string;
  is_sender: boolean;
}

export interface Message {
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
  reactions: Reaction[];
  seen: number;
  seen_by: Record<string, any>;
  hidden: number;
  deleted: number;
  edited: number;
  is_event: number;
  delivered: number;
  behavior: number | null;
  original: string;
  quoted?: any;
  event_type?: number;
  replies?: number;
  reply_by?: string[];
  parent?: string;
  subject?: string;
  message_type?: string;
  attendee_type?: string;
  attendee_distance?: number;
  sender_urn?: string;
  reply_to?: any;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
  limit: number;
  offset: number;
}

export interface MessageFilters {
  limit?: number;
  offset?: number;
  order_desc?: boolean;
}

/**
 * Fetch messages from a specific chat (from persistence layer)
 */
export async function getChatMessages(
  chatId: string,
  filters?: MessageFilters
): Promise<MessageListResponse> {
  const params = new URLSearchParams();
  
  if (filters?.limit) {
    params.append('limit', String(filters.limit));
  }
  if (filters?.offset) {
    params.append('offset', String(filters.offset));
  }
  if (filters?.order_desc !== undefined) {
    params.append('order_desc', String(filters.order_desc));
  }

  const url = `${API_BASE_URL}/api/chats/${chatId}/messages${params.toString() ? '?' + params.toString() : ''}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch messages' }));
    throw new ApiError(response.status, error.detail || 'Failed to fetch messages');
  }

  return response.json();
}

export { ApiError };

