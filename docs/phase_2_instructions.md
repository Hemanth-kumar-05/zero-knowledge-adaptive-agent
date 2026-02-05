# Phase 2 Instructions: User Management & Personalization

## Overview
Phase 2 focuses on implementing user authentication, authorization, and personalized chat experiences. This phase builds upon the foundational RAG system from Phase 1 and introduces user-specific features to enhance interaction quality.

---

## Table of Contents
1. [User Management](#1-user-management)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [AI-Powered Dynamic Preferences](#3-ai-powered-dynamic-preferences)
4. [AI Preference Extraction System](#4-ai-preference-extraction-system)
5. [Personalization Limits](#5-personalization-limits)
6. [Database Schema Updates](#6-database-schema-updates)
7. [API Endpoints](#7-api-endpoints)
8. [Implementation Checklist](#8-implementation-checklist)
9. [Practical Examples](#9-practical-examples)

---

## Practical Example Walkthrough

### Scenario: First-Time User Conversation

**User Message 1:**
> "Hi! I'm Hemanth, a third-year CS student. I'm looking for information about the final year project guidelines."

**AI Extraction Process:**
```json
{
  "detected_preferences": [
    {
      "key": "Name",
      "value": "Hemanth",
      "confidence": 0.95,
      "source": "extracted"
    },
    {
      "key": "Year",
      "value": "third-year",
      "confidence": 0.92,
      "source": "extracted"
    },
    {
      "key": "Major",
      "value": "Computer Science",
      "confidence": 0.90,
      "source": "extracted"
    }
  ]
}
```

**System Action:** Stores all 3 preferences in user's preference array.

---

**User Message 2:**
> "Um, hey I would like an elaborate answer with examples if possible. Don't keep it too formal."

**AI Extraction Process:**
```json
{
  "detected_preferences": [
    {
      "key": "Response style",
      "value": "elaborate",
      "confidence": 0.88,
      "source": "extracted"
    },
    {
      "key": "Example inclusion",
      "value": "include examples",
      "confidence": 0.85,
      "source": "extracted"
    },
    {
      "key": "Tone",
      "value": "casual",
      "confidence": 0.80,
      "source": "extracted"
    }
  ]
}
```

**System Action:** Adds these preferences and applies them to the response.

**AI Response (personalized):**
> "Hey Hemanth! Let me walk you through the final year project guidelines in detail.
> 
> The final year project is a comprehensive, semester-long endeavor where you'll apply your CS knowledge to solve a real-world problem. Here's what you need to know:
> 
> **Project Selection (Weeks 1-2)**
> You'll need to choose a project that aligns with your interests. For example, if you're into machine learning, you might build a predictive model for campus resource allocation..."

*(Notice: casual tone, elaborate detail, includes examples, addresses by name)*

---

**User Message 3 (Later in conversation):**
> "Actually, can you make future responses a bit more concise? The elaborate ones are taking too long to read."

**AI Extraction Process:**
```json
{
  "detected_preferences": [
    {
      "key": "Response style",
      "value": "concise",
      "confidence": 0.92,
      "source": "extracted"
    }
  ]
}
```

**System Action:** Detects conflict with existing "Response style: elaborate". Uses higher confidence (0.92 > 0.88) and recency to update the preference.

**Updated Preference Array:**
```json
{
  "preferences": [
    {"key": "Name", "value": "Hemanth", ...},
    {"key": "Year", "value": "third-year", ...},
    {"key": "Major", "value": "Computer Science", ...},
    {"key": "Response style", "value": "concise", "confidence": 0.92, "update_count": 2},
    {"key": "Example inclusion", "value": "include examples", ...},
    {"key": "Tone", "value": "casual", ...}
  ]
}
```

---

## 1. User Management

### Objectives
- Store and manage user profiles
- Track user sessions and chat history
- Maintain user-specific preferences and settings

### Features
- **User Profile Creation**: Automatic profile creation upon first login
- **Profile Information**:
  - User ID (unique identifier)
  - Email (from Google OAuth)
  - Name
  - Profile picture URL
  - Registration date
  - Last login timestamp
  - Account status (active/inactive)

### Database Collections

#### `users` Collection
```json
{
  "_id": "ObjectId",
  "google_id": "string (unique)",
  "email": "string (unique)",
  "name": "string",
  "profile_picture": "string (URL)",
  "created_at": "datetime",
  "last_login": "datetime",
  "account_status": "string (active/inactive)",
  "preferences": [
    {
      "key": "Name",
      "value": "Hemanth",
      "confidence": 0.95,
      "source": "extracted",
      "extracted_from_message": "hi I'm Hemanth. Blah blah blah...",
      "created_at": "datetime",
      "updated_at": "datetime",
      "update_count": 1
    },
    {
      "key": "Response style",
      "value": "elaborate",
      "confidence": 0.88,
      "source": "extracted",
      "extracted_from_message": "I would like a elaborate answer",
      "created_at": "datetime",
      "updated_at": "datetime",
      "update_count": 1
    },
    {
      "key": "Preferred topics",
      "value": "machine learning, data science",
      "confidence": 0.75,
      "source": "inferred",
      "extracted_from_message": null,
      "created_at": "datetime",
      "updated_at": "datetime",
      "update_count": 3
    }
  ],
  "personalization_metadata": {
    "total_interactions": "integer",
    "preference_updates_count": "integer",
    "last_preference_update": "datetime",
    "total_preferences": "integer"
  }
}
```

#### Preference Array Structure
Each preference item contains:
- **key**: The preference category/name (e.g., "Name", "Response style", "Tone")
- **value**: The actual preference value extracted or inferred
- **confidence**: Score (0.0-1.0) indicating how confident the system is about this preference
- **source**: How the preference was obtained:
  - `extracted`: Directly extracted from user message via AI
  - `inferred`: Inferred from user behavior patterns
  - `manual`: User manually set in settings
  - `default`: System default value
- **extracted_from_message**: The original message text where this was found (if applicable)
- **created_at**: When this preference was first added
- **updated_at**: Last modification timestamp
- **update_count**: How many times this preference has been updated

---

## 2. Authentication & Authorization

### Google OAuth 2.0 Integration

#### Implementation Steps
1. **Register Application with Google Cloud Console**
   - Create OAuth 2.0 credentials
   - Configure authorized redirect URIs
   - Obtain Client ID and Client Secret

2. **Backend Dependencies**
   ```
   google-auth
   google-auth-oauthlib
   google-auth-httplib2
   PyJWT
   python-dotenv
   openai  # For GPT-based preference extraction
   anthropic  # Alternative: Claude for preference extraction
   ```
   
   **Note**: For preference extraction, choose one:
   - **OpenAI GPT-4**: Best accuracy, requires API key and costs per request
   - **Anthropic Claude**: Good alternative with similar capabilities
   - **Local LLM**: Free but requires setup (e.g., Ollama with Llama models)

3. **Authentication Flow**
   ```
   User clicks "Sign in with Google"
   ↓
   Redirect to Google OAuth consent screen
   ↓
   User authorizes application
   ↓
   Google redirects back with authorization code
   ↓
   Backend exchanges code for access token
   ↓
   Fetch user info from Google
   ↓
   Create/update user in database
   ↓
   Generate JWT token for session management
   ↓
   Return JWT to frontend
   ```

4. **JWT Token Structure**
   ```json
   {
     "user_id": "string",
     "email": "string",
     "name": "string",
     "exp": "timestamp",
     "iat": "timestamp"
   }
   ```

### Security Measures
- Store Google Client Secret in environment variables
- Use HTTPS for all authentication endpoints
- Implement token refresh mechanism
- Set appropriate token expiration (24 hours recommended)
- Validate tokens on every protected endpoint
- Implement rate limiting on auth endpoints

### Protected Routes
- All chat endpoints require authentication
- Session management endpoints
- User preference endpoints
- Chat history endpoints

---

## 3. AI-Powered Dynamic Preferences

### Overview
Unlike traditional fixed preference categories, this system uses AI to automatically extract and maintain preferences from natural conversation. The agent analyzes every user message to identify and update personalization data dynamically.

### How It Works

#### Automatic Extraction Process
```
User message: "hi I'm Hemanth. Looking forward to chatting!"
           ↓
    AI Preference Extractor
           ↓
Extracted: {key: "Name", value: "Hemanth", confidence: 0.95}
           ↓
    Store in preferences array
```

#### Example Extractions

| User Message | Extracted Preference | Key | Value | Confidence |
|--------------|---------------------|-----|-------|------------|
| "hi I'm Hemanth" | User's name | `Name` | `Hemanth` | 0.95 |
| "I would like an elaborate answer" | Response detail level | `Response style` | `elaborate` | 0.88 |
| "keep it simple please" | Communication style | `Communication style` | `simple` | 0.82 |
| "I prefer bullet points" | Format preference | `Format preference` | `bullet points` | 0.90 |
| "don't be too formal" | Tone preference | `Tone` | `casual` | 0.78 |
| "I'm a CS major" | Academic background | `Major` | `Computer Science` | 0.85 |
| "call me by my first name" | Addressing preference | `Address as` | `first name` | 0.92 |

### Common Preference Categories

While preferences are dynamic, these are common categories the AI extracts:

#### Personal Information
- **Name**: User's name or nickname
- **Preferred name**: How they want to be addressed
- **Major/Department**: Academic field
- **Year**: Academic year (freshman, sophomore, etc.)
- **Role**: Student, faculty, researcher, etc.

#### Communication Style
- **Response style**: elaborate, concise, balanced, detailed, brief
- **Tone**: casual, professional, friendly, formal, academic
- **Communication style**: simple, technical, mixed
- **Formality level**: high, medium, low

#### Format Preferences
- **Format preference**: bullet points, paragraphs, numbered lists, mixed
- **Example inclusion**: include examples, no examples, occasional examples
- **References**: always cite, only when asked, minimal citations

#### Content Preferences
- **Explanation depth**: deep dive, overview, step-by-step
- **Technical level**: beginner-friendly, intermediate, advanced
- **Response length**: short, medium, long
- **Include analogies**: yes, no, sometimes

### User Preference Interface

#### Frontend UI Components
1. **Preference Dashboard**
   - Display all extracted preferences as cards
   - Show confidence score for each preference
   - Show source (extracted/inferred/manual)
   - Allow manual editing or deletion
   - Show original message context on hover

2. **Inline Preference Detection**
   - Real-time detection indicator during chat
   - Subtle notification when new preference is detected
   - Quick confirm/reject action

3. **Manual Override**
   - Add custom preference button
   - Edit existing preference values
   - Set preference priority/importance

---

## 4. AI Preference Extraction System

### Architecture

```
User Message → Preprocessing → LLM Preference Extractor → Validation → Storage
                                         ↓
                              Extract Key-Value Pairs
                              Calculate Confidence
                              Detect Conflicts
```

### Implementation Strategy

#### 1. LLM-Based Extraction

Use a language model (GPT-4, Claude, or fine-tuned model) with a specialized prompt:

```python
class AIPreferenceExtractor:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.min_confidence = 0.70
        self.extraction_prompt = self._build_extraction_prompt()
    
    def _build_extraction_prompt(self):
        return """
        You are a preference extraction system. Analyze the user's message and extract 
        any personal information, communication preferences, or style preferences.
        
        Extract preferences in the following format:
        [
          {"key": "preference_name", "value": "preference_value", "confidence": 0.0-1.0}
        ]
        
        Common preference categories:
        - Personal: Name, Preferred name, Major, Year, Role
        - Style: Response style, Tone, Communication style, Formality level
        - Format: Format preference, Example inclusion, References
        - Content: Explanation depth, Technical level, Response length
        
        Examples:
        - "Hi I'm Hemanth" → {"key": "Name", "value": "Hemanth", "confidence": 0.95}
        - "I would like an elaborate answer" → {"key": "Response style", "value": "elaborate", "confidence": 0.88}
        - "keep responses concise" → {"key": "Response style", "value": "concise", "confidence": 0.90}
        
        Only extract explicit or very clear implicit preferences. 
        Be conservative with confidence scores.
        
        User message: {user_message}
        """
    
    def extract_preferences(self, user_message: str, user_id: str) -> list:
        """
        Extract preferences from user message using LLM
        """
        response = self.llm_client.generate(
            prompt=self.extraction_prompt.format(user_message=user_message),
            temperature=0.3,  # Low temperature for consistency
            response_format="json"
        )
        
        extracted_prefs = json.loads(response)
        
        # Filter by confidence threshold
        valid_prefs = [
            pref for pref in extracted_prefs 
            if pref['confidence'] >= self.min_confidence
        ]
        
        return valid_prefs
    
    def merge_with_existing(self, user_id: str, new_prefs: list) -> list:
        """
        Merge new preferences with existing ones, handling conflicts
        """
        existing_prefs = self.get_user_preferences(user_id)
        
        for new_pref in new_prefs:
            existing_pref = self._find_preference(existing_prefs, new_pref['key'])
            
            if existing_pref:
                # Check if new preference conflicts with existing
                if self._is_conflict(existing_pref, new_pref):
                    # Use confidence score to resolve
                    if new_pref['confidence'] > existing_pref['confidence']:
                        self._update_preference(user_id, new_pref)
                    # Else keep existing
                else:
                    # Update or reinforce existing preference
                    self._update_preference(user_id, new_pref)
            else:
                # Add new preference
                self._add_preference(user_id, new_pref)
        
        return self.get_user_preferences(user_id)
```

#### 2. Real-Time Processing

Process every user message for preference extraction:

```python
class ChatMessageHandler:
    def __init__(self, preference_extractor, rag_pipeline):
        self.preference_extractor = preference_extractor
        self.rag_pipeline = rag_pipeline
    
    async def handle_message(self, user_id: str, message: str, session_id: str):
        # 1. Extract preferences in parallel with RAG processing
        extraction_task = asyncio.create_task(
            self.preference_extractor.extract_preferences(message, user_id)
        )
        
        # 2. Get current preferences for context
        current_prefs = self.get_user_preferences(user_id)
        
        # 3. Generate response using RAG + preferences
        response = await self.rag_pipeline.generate(
            query=message,
            user_preferences=current_prefs
        )
        
        # 4. Update preferences if any were extracted
        new_prefs = await extraction_task
        if new_prefs:
            updated_prefs = self.preference_extractor.merge_with_existing(
                user_id, new_prefs
            )
            # Notify user about detected preferences
            response['detected_preferences'] = new_prefs
        
        return response
```

#### 3. Conflict Resolution

```python
def resolve_preference_conflict(existing_pref, new_pref):
    """
    Handle conflicting preferences
    """
    # Strategy 1: Confidence-based
    if new_pref['confidence'] > existing_pref['confidence'] + 0.1:
        return new_pref  # Replace with higher confidence
    
    # Strategy 2: Recency-based (with time decay)
    time_diff = datetime.now() - existing_pref['updated_at']
    if time_diff.days > 30:  # Old preference, likely outdated
        return new_pref
    
    # Strategy 3: Update count (reinforcement)
    if existing_pref['update_count'] >= 5:
        # Strong signal, keep existing unless new is much more confident
        if new_pref['confidence'] > 0.95:
            return new_pref
        return existing_pref
    
    # Default: keep existing, increment update count
    existing_pref['update_count'] += 1
    return existing_pref
```

### Feedback Collection

#### `user_feedback` Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: users)",
  "message_id": "ObjectId (ref: messages)",
  "session_id": "ObjectId (ref: sessions)",
  "feedback_type": "string (thumbs_up/thumbs_down/flag)",
  "feedback_details": {
    "too_long": "boolean",
    "too_short": "boolean",
    "too_formal": "boolean",
    "too_casual": "boolean",
    "inaccurate": "boolean",
    "custom_comment": "string"
  },
  "created_at": "datetime"
}
```

---

## 5. Personalization Limits

### Rationale
Similar to ChatGPT's approach, limits prevent:
- Over-personalization leading to filter bubbles
- Degradation of response quality
- Loss of diverse information exposure
- System becoming too rigid
- Accumulation of incorrect or outdated preferences

### Limit Specifications

#### 1. Personalization Weight
- **Base Response**: 70% (RAG results, factual content)
- **Personalized Style**: 30% (tone, length, formatting based on preferences)
- Ensures core information remains unchanged

#### 2. Preference Array Limits
- **Maximum preferences per user**: 50 preferences
- **Minimum confidence for storage**: 0.70
- **Auto-prune preferences**: Remove preferences with confidence < 0.50 after 30 days
- **Preference categories limit**: Max 5 preferences per category

#### 3. Automatic Extraction Limits
- **Max extractions per message**: 5 preferences
- **Cooldown for same preference key**: 24 hours (prevent spam updates)
- **Confidence threshold for auto-update**: 0.75
- **Confidence threshold for conflict override**: 0.90

#### 4. Update Frequency Limits
- **Max updates per preference key**: 15 updates total
- **After 15 updates**: Preference becomes "locked" (manual edit only)
- **Reset period**: 90 days of inactivity resets update count
- **Daily extraction limit**: 20 new/updated preferences per day

#### 5. Preference Constraints
- Responses must remain factually accurate regardless of style preferences
- Academic content cannot be oversimplified beyond readability
- All sources must still be cited
- Maximum response length: 2000 words
- Minimum response length: 50 words
- Personal information (name, major, etc.) cannot affect factual content

#### 6. Confidence Decay
- Preferences lose 5% confidence per 30 days of non-reinforcement
- Preferences below 0.50 confidence are archived (not deleted)
- Archived preferences can be restored if reinforced

### Monitoring & Override

#### Admin Dashboard Metrics
- Total preferences extracted per user
- Average confidence scores
- Preference update frequency
- Conflict resolution rate
- Extraction accuracy (based on user confirmations)
- Most common extracted preference keys

#### User Controls
- **View All Preferences**: See complete preference array with confidence scores
- **Delete Preference**: Remove individual preferences
- **Edit Preference**: Manually change value or confidence
- **Lock Preference**: Prevent automatic updates
- **Unlock Preference**: Re-enable automatic updates
- **Reset All Preferences**: Clear entire preference array
- **Disable Auto-Extraction**: Turn off automatic preference detection
- **View Extraction History**: See all detected preferences (confirmed and rejected)

---

## 6. Database Schema Updates

### New Collections

#### 1. `users` (detailed above)

#### 2. `user_feedback`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "message_id": "ObjectId",
  "session_id": "ObjectId",
  "feedback_type": "string",
  "feedback_details": "object",
  "created_at": "datetime"
}
```

#### 3. `preference_history`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "preference_key": "string",
  "old_value": "string",
  "new_value": "string",
  "change_source": "string (extracted/inferred/manual/admin)",
  "confidence_score": "float (for extracted/inferred changes)",
  "extracted_from_message": "string (optional)",
  "created_at": "datetime"
}
```

#### 4. `preference_extractions` (Audit Log)
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "message_id": "ObjectId",
  "extracted_preferences": [
    {
      "key": "string",
      "value": "string",
      "confidence": "float"
    }
  ],
  "user_action": "string (confirmed/rejected/ignored)",
  "created_at": "datetime"
}
```

### Updated Collections

#### `sessions` Collection (add user reference)
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: users)", // NEW
  "session_name": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "is_active": "boolean"
}
```

#### `messages` Collection (add feedback reference)
```json
{
  "_id": "ObjectId",
  "session_id": "ObjectId",
  "user_id": "ObjectId",
  "role": "string (user/assistant)",
  "content": "string",
  "timestamp": "datetime",
  "applied_preferences": [
    {
      "key": "string",
      "value": "string"
    }
  ],
  "extracted_preferences": [
    {
      "key": "string",
      "value": "string",
      "confidence": "float"
    }
  ],
  "has_feedback": "boolean"
}
```

---

## 7. API Endpoints

### Authentication Endpoints

#### POST `/api/auth/google`
**Description**: Initiate Google OAuth flow
**Request**: 
```json
{
  "redirect_uri": "string"
}
```
**Response**: 
```json
{
  "auth_url": "string"
}
```

#### POST `/api/auth/google/callback`
**Description**: Handle OAuth callback and generate JWT
**Request**: 
```json
{
  "code": "string",
  "state": "string"
}
```
**Response**: 
```json
{
  "access_token": "string (JWT)",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "profile_picture": "string"
  }
}
```

#### POST `/api/auth/logout`
**Description**: Invalidate user session
**Headers**: `Authorization: Bearer <token>`
**Response**: 
```json
{
  "message": "Logged out successfully"
}
```

#### GET `/api/auth/me`
**Description**: Get current user info
**Headers**: `Authorization: Bearer <token>`
**Response**: User object

### User Management Endpoints

#### GET `/api/users/profile`
**Description**: Get current user profile
**Headers**: `Authorization: Bearer <token>`
**Response**: Complete user object with preferences

#### PUT `/api/users/profile`
**Description**: Update user profile
**Headers**: `Authorization: Bearer <token>`
**Request**: 
```json
{
  "name": "string (optional)",
  "profile_picture": "string (optional)"
}
```

### Preference Endpoints

#### GET `/api/users/preferences`
**Description**: Get all user preferences as an array
**Headers**: `Authorization: Bearer <token>`
**Response**: 
```json
{
  "preferences": [
    {
      "key": "Name",
      "value": "Hemanth",
      "confidence": 0.95,
      "source": "extracted",
      "created_at": "2026-01-28T10:30:00Z",
      "updated_at": "2026-01-28T10:30:00Z",
      "update_count": 1,
      "locked": false
    },
    {
      "key": "Response style",
      "value": "elaborate",
      "confidence": 0.88,
      "source": "extracted",
      "created_at": "2026-01-28T11:15:00Z",
      "updated_at": "2026-01-28T11:15:00Z",
      "update_count": 1,
      "locked": false
    }
  ],
  "total_count": 2,
  "auto_extraction_enabled": true
}
```

#### POST `/api/users/preferences`
**Description**: Add or update a single preference manually
**Headers**: `Authorization: Bearer <token>`
**Request**: 
```json
{
  "key": "Response style",
  "value": "concise"
}
```
**Response**: 
```json
{
  "message": "Preference updated",
  "preference": {
    "key": "Response style",
    "value": "concise",
    "confidence": 1.0,
    "source": "manual",
    "updated_at": "2026-01-28T12:00:00Z"
  }
}
```

#### DELETE `/api/users/preferences/{key}`
**Description**: Delete a specific preference
**Headers**: `Authorization: Bearer <token>`
**Response**: 
```json
{
  "message": "Preference deleted",
  "deleted_key": "Response style"
}
```

#### PUT `/api/users/preferences/{key}/lock`
**Description**: Lock/unlock a preference to prevent automatic updates
**Headers**: `Authorization: Bearer <token>`
**Request**: 
```json
{
  "locked": true
}
```
**Response**: 
```json
{
  "message": "Preference locked",
  "preference": {...}
}
```

#### GET `/api/users/preferences/history`
**Description**: Get preference change history
**Headers**: `Authorization: Bearer <token>`
**Query Params**: `?limit=20&offset=0&key=Response style (optional)`
**Response**: Array of preference_history documents

#### POST `/api/users/preferences/reset`
**Description**: Reset all preferences (clear array)
**Headers**: `Authorization: Bearer <token>`
**Response**: 
```json
{
  "message": "All preferences reset",
  "preferences": []
}
```

#### PUT `/api/users/preferences/auto-extract`
**Description**: Enable/disable automatic preference extraction
**Headers**: `Authorization: Bearer <token>`
**Request**: 
```json
{
  "enabled": false
}
```
**Response**: 
```json
{
  "message": "Auto-extraction disabled",
  "auto_extraction_enabled": false
}
```

#### GET `/api/users/preferences/extractions`
**Description**: Get extraction history (all detected preferences)
**Headers**: `Authorization: Bearer <token>`
**Query Params**: `?limit=20&offset=0`
**Response**: 
```json
{
  "extractions": [
    {
      "_id": "...",
      "message_id": "...",
      "extracted_preferences": [
        {"key": "Name", "value": "Hemanth", "confidence": 0.95}
      ],
      "user_action": "confirmed",
      "created_at": "2026-01-28T10:30:00Z"
    }
  ]
}
```

#### POST `/api/users/preferences/extractions/{extraction_id}/confirm`
**Description**: Confirm or reject an extracted preference
**Headers**: `Authorization: Bearer <token>`
**Request**: 
```json
{
  "preference_index": 0,
  "action": "confirm"  // or "reject"
}
```

### Feedback Endpoints

#### POST `/api/feedback`
**Description**: Submit feedback for a message
**Headers**: `Authorization: Bearer <token>`
**Request**: 
```json
{
  "message_id": "string",
  "feedback_type": "string",
  "feedback_details": "object (optional)"
}
```
**Response**: 
```json
{
  "message": "Feedback recorded",
  "preference_updated": "boolean"
}
```

#### GET `/api/feedback/history`
**Description**: Get user's feedback history
**Headers**: `Authorization: Bearer <token>`
**Query Params**: `?limit=20&offset=0`
**Response**: Array of feedback documents

---

## 8. Implementation Checklist

### Phase 2.1: Authentication Foundation
- [ ] Set up Google Cloud Console project
- [ ] Obtain OAuth credentials
- [ ] Install required packages (`google-auth`, `PyJWT`)
- [ ] Create `.env` configuration for secrets
- [ ] Implement auth routes (`/api/auth/*`)
- [ ] Create JWT utility functions
- [ ] Implement authentication middleware
- [ ] Update frontend with Google Sign-In button
- [ ] Implement token storage in frontend (localStorage/cookies)
- [ ] Add auth interceptor to API client
- [ ] Test complete OAuth flow

### Phase 2.2: User Management
- [ ] Create `users` collection with array-based preferences field
- [ ] Create indexes (google_id, email)
- [ ] Implement user repository (`users_repo.py`)
- [ ] Create user service (`user_service.py`)
- [ ] Implement user profile endpoints
- [ ] Add user_id to sessions and messages collections
- [ ] Update existing repositories to handle user context
- [ ] Migrate existing data (if any)
- [ ] Create user profile page in frontend
- [ ] Test user creation and profile management

### Phase 2.3: AI Preference Extraction System
- [ ] Set up LLM integration (OpenAI/Claude/local model)
- [ ] Create `AIPreferenceExtractor` class
- [ ] Design extraction prompt template
- [ ] Implement extraction pipeline
- [ ] Create `preference_history` collection
- [ ] Create `preference_extractions` audit collection
- [ ] Implement preference repository with array operations
- [ ] Add preference merging and conflict resolution logic
- [ ] Implement confidence scoring system
- [ ] Test extraction accuracy with various inputs

### Phase 2.4: Preference Management API
- [ ] Implement GET `/api/users/preferences` (return array)
- [ ] Implement POST `/api/users/preferences` (add/update single)
- [ ] Implement DELETE `/api/users/preferences/{key}`
- [ ] Implement PUT `/api/users/preferences/{key}/lock`
- [ ] Implement GET `/api/users/preferences/history`
- [ ] Implement POST `/api/users/preferences/reset`
- [ ] Implement PUT `/api/users/preferences/auto-extract`
- [ ] Implement GET `/api/users/preferences/extractions`
- [ ] Implement POST confirmation endpoint
- [ ] Test all CRUD operations on preferences

### Phase 2.5: Real-Time Extraction Integration
- [ ] Integrate extraction into message handler
- [ ] Update messages collection to store extracted preferences
- [ ] Implement async extraction processing
- [ ] Add extraction results to API response
- [ ] Create frontend notification for detected preferences
- [ ] Add confirm/reject UI components
- [ ] Implement extraction history view
- [ ] Test real-time extraction during chat

### Phase 2.6: Preference Application to Responses
- [ ] Update RAG pipeline to accept preferences array
- [ ] Create preference formatter/applier module
- [ ] Implement style adjustment based on preferences
- [ ] Apply response length preferences
- [ ] Apply tone/formality preferences
- [ ] Store applied preferences snapshot with each message
- [ ] Test response variations with different preferences
- [ ] Validate 70/30 content-to-style ratio

### Phase 2.7: Personalization Limits & Controls
- [ ] Implement max preferences limit (50)
- [ ] Implement daily extraction limit (20)
- [ ] Implement per-preference update limit (15)
- [ ] Add cooldown period logic (24h for same key)
- [ ] Implement confidence decay (5% per 30 days)
- [ ] Add preference auto-pruning job
- [ ] Create preference locking mechanism
- [ ] Test all limit enforcement

### Phase 2.8: Frontend UI Development
- [ ] Create preference dashboard page
- [ ] Display preferences as cards with metadata
- [ ] Add edit/delete controls for each preference
- [ ] Create preference lock toggle
- [ ] Add auto-extraction enable/disable toggle
- [ ] Create extraction history view
- [ ] Add inline preference detection indicators
- [ ] Create confirmation modal for detected preferences
- [ ] Add preference visualization (confidence, source)
- [ ] Test all UI interactions

### Phase 2.9: Feedback Collection
- [ ] Create `user_feedback` collection
- [ ] Implement feedback repository
- [ ] Create feedback service
- [ ] Implement POST `/api/feedback` endpoint
- [ ] Implement GET `/api/feedback/history` endpoint
- [ ] Add feedback UI (thumbs up/down buttons)
- [ ] Add detailed feedback form
- [ ] Link feedback to preference updates
- [ ] Test feedback flow

### Phase 2.10: Testing & Documentation
- [ ] Write unit tests for preference extraction
- [ ] Write unit tests for auth services
- [ ] Write integration tests for OAuth flow
- [ ] Test extraction accuracy (create test dataset)
- [ ] Test conflict resolution logic
- [ ] Test confidence scoring accuracy
- [ ] Load test with multiple concurrent users
- [ ] Security audit of auth implementation
- [ ] Test personalization limits enforcement
- [ ] Document API endpoints
- [ ] Create user guide for preference system
- [ ] Document extraction algorithm
- [ ] Create admin monitoring documentation

---

## Environment Variables Required

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback

# JWT Configuration
JWT_SECRET_KEY=your_secure_random_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# LLM for Preference Extraction (Choose one)
# Option 1: OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # or gpt-4

# Option 2: Anthropic Claude
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Option 3: Local LLM (Ollama)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3

# Preference Extraction Settings
PREFERENCE_EXTRACTION_ENABLED=true
PREFERENCE_MIN_CONFIDENCE=0.70
PREFERENCE_MAX_PER_USER=50
PREFERENCE_DAILY_LIMIT=20

# Application
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

---

## Success Criteria

### Phase 2 Completion Metrics
1. ✅ Users can authenticate via Google OAuth
2. ✅ User profiles are created and maintained with array-based preferences
3. ✅ AI automatically extracts preferences from natural conversation
4. ✅ Users can view, edit, and delete extracted preferences
5. ✅ Preferences are applied to chat responses (70/30 content/style ratio)
6. ✅ System handles preference conflicts intelligently
7. ✅ Automatic extraction respects personalization limits
8. ✅ All endpoints are secured with authentication
9. ✅ Frontend UI displays preferences with confidence scores
10. ✅ System handles 100+ concurrent authenticated users

### Preference Extraction Goals
- Extract preferences with >85% accuracy
- Minimum 0.70 confidence threshold for storage
- Process each message for extraction in <500ms
- Successfully merge conflicting preferences
- Users can confirm/reject detected preferences

### User Experience Goals
- Authentication flow completes in <5 seconds
- Preference extraction happens transparently
- Users see clear notifications for detected preferences
- Preference application reflects immediately in responses
- Override controls are easily accessible
- Preference dashboard is intuitive and informative

---

## Future Considerations (Phase 3+)
- Multi-tenant support for different institutions
- Role-based access control (student, faculty, admin)
- Advanced analytics dashboard
- A/B testing for extraction algorithms
- Export chat history with preferences
- Collaborative sessions with shared preferences
- Voice input/output support
- Multi-language preference extraction

---

## 9. Practical Examples

### Example 1: Name Extraction and Usage

**Input:** "Hi! I'm Hemanth. Nice to meet you!"

**Extracted:**
```json
{"key": "Name", "value": "Hemanth", "confidence": 0.95}
```

**Future responses will use:**
- "Here's what you need to know, Hemanth..."
- "Great question, Hemanth! Let me explain..."

---

### Example 2: Style Preference Extraction

**Input:** "I would like an elaborate answer with lots of details"

**Extracted:**
```json
{"key": "Response style", "value": "elaborate with details", "confidence": 0.88}
```

**Future responses will be:**
- Longer and more comprehensive
- Include additional context and background
- Provide thorough explanations

---

### Example 3: Multiple Preferences in One Message

**Input:** "Hi, I'm Sarah, a second-year ME student. I prefer short, bullet-pointed answers."

**Extracted:**
```json
[
  {"key": "Name", "value": "Sarah", "confidence": 0.95},
  {"key": "Year", "value": "second-year", "confidence": 0.92},
  {"key": "Major", "value": "Mechanical Engineering", "confidence": 0.90},
  {"key": "Response style", "value": "short", "confidence": 0.85},
  {"key": "Format preference", "value": "bullet points", "confidence": 0.88}
]
```

---

### Example 4: Conflict Resolution

**Scenario:** User initially says "I like detailed explanations" (stored as "Response style: detailed")

**Later says:** "Keep it brief please"

**System Action:**
1. Extracts: `{"key": "Response style", "value": "brief", "confidence": 0.90}`
2. Detects conflict with existing "detailed" preference
3. Compares confidence and recency
4. Updates to "brief" with higher confidence
5. Logs change in preference_history

---

### Example 5: Preference Dashboard UI

**Display:**
```
┌─────────────────────────────────────────────────────┐
│ Your Preferences                    [+ Add Manual]   │
├─────────────────────────────────────────────────────┤
│ 🟢 Name: Hemanth                                    │
│    Confidence: 95% | Source: Extracted              │
│    From: "Hi I'm Hemanth"                           │
│    [Edit] [Delete] [🔓 Unlocked]                    │
├─────────────────────────────────────────────────────┤
│ 🟡 Response style: concise                          │
│    Confidence: 82% | Source: Extracted              │
│    From: "keep responses concise"                   │
│    Updated 2 times | Last: 2 hours ago              │
│    [Edit] [Delete] [🔒 Lock]                        │
├─────────────────────────────────────────────────────┤
│ 🟢 Major: Computer Science                          │
│    Confidence: 90% | Source: Extracted              │
│    From: "I'm a CS major"                           │
│    [Edit] [Delete] [🔓 Unlocked]                    │
└─────────────────────────────────────────────────────┘

Auto-extraction: [🟢 Enabled]  |  Total: 3/50 preferences
```

---

### Example 6: Real-Time Detection Notification

**User types:** "Please use technical language, I can handle it"

**UI shows (bottom-right notification):**
```
┌─────────────────────────────────────┐
│ 🔍 Preference Detected!              │
│                                      │
│ Technical level: advanced            │
│ Confidence: 88%                      │
│                                      │
│ [✓ Apply]  [✗ Reject]  [Later]      │
└─────────────────────────────────────┘
```

---

**Document Version**: 2.0  
**Created**: January 28, 2026  
**Last Updated**: January 28, 2026  
**Major Changes**: Converted from fixed preference categories to AI-powered dynamic array-based preference extraction system
