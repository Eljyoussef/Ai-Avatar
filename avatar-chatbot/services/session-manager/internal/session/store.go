package session

import (
    "context"
    "time"
)

type SessionState struct {
    ID              string                 `json:"id"`
    UserID          string                 `json:"user_id"`
    Gender          string                 `json:"gender"`
    AccentProfile   string                 `json:"accent_profile"`
    IsActive        bool                   `json:"is_active"`
    IsInterrupted   bool                   `json:"is_interrupted"`
    IsSpeaking      bool                   `json:"is_speaking"`
    MessageHistory  []Message              `json:"message_history"`
    ActiveDocuments []string               `json:"active_documents"`
    Preferences     UserPreferences        `json:"preferences"`
    CreatedAt       time.Time              `json:"created_at"`
    LastActive      time.Time              `json:"last_active"`
    TTL             time.Duration          `json:"ttl"`
}

type Message struct {
    Role      string    `json:"role"`
    Content   string    `json:"content"`
    Timestamp time.Time `json:"timestamp"`
}

type UserPreferences struct {
    VoiceSpeed    float64 `json:"voice_speed"`
    VoiceGender   string  `json:"voice_gender"`
    AvatarEnabled bool    `json:"avatar_enabled"`
    AvatarQuality string  `json:"avatar_quality"`
}

type Store interface {
    Save(ctx context.Context, session *SessionState) error
    Get(ctx context.Context, sessionID string) (*SessionState, error)
    Delete(ctx context.Context, sessionID string) error
}