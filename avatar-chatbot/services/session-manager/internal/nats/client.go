package nats

import (
    "encoding/json"
    "time"

    "github.com/nats-io/nats.go"
    "go.uber.org/zap"
)

type NATSClient struct {
    Conn   *nats.Conn
    logger *zap.Logger
}

func NewNATSClient(url string, logger *zap.Logger) (*NATSClient, error) {
    conn, err := nats.Connect(url,
        nats.ReconnectWait(2*time.Second),
        nats.MaxReconnects(-1),
    )
    if err != nil {
        return nil, err
    }

    logger.Info("Connected to NATS", zap.String("url", url))
    return &NATSClient{Conn: conn, logger: logger}, nil
}

func (n *NATSClient) Publish(subject string, data interface{}) error {
    payload, err := json.Marshal(data)
    if err != nil {
        return err
    }
    return n.Conn.Publish(subject, payload)
}

func (n *NATSClient) Subscribe(subject string, handler func(subject string, data []byte)) error {
    _, err := n.Conn.Subscribe(subject, func(msg *nats.Msg) {
        handler(msg.Subject, msg.Data)
    })
    return err
}

func (n *NATSClient) Request(subject string, data interface{}, timeout time.Duration) (*nats.Msg, error) {
    payload, err := json.Marshal(data)
    if err != nil {
        return nil, err
    }
    return n.Conn.Request(subject, payload, timeout)
}

func (n *NATSClient) Close() {
    n.Conn.Close()
}