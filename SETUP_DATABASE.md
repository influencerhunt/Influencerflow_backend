# Database Setup for InfluencerFlow

## Setting up the User Profiles Table

The application requires a `user_profiles` table in your Supabase database to store extended user profile information.

### Option 1: Automatic Setup (Recommended)
The table will be created automatically when you first call the profile endpoints. The application will handle this gracefully.

### Option 2: Manual Setup
If you want to create the table manually, run the SQL script in your Supabase SQL editor:

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Run the contents of `create_user_profiles_table.sql`

### Table Structure

The `user_profiles` table includes:

- **Basic Info**: `id`, `email`, `full_name`, `role`, `profile_completed`
- **Profile Data**: `bio`, `location`, `website`, `phone`
- **Social Media**: `social_instagram`, `social_tiktok`, `social_youtube`, `social_twitter`
- **Influencer Fields**: `experience_level`, `content_categories` (JSON)
- **Brand Fields**: `company`, `budget_range`
- **Common Fields**: `interests` (JSON)
- **Timestamps**: `created_at`, `updated_at`

### Row Level Security (RLS)

The table has RLS enabled with policies that ensure:
- Users can only view their own profile
- Users can only update their own profile
- Users can only insert their own profile

### API Endpoints

Once set up, the following endpoints will be available:

- `POST /api/v1/auth/profile` - Update user profile
- `GET /api/v1/auth/me` - Get current user with profile data

### Environment Variables Required

Make sure your backend has these environment variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key  
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Testing the Setup

1. Start your backend server
2. Create a user account via signup
3. Login to get an access token
4. Call the profile endpoint to update profile data
5. Verify the data is stored in Supabase

The profile endpoint accepts all the fields defined in the frontend onboarding form. 