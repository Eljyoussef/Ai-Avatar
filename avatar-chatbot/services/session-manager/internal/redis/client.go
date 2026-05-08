package redis

import (
    "context"
    "encoding/json"
    "time"

    "github.com/avatar-chatbot/session-manager/internal/session"
    "github.com/redis/go-redis/v9"
    "go.uber.org/zap"
)

type RedisStore struct {
    client *redis.Client
    logger *zap.Logger
}

func NewRedisStore(redisURL string, logger *zap.Logger) (*RedisStore, error) {
    opts, err := redis.ParseURL(redisURL)
    if err != nil {
        return nil, err
    }

    client := redis.NewClient(opts)

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    if err := client.Ping(ctx).Err(); err != nil {
        return nil, err
    }

    logger.Info("Connected to Redis")
    return &RedisStore{client: client, logger: logger}, nil
}

func (r *RedisStore) Save(ctx context.Context, s *session.SessionState) error {
    data, err := json.Marshal(s)
    if err != nil {
        return err
    }

    key := "session:" + s.ID
    return r.client.Set(ctx, key, data, s.TTL).Err()
}

func (r *RedisStore) Get(ctx context.Context, sessionID string) (*session.SessionState, error) {
    key := "session:" + sessionID
    data, err := r.client.Get(ctx, key).Result()
    if err != nil {
        return nil, err
    }

    var s session.SessionState
    if err := json.Unmarshal([]byte(data), &s); err != nil {
        return nil, err
    }

    return &s, nil
}

func (r *RedisStore) Delete(ctx context.Context, sessionID string) error {
    key := "session:" + sessionID
    return r.client.Del(ctx, key).Err()
}

func (r *RedisStore) SetInterruptFlag(ctx context.Context, sessionID string) error {
    key := "session:" + sessionID + ":interrupt"
    return r.client.Set(ctx, key, "true", 10*time.Second).Err()
}

func (r *RedisStore) ClearInterruptFlag(ctx context.Context, sessionID string) error {
    key := "session:" + sessionID + ":interrupt"
    return r.client.Del(ctx, key).Err()
}

func (r *RedisStore) IsInterrupted(ctx context.Context, sessionID string) bool {
    key := "session:" + sessionID + ":interrupt"
    val, err := r.client.Get(ctx, key).Result()
    return err == nil && val == "true"
}

func (r *RedisStore) Close() error {
    return r.client.Close()
}