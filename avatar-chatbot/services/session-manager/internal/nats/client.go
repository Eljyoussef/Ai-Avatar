package nats

import (
    "encoding/json"

    "github.com/nats-io/nats.go"
    "go.uber.org/zap"
)

type NATSClient struct {
    conn   *nats.Conn
    logger *zap.Logger
}

func NewNATSClient(url string, logger *zap.Logger) (*NATSClient, error) {
    conn, err := nats.Connect(url,
        nats.ReconnectWait(2),
        nats.MaxReconnects(-1),
    )
    if err != nil {
        return nil, err
    }

    logger.Info("Connected to NATS", zap.String("url", url))
    return &NATSClient{conn: conn, logger: logger}, nil
}

func (n *NATSClient) Publish(subject string, data interface{}) error {
    payload, err := json.Marshal(data)
    if err != nil {
        return err
    }
    return n.conn.Publish(subject, payload)
}

func (n *NATSClient) Subscribe(subject string, handler nats.MsgHandler) (*nats.Subscription, error) {
    return n.conn.Subscribe(subject, handler)
}

func (n *NATSClient) Request(subject string, data interface{}, timeout time.Duration) (*nats.Msg, error) {
    payload, err := json.Marshal(data)
    if err != nil {
        return nil, err
    }
    return n.conn.Request(subject, payload, timeout)
}

func (n *NATSClient) Close() {
    n.conn.Close()
}