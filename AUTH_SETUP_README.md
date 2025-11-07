# Supabase Auth Setup Instructions

## ✅ What's Been Implemented

Your React app now has:
- ✅ Email + password authentication
- ✅ Sign-in, sign-up, and password reset pages
- ✅ Protected `/app` route (requires authentication)
- ✅ User profile avatar with initials in header
- ✅ Welcome message: "Welcome [Username], Let's get started..."
- ✅ Logout button in header
- ✅ Session persistence across page reloads
- ✅ Auth callback handler for email confirmations

## 🚀 Setup Steps

### 1. Run SQL in Supabase

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Open the file `supabase_profiles_setup.sql` (in the project root)
4. Copy and paste the entire SQL script
5. Click **Run** to create the `profiles` table and RLS policies

### 2. Configure Supabase Auth Settings

1. In Supabase Dashboard, go to **Authentication → URL Configuration**
2. Set the following:
   - **Site URL**: `http://localhost:5173` (for development)
   - **Additional Redirect URLs**: Add these:
     - `http://localhost:5173/auth/callback`
     - `http://localhost:5173/reset-password`

3. In **Authentication → Email Templates**:
   - Verify that confirmation emails redirect to `/auth/callback`
   - Default templates should work fine

### 3. Environment Variables

Your `frontend/.env` file should already have:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://elraxlbwaxyyytczyplo.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_APP_URL=http://localhost:5173
```

✅ **Already configured!**

### 4. Install Dependencies

```bash
cd frontend
npm install
```

### 5. Start the Application

**Terminal 1 - Backend (FastAPI):**
```bash
python -m uvicorn server:app --reload --port 8000
```

**Terminal 2 - Frontend (React + Vite):**
```bash
cd frontend
npm run dev
```

Open: http://localhost:5173

## 🎯 How It Works

### User Flow

1. **Sign Up** (`/sign-up`):
   - User enters username, email, password
   - Username is stored in `user_metadata.username`
   - Confirmation email sent
   - After email confirmation → redirects to `/auth/callback` → lands on `/app`

2. **Sign In** (`/sign-in`):
   - User enters email + password
   - Redirects to `/app` on success
   - Welcome message shows: "Welcome [Username], Let's get started..."
   - Avatar shows first 2 letters of username (uppercase)

3. **Password Reset** (`/reset-password`):
   - **Request mode**: User enters email → receives reset link
   - **Update mode**: User clicks link → sets new password → redirects to sign-in

4. **Protected App** (`/app`):
   - Cannot access without authentication
   - Session persists across reloads
   - Logout button in header signs user out and redirects to `/sign-in`

### Header Features

- **Left**: App logo and title
- **Right**:
  - Welcome message: "Welcome Prajwal, Let's get started..."
  - Avatar circle with initials (e.g., "PR")
  - Logout button (hover to see tooltip)

## 🔧 Technical Details

### Files Added

- `frontend/src/lib/supabase.ts` - Supabase client
- `frontend/src/auth/AuthContext.tsx` - Auth state management
- `frontend/src/auth/ProtectedRoute.tsx` - Route guard
- `frontend/src/pages/SignIn.tsx` - Sign-in page
- `frontend/src/pages/SignUp.tsx` - Sign-up page
- `frontend/src/pages/ResetPassword.tsx` - Password reset (request + update)
- `frontend/src/pages/AuthCallback.tsx` - Email confirmation handler

### Files Modified

- `frontend/src/main.tsx` - Added routing with `BrowserRouter`
- `frontend/src/App.tsx` - Added user profile, welcome message, logout button
- `frontend/package.json` - Added `@supabase/supabase-js`, `react-router-dom`

### Database Schema

**Table: `public.profiles`**
- `id` (uuid, PK, FK to `auth.users.id`)
- `username` (text, unique, not null)
- `created_at` (timestamptz, default now())

**RLS Policies:**
- Users can only view, insert, and update their own profile
- Enforced with `auth.uid()` checks

### User Metadata

When a user signs up, their username is stored in:
- `auth.users.raw_user_meta_data.username` (via Supabase Auth)
- `public.profiles.username` (via profile upsert on first login)

The app reads from `user.user_metadata.username` to display in the header.

## 🐛 Troubleshooting

### "Cannot access /app"
- Make sure you're signed in
- Check browser console for errors
- Verify `.env` has correct Supabase URL and anon key

### "Username not showing in header"
- Sign up with a new account (old accounts before this update won't have metadata)
- Or update existing user metadata in Supabase Dashboard

### "Email confirmation link not working"
- Verify redirect URLs are configured in Supabase Auth settings
- Check that `VITE_APP_URL` matches your actual dev URL

### "Logout button not working"
- Check browser console for errors
- Verify Supabase client is initialized correctly

## 🎉 Success Criteria

✅ Cannot access `/app` without valid session  
✅ Sign-up requires email confirmation  
✅ Password reset works end-to-end via email link  
✅ Auth state persists across page reload  
✅ Profile row created on sign-up  
✅ Welcome message shows username  
✅ Avatar shows user initials  
✅ Logout button signs out and redirects  

## 📝 Notes

- **Security**: Row-level security (RLS) is enabled on the profiles table
- **Sessions**: Stored in localStorage, auto-refreshed by Supabase client
- **Email**: Uses Supabase Auth's built-in email service
- **Styling**: Matches your existing UI theme (blue + magenta gradients)

---

**Need help?** Check Supabase Auth docs: https://supabase.com/docs/guides/auth
