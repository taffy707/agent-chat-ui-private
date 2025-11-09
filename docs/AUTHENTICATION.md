# Authentication

This application uses **Supabase** for frontend authentication, providing secure user sign-up, sign-in, session management, and protected routes.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Features](#features)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Protected Routes](#protected-routes)
- [Google OAuth (Optional)](#google-oauth-optional)
- [Testing Locally](#testing-locally)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)

---

## Overview

The authentication system is implemented entirely on the frontend and includes:

- **Email/Password Authentication**: Users can sign up and sign in with email and password
- **Google OAuth** (optional): Users can sign in with their Google account
- **Session Management**: Automatic session persistence and refresh using Supabase
- **Protected Routes**: Middleware-based route protection that redirects unauthenticated users
- **User Profile Management**: Support for user metadata (first name, last name, company name)

**Important**: This implementation only covers frontend authentication. Backend authentication for LangGraph server or Document API is out of scope.

---

## Setup

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be provisioned
3. Navigate to **Project Settings** > **API** to find your credentials

### 2. Configure Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Update the Supabase configuration in `.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

**Where to find these values:**

- `NEXT_PUBLIC_SUPABASE_URL`: Your project URL from Supabase dashboard
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: The `anon` public key from Project Settings > API

### 3. Configure Authentication in Supabase

1. In your Supabase dashboard, go to **Authentication** > **URL Configuration**
2. Add your site URL to **Site URL**: `http://localhost:3000` (for local development)
3. Add redirect URLs for production if deploying

### 4. (Optional) Enable Google OAuth

If you want to enable Google sign-in:

1. Go to **Authentication** > **Providers** in Supabase
2. Enable the Google provider
3. Add your Google OAuth credentials (Client ID and Secret)
4. Ensure `NEXT_PUBLIC_GOOGLE_AUTH_DISABLED` is NOT set to `"true"` in your `.env.local`

To disable Google OAuth, set:

```bash
NEXT_PUBLIC_GOOGLE_AUTH_DISABLED=true
```

---

## Features

### Sign Up

- Email and password validation
- Password requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
- User metadata collection (first name, last name, company name)
- Email verification (configurable in Supabase)

### Sign In

- Email/password authentication
- Optional Google OAuth
- Session persistence across page reloads
- Automatic session refresh

### Sign Out

- Clears session and redirects to sign-in page
- Can be triggered from any component using `useAuthContext()`
- Available via the user profile menu in the sidebar (bottom of the navigation)

### Protected Routes

- All routes except `/signin` and `/signup` are protected by default
- Unauthenticated users are automatically redirected to `/signin`
- Authenticated users trying to access auth pages are redirected to `/`

---

## Environment Variables

| Variable                           | Required | Description                             |
| ---------------------------------- | -------- | --------------------------------------- |
| `NEXT_PUBLIC_SUPABASE_URL`         | Yes      | Your Supabase project URL               |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`    | Yes      | Your Supabase anonymous (public) key    |
| `NEXT_PUBLIC_GOOGLE_AUTH_DISABLED` | No       | Set to `"true"` to disable Google OAuth |

**Security Notes:**

- Only the `anon` key should be used client-side (it's prefixed with `NEXT_PUBLIC_`)
- Never expose your Supabase `service_role` key in the frontend
- The `anon` key is safe to expose as it's protected by Row Level Security (RLS)

---

## Usage

### User Profile in Navigation

The application includes a user profile section at the bottom of the sidebar navigation. This section displays:

- User's avatar (or initials if no avatar is set)
- User's display name or email
- Dropdown menu with:
  - User information
  - Sign out button (when authenticated)
  - Sign in button (when not authenticated)

To access the user profile menu:

1. Click on your profile section at the bottom of the sidebar
2. Select "Sign out" to log out of your account

### Using the Auth Context

The `useAuthContext` hook provides access to authentication state and methods:

```tsx
import { useAuthContext } from "@/providers/Auth";

function MyComponent() {
  const { user, isAuthenticated, isLoading, signOut } = useAuthContext();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div>Please sign in</div>;
  }

  return (
    <div>
      <p>Welcome, {user?.displayName || user?.email}!</p>
      <button onClick={() => signOut()}>Sign Out</button>
    </div>
  );
}
```

### Available Auth Methods

```tsx
const {
  // State
  user, // Current user object or null
  session, // Current session or null
  isAuthenticated, // Boolean: true if user is signed in
  isLoading, // Boolean: true while loading auth state

  // Methods
  signIn, // (credentials) => Promise
  signUp, // (credentials) => Promise
  signInWithGoogle, // () => Promise
  signOut, // () => Promise
  resetPassword, // (email) => Promise
  updatePassword, // (newPassword) => Promise
  updateUser, // (attributes) => Promise
} = useAuthContext();
```

### User Object Structure

```typescript
interface User {
  id: string;
  email: string | null;
  displayName?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  companyName?: string | null;
  avatarUrl?: string | null;
  metadata?: Record<string, any>;
}
```

---

## Protected Routes

Protected routes are enforced via Next.js middleware in `src/middleware.ts`:

### How It Works

1. **Middleware runs on every request** (except static files and images)
2. **Checks for valid session** using Supabase server-side client
3. **Redirects unauthenticated users** to `/signin`
4. **Redirects authenticated users** away from `/signin` and `/signup`

### Customizing Protected Routes

To modify which routes require authentication, edit `src/lib/auth/middleware.ts`:

```typescript
const NO_AUTH_PATHS = ["/signin", "/signup", "/your-public-route"];
```

---

## Google OAuth (Optional)

### Enabling Google OAuth

1. **Set up Google OAuth in Supabase:**

   - Go to Authentication > Providers
   - Enable Google
   - Enter your Google Client ID and Secret

2. **Configure in your app:**

   - Ensure `NEXT_PUBLIC_GOOGLE_AUTH_DISABLED` is NOT set or set to `"false"`

3. **Set redirect URL in Google Console:**
   - Add `https://your-project.supabase.co/auth/v1/callback` to authorized redirect URIs

### Disabling Google OAuth

Set in `.env.local`:

```bash
NEXT_PUBLIC_GOOGLE_AUTH_DISABLED=true
```

This will hide the "Sign in with Google" button on auth pages.

---

## Testing Locally

### 1. Start the development server

```bash
pnpm dev
```

### 2. Test Sign Up

1. Navigate to `http://localhost:3000/signup`
2. Fill in the form with test data
3. Submit the form
4. Check your email for verification (if enabled in Supabase)

### 3. Test Sign In

1. Navigate to `http://localhost:3000/signin`
2. Enter your credentials
3. You should be redirected to the home page

### 4. Test Protected Routes

1. Sign out
2. Try to access `http://localhost:3000/`
3. You should be redirected to `/signin`

### 5. Test Session Persistence

1. Sign in
2. Refresh the page
3. You should remain signed in

---

## Security Notes

### Client-Side Security

- **Never expose service role keys**: Only use the `anon` key client-side
- **Use HTTPS in production**: Always use HTTPS for authentication in production
- **Configure CORS properly**: Ensure your Supabase project has the correct CORS settings

### Password Security

- Passwords are validated on the client for UX
- Passwords are hashed by Supabase server-side using bcrypt
- Password requirements are enforced in the signup form

### Session Security

- Sessions are stored in HTTP-only cookies (via Supabase SSR)
- Sessions automatically refresh before expiration
- Sessions are validated on every protected route request

### Row Level Security (RLS)

- Consider enabling RLS policies in Supabase for any database tables you create
- The `anon` key is safe to expose because of RLS policies

---

## Troubleshooting

### "Missing Supabase configuration" Error

**Problem**: Missing or incorrect environment variables

**Solution**:

1. Ensure `.env.local` exists and contains valid values
2. Restart your development server after changing environment variables
3. Verify the values in your Supabase dashboard

### Redirected to `/signin` Even After Signing In

**Problem**: Session not persisting

**Solution**:

1. Check browser console for errors
2. Ensure cookies are enabled in your browser
3. Verify your Supabase URL and keys are correct
4. Clear browser cookies and try again

### Google OAuth Not Working

**Problem**: Google sign-in button not appearing or failing

**Solution**:

1. Verify `NEXT_PUBLIC_GOOGLE_AUTH_DISABLED` is not set to `"true"`
2. Ensure Google OAuth is enabled in Supabase
3. Check that redirect URLs are properly configured in Google Console
4. Verify your domain is added to Supabase's allowed redirect URLs

### Email Confirmation Not Arriving

**Problem**: Users not receiving confirmation emails

**Solution**:

1. Check spam/junk folder
2. In Supabase dashboard, go to Authentication > Email Templates
3. For development, disable email confirmation: Authentication > Providers > Email > Enable email confirmations (toggle off)

### TypeScript Errors

**Problem**: Type errors when using `useAuthContext`

**Solution**:

- Ensure you're using the hook inside a component wrapped by `AuthProvider`
- Check that you've imported the types correctly
- Restart your TypeScript server in your editor

---

## Architecture

### File Structure

```
src/
├── lib/auth/
│   ├── types.ts              # TypeScript types and interfaces
│   ├── supabase-client.ts    # Supabase client singleton
│   ├── supabase.ts           # SupabaseAuthProvider implementation
│   └── middleware.ts         # Auth middleware logic
├── providers/
│   └── Auth.tsx              # AuthProvider React context
├── app/(auth)/
│   ├── signin/page.tsx       # Sign in page
│   └── signup/page.tsx       # Sign up page
├── components/
│   ├── thread/sidebar/
│   │   ├── index.tsx         # Main sidebar component
│   │   └── nav-user.tsx      # User profile navigation component
│   └── ui/
│       ├── password-input.tsx    # Password input with show/hide toggle
│       └── alert.tsx             # Alert component for messages
└── middleware.ts             # Next.js middleware entry point
```

### Provider Hierarchy

The AuthProvider is integrated into the root layout:

```
RootLayout
  └── NuqsAdapter
      └── AuthProvider
          └── {children}
```

---

## Future Enhancements

Potential improvements that could be added:

- **Password Reset Flow**: Implement forgot password functionality
- **Email Verification UI**: Custom email verification landing page
- **Social Login**: Add GitHub, Twitter, or other OAuth providers
- **Two-Factor Authentication**: Add 2FA support
- **Session Management UI**: Show active sessions and allow revocation
- **User Profile Page**: Full user profile editing
- **Backend Integration**: Secure JWT-based authentication for LangGraph/Document API

---

## Support

For issues or questions:

1. Check the [Supabase Documentation](https://supabase.com/docs/guides/auth)
2. Review the [troubleshooting section](#troubleshooting) above
3. Open an issue in the project repository

---

## License

This authentication implementation follows the same license as the main project.
