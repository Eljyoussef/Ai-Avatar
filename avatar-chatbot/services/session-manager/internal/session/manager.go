package session

import (
    "context"
    "sync"
    "time"

    "github.com/google/uuid"
    "go.uber.org/zap"
)

type NATSPublisher interface {
    Publish(subject string, data interface{}) error
}

type Manager struct {
    store    Store
    nats     NATSPublisher
    logger   *zap.Logger
    mu       sync.RWMutex
    cache    map[string]*SessionState
}

func NewManager(store Store, nats NATSPublisher, logger *zap.Logger) *Manager {
    return &Manager{
        store:  store,
        nats:   nats,
        logger: logger,
        cache:  make(map[string]*SessionState),
    }
}

func (m *Manager) CreateSession(ctx context.Context, userID string) (*SessionState, error) {
    s := &SessionState{
        ID:             uuid.New().String(),
        UserID:         userID,
        Gender:         "neutral",
        AccentProfile:  "fr-FR",
        IsActive:       true,
        IsInterrupted:  false,
        IsSpeaking:     false,
        MessageHistory: make([]Message, 0),
        Preferences: UserPreferences{
            VoiceSpeed:    1.0,
            VoiceGender:   "female",
            AvatarEnabled: false,
            AvatarQuality: "realtime",
        },
        CreatedAt:  time.Now(),
        LastActive: time.Now(),
        TTL:        30 * time.Minute,
    }

    if err := m.store.Save(ctx, s); err != nil {
        return nil, err
    }

    m.mu.Lock()
    m.cache[s.ID] = s
    m.mu.Unlock()

    m.logger.Info("Session created", zap.String("session_id", s.ID))
    return s, nil
}

func (m *Manager) GetSession(ctx context.Context, sessionID string) (*SessionState, error) {
    m.mu.RLock()
    if s, ok := m.cache[sessionID]; ok {
        m.mu.RUnlock()
        s.LastActive = time.Now()
        return s, nil
    }
    m.mu.RUnlock()

    s, err := m.store.Get(ctx, sessionID)
    if err != nil {
        return nil, err
    }

    s.LastActive = time.Now()

    m.mu.Lock()
    m.cache[sessionID] = s
    m.mu.Unlock()

    return s, nil
}

func (m *Manager) HandleInterrupt(ctx context.Context, sessionID string) error {
    s, err := m.GetSession(ctx, sessionID)
    if err != nil {
        return err
    }

    s.IsInterrupted = true
    s.IsSpeaking = false

    if err := m.store.Save(ctx, s); err != nil {
        return err
    }

    m.nats.Publish("session."+sessionID+".control.interrupt", map[string]interface{}{
        "session_id": sessionID,
        "timestamp":  time.Now().UnixMilli(),
    })

    m.logger.Info("Interrupt handled", zap.String("session_id", sessionID))
    return nil
}

func (m *Manager) SetAccent(ctx context.Context, sessionID, accent string) error {
    s, err := m.GetSession(ctx, sessionID)
    if err != nil {
        return err
    }

    s.AccentProfile = accent
    return m.store.Save(ctx, s)
}

func (m *Manager) SetGender(ctx context.Context, sessionID, gender string) error {
    s, err := m.GetSession(ctx, sessionID)
    if err != nil {
        return err
    }

    s.Gender = gender
    return m.store.Save(ctx, s)
}

func (m *Manager) AddMessage(ctx context.Context, sessionID string, msg Message) error {
    s, err := m.GetSession(ctx, sessionID)
    if err != nil {
        return err
    }

    s.MessageHistory = append(s.MessageHistory, msg)
    if len(s.MessageHistory) > 50 {
        s.MessageHistory = s.MessageHistory[len(s.MessageHistory)-50:]
    }

    return m.store.Save(ctx, s)
}

func (m *Manager) DeleteSession(ctx context.Context, sessionID string) error {
    m.mu.Lock()
    delete(m.cache, sessionID)
    m.mu.Unlock()

    return m.store.Delete(ctx, sessionID)
}

func (m *Manager) CleanupExpired(ctx context.Context) {
    m.mu.Lock()
    defer m.mu.Unlock()

    now := time.Now()
    for id, s := range m.cache {
        if now.Sub(s.LastActive) > s.TTL {
            delete(m.cache, id)
            m.store.Delete(ctx, id)
            m.logger.Info("Session expired", zap.String("session_id", id))
        }
    }
}