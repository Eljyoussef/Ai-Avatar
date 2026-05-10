package main

import (
    "context"
    "os"
    "os/signal"
    "syscall"

    "github.com/avatar-chatbot/session-manager/internal/config"
    "github.com/avatar-chatbot/session-manager/internal/handlers"
    "github.com/avatar-chatbot/session-manager/internal/nats"
    "github.com/avatar-chatbot/session-manager/internal/redis"
    "github.com/avatar-chatbot/session-manager/internal/session"
    "go.uber.org/zap"
)

func main() {
    logger, _ := zap.NewProduction()
    defer logger.Sync()

    logger.Info("Starting Session Manager")

    cfg := config.Load()

    redisStore, err := redis.NewRedisStore(cfg.RedisURL, logger)
    if err != nil {
        logger.Fatal("Failed to connect to Redis", zap.Error(err))
    }
    defer redisStore.Close()

    natsClient, err := nats.NewNATSClient(cfg.NatsURL, logger)
    if err != nil {
        logger.Fatal("Failed to connect to NATS", zap.Error(err))
    }
    defer natsClient.Close()

    sessionMgr := session.NewManager(redisStore, natsClient, logger)

    handler := handlers.NewSessionHandler(sessionMgr, natsClient, logger)
    if err := handler.Register(); err != nil {
        logger.Fatal("Failed to register handlers", zap.Error(err))
    }

    logger.Info("Session Manager running")

    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()
    <-ctx.Done()

    logger.Info("Shutting down Session Manager")
}