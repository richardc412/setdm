# Authentication Setup

This document describes the authentication system implemented in the SetDM frontend.

## Overview

The frontend uses JWT-based authentication with OAuth2 password flow, connecting to the FastAPI backend.

## Architecture

### Files Created

```
frontend/
├── lib/
│   └── api.ts                      # API client for auth endpoints
├── contexts/
│   └── AuthContext.tsx             # Auth context provider & hooks
├── components/
│   └── ProtectedRoute.tsx          # Protected route wrapper
└── app/
    ├── layout.tsx                  # Updated with AuthProvider
    ├── page.tsx                    # Home page (redirects)
    ├── login/
    │   └── page.tsx               # Login page
    ├── register/
    │   └── page.tsx               # Registration page
    └── dashboard/
        └── page.tsx               # Protected dashboard
```

## Features

### 1. Authentication API (`lib/api.ts`)

- **`login(credentials)`**: Authenticate user and get JWT token
- **`register(data)`**: Register new user
- **`getCurrentUser(token)`**: Fetch current user info
- **`logout()`**: Client-side logout

### 2. Auth Context (`contexts/AuthContext.tsx`)

Global authentication state management with:

- `user`: Current user object
- `token`: JWT access token
- `loading`: Loading state
- `isAuthenticated`: Boolean authentication status
- `login()`: Login function
- `register()`: Registration function
- `logout()`: Logout function

### 3. Protected Routes (`components/ProtectedRoute.tsx`)

Wrapper component that:

- Checks authentication status
- Redirects to `/login` if not authenticated
- Shows loading spinner during auth check

## Usage

### Using Auth Context

```tsx
import { useAuth } from "@/contexts/AuthContext";

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  return (
    <div>
      <p>Welcome, {user?.username}!</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Creating Protected Pages

```tsx
import ProtectedRoute from "@/components/ProtectedRoute";

export default function MyProtectedPage() {
  return <ProtectedRoute>{/* Your page content */}</ProtectedRoute>;
}
```

### Making Authenticated API Calls

```tsx
import { useAuth } from "@/contexts/AuthContext";

function MyComponent() {
  const { token } = useAuth();

  const fetchData = async () => {
    const response = await fetch("http://localhost:8000/api/data", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.json();
  };

  // ...
}
```

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Demo Credentials

The backend has pre-loaded demo users:

- **Username**: `demo` / **Password**: `demo123`
- **Username**: `admin` / **Password**: `admin123`

## Authentication Flow

### Login Flow

1. User enters credentials on `/login`
2. Frontend sends POST to `/auth/login` (OAuth2 form data)
3. Backend validates and returns JWT token
4. Token stored in localStorage
5. User data fetched with token
6. Redirect to `/dashboard`

### Registration Flow

1. User enters details on `/register`
2. Frontend sends POST to `/auth/register`
3. Backend creates user
4. Auto-login with new credentials
5. Redirect to `/dashboard`

### Protected Page Access

1. Component wrapped in `<ProtectedRoute>`
2. Auth context checks for valid token
3. If no token → redirect to `/login`
4. If token exists → fetch user data
5. If token invalid → clear and redirect to `/login`
6. If valid → render page

### Logout Flow

1. User clicks logout
2. Frontend calls `/auth/logout` (optional)
3. Clear token from localStorage
4. Clear user state
5. Redirect to `/login`

## Security Considerations

### Token Storage

- Tokens stored in `localStorage`
- Consider `httpOnly` cookies for production
- Tokens expire after 30 minutes (backend config)

### CORS

Make sure backend allows frontend origin:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Token Refresh

Current implementation doesn't include refresh tokens. For production:

- Implement refresh token flow
- Add token renewal before expiration
- Handle 401 errors globally

## Running the Application

### Start Backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

Frontend runs on `http://localhost:3000`

### Access

1. Navigate to `http://localhost:3000`
2. You'll be redirected to `/login`
3. Login with demo credentials
4. View your dashboard at `/dashboard`

## API Endpoints

### Backend Auth Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (OAuth2 form data)
- `GET /auth/me` - Get current user (requires auth)
- `POST /auth/logout` - Logout (placeholder)

### Testing with cURL

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo123"

# Get current user
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Troubleshooting

### "Failed to fetch user" error

- Check backend is running on port 8000
- Verify CORS is configured correctly
- Check browser console for network errors

### Redirect loop

- Clear localStorage: `localStorage.clear()`
- Check token expiration
- Verify backend auth endpoints are working

### TypeScript errors

- Run `npm run build` to check for type errors
- Ensure all dependencies are installed
- Check `tsconfig.json` paths configuration

## Next Steps

For production deployment:

1. Use environment-specific API URLs
2. Implement refresh token flow
3. Add rate limiting on backend
4. Use secure, httpOnly cookies
5. Add CSRF protection
6. Implement MFA (optional)
7. Add password reset flow
8. Add email verification
