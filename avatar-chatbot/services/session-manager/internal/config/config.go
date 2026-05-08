package config

import "os"

type Config struct {
    NatsURL  string
    RedisURL string
    LogLevel string
}

func Load() *Config {
    return &Config{
        NatsURL:  getEnv("NATS_URL", "nats://localhost:4222"),
        RedisURL: getEnv("REDIS_URL", "redis://localhost:6379/0"),
        LogLevel: getEnv("LOG_LEVEL", "info"),
    }
}

func getEnv(key, fallback string) string {
    if value, ok := os.LookupEnv(key); ok {
        return value
    }
    return fallback
}