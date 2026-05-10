package handlers

import (
    "context"
    "encoding/json"
    "strings"
    "time"

    "github.com/avatar-chatbot/session-manager/internal/session"
    "go.uber.org/zap"
)

type NATSPubSub interface {
    Publish(subject string, data interface{}) error
    Subscribe(subject string, handler func(subject string, data []byte)) error
}

type SessionHandler struct {
    manager *session.Manager
    logger  *zap.Logger
    nats    NATSPubSub
}

func NewSessionHandler(manager *session.Manager, nats NATSPubSub, logger *zap.Logger) *SessionHandler {
    return &SessionHandler{
        manager: manager,
        logger:  logger,
        nats:    nats,
    }
}

func (h *SessionHandler) Register() error {
    h.nats.Subscribe("session.create", func(subject string, data []byte) {
        var req struct {
            UserID string `json:"user_id"`
        }
        json.Unmarshal(data, &req)
        ctx := context.Background()
        h.manager.CreateSession(ctx, req.UserID)
    })

    h.nats.Subscribe("session.*.control.interrupt", func(subject string, data []byte) {
        sessionID := extractSessionID(subject)
        h.manager.HandleInterrupt(context.Background(), sessionID)
    })

    h.nats.Subscribe("session.*.accent.update", func(subject string, data []byte) {
        sessionID := extractSessionID(subject)
        var req struct{ Accent string `json:"accent"` }
        json.Unmarshal(data, &req)
        h.manager.SetAccent(context.Background(), sessionID, req.Accent)
    })

    h.nats.Subscribe("session.*.gender.update", func(subject string, data []byte) {
        sessionID := extractSessionID(subject)
        var req struct{ Gender string `json:"gender"` }
        json.Unmarshal(data, &req)
        h.manager.SetGender(context.Background(), sessionID, req.Gender)
    })

    go func() {
        ticker := time.NewTicker(5 * time.Minute)
        for range ticker.C {
            h.manager.CleanupExpired(context.Background())
        }
    }()

    h.logger.Info("Session handlers registered")
    return nil
}

func extractSessionID(subject string) string {
    parts := strings.Split(subject, ".")
    if len(parts) >= 2 {
        return parts[1]
    }
    return ""
}