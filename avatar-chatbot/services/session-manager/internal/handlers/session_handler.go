package handlers

import (
    "context"
    "encoding/json"
    "time"

    "github.com/avatar-chatbot/session-manager/internal/session"
    "github.com/nats-io/nats.go"
    "go.uber.org/zap"
)

type SessionHandler struct {
    manager *session.Manager
    logger  *zap.Logger
    nats    *nats.Conn
}

func NewSessionHandler(manager *session.Manager, natsConn *nats.Conn, logger *zap.Logger) *SessionHandler {
    return &SessionHandler{
        manager: manager,
        logger:  logger,
        nats:    natsConn,
    }
}

func (h *SessionHandler) Register() error {
    // Handle session creation
    h.nats.Subscribe("session.create", func(msg *nats.Msg) {
        var req struct {
            UserID string `json:"user_id"`
        }
        json.Unmarshal(msg.Data, &req)

        ctx := context.Background()
        s, err := h.manager.CreateSession(ctx, req.UserID)
        if err != nil {
            h.logger.Error("Failed to create session", zap.Error(err))
            return
        }

        response, _ := json.Marshal(s)
        msg.Respond(response)
    })

    // Handle interrupts
    h.nats.Subscribe("session.*.control.interrupt", func(msg *nats.Msg) {
        sessionID := extractSessionID(msg.Subject)
        ctx := context.Background()
        
        if err := h.manager.HandleInterrupt(ctx, sessionID); err != nil {
            h.logger.Error("Failed to handle interrupt", zap.Error(err))
        }
    })

    // Handle accent updates
    h.nats.Subscribe("session.*.accent.update", func(msg *nats.Msg) {
        sessionID := extractSessionID(msg.Subject)
        var req struct {
            Accent string `json:"accent"`
        }
        json.Unmarshal(msg.Data, &req)

        ctx := context.Background()
        h.manager.SetAccent(ctx, sessionID, req.Accent)
    })

    // Handle gender updates
    h.nats.Subscribe("session.*.gender.update", func(msg *nats.Msg) {
        sessionID := extractSessionID(msg.Subject)
        var req struct {
            Gender string `json:"gender"`
        }
        json.Unmarshal(msg.Data, &req)

        ctx := context.Background()
        h.manager.SetGender(ctx, sessionID, req.Gender)
    })

    // Start cleanup goroutine
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