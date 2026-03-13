# User Role Feature Documentation

## Overview
The `role` field has been added to user profiles across the entire backend to support role-based functionality and future authorization features.

## Default Role
- **Default**: `"student"` - All new users are assigned this role by default
- The role can be updated through the profile update endpoint

## Database Schema Changes

### User Document Structure
```javascript
{
  "_id": ObjectId("..."),
  "google_id": "123456789",
  "email": "user@example.com",
  "name": "John Doe",
  "profile_picture": "https://...",
  "role": "student",  // NEW FIELD
  "created_at": ISODate("..."),
  "last_login": ISODate("..."),
  "account_status": "active",
  "preferences": [...],
  "personalization_metadata": {...}
}
```

## Files Modified

### 1. Schemas (`backend/app/api/schemas/`)
- **users.py**:
  - Added `role: str` to `UserProfile` schema
  - Added `role: Optional[str]` to `UserProfileUpdate` schema
  
- **auth.py**:
  - Added `role: str` to `UserInfo` schema

### 2. Database Repository (`backend/app/db/repositories/users_repo.py`)
- Added `role` field to `create_user()` method with default value `"student"`
- Added `"role"` to allowed fields in `update_user_profile()` method

### 3. API Routes
- **auth.py**:
  - Added `role` to JWT token payload during authentication
  - Added `role` to `/auth/me` endpoint response

## API Endpoints

### Get User Profile
```http
GET /api/v1/users/profile
Authorization: Bearer <token>

Response:
{
  "id": "...",
  "email": "...",
  "name": "...",
  "role": "student",
  ...
}
```

### Update User Profile
```http
PUT /api/v1/users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Name",
  "role": "instructor"
}

Response:
{
  "id": "...",
  "email": "...",
  "name": "New Name",
  "role": "instructor",
  ...
}
```

### Get Current User Info
```http
GET /api/v1/auth/me
Authorization: Bearer <token>

Response:
{
  "id": "...",
  "email": "...",
  "name": "...",
  "profile_picture": "...",
  "role": "student"
}
```

## JWT Token

The JWT token now includes the `role` field:
```json
{
  "user_id": "...",
  "email": "...",
  "name": "...",
  "role": "student"
}
```

This allows for quick role-based checks without database queries.

## Migration for Existing Users

If you have existing users in your database, run the migration script to add the `role` field:

```bash
cd backend
python scripts/add_role_to_users.py
```

This script will:
1. Find all users without a `role` field
2. Add the default `"student"` role to those users
3. Verify the migration was successful

## Possible Role Values

While the system currently uses `"student"` as default, you can implement any role-based system you need. Common roles might include:

- `"student"` - Regular student user (default)
- `"instructor"` - Teaching staff
- `"admin"` - System administrator
- `"ta"` - Teaching assistant
- `"guest"` - Guest/temporary access

## Future Enhancements

With the `role` field in place, you can implement:

1. **Role-based Access Control (RBAC)**:
   - Create middleware to check user roles
   - Restrict endpoints based on roles
   
2. **Role-specific Features**:
   - Show different UI elements based on role
   - Enable features only for certain roles
   
3. **Permissions System**:
   - Map roles to specific permissions
   - Fine-grained access control

## Example: Role-based Authorization Decorator

```python
from functools import wraps
from fastapi import HTTPException, status

def require_role(*allowed_roles):
    """Decorator to restrict endpoint access by role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = None, **kwargs):
            user_role = current_user.get("role", "student")
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {allowed_roles}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage:
@router.get("/admin/users")
@require_role("admin", "instructor")
async def get_all_users(current_user: Dict = Depends(get_current_user)):
    # Only admins and instructors can access this
    ...
```

## Testing

To test the role functionality:

1. **Create a new user**: The role should default to `"student"`
2. **Update user role**: Use the profile update endpoint
3. **Check JWT token**: Decode the token to verify role is included
4. **Verify endpoints**: Ensure all user endpoints return the role field

---

**Date Added**: March 6, 2026  
**Version**: 1.0  
**Status**: ✅ Implemented
