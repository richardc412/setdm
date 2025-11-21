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

export { ApiError };

