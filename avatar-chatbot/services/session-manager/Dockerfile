FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY services/session-manager/go.mod ./
RUN go mod download
RUN go mod tidy
COPY services/session-manager/ ./
RUN CGO_ENABLED=0 GOOS=linux GONOSUMCHECK=* GONOSUMDB=* GOFLAGS=-mod=mod go build -o session-manager ./cmd/main.go
FROM alpine:3.19
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /app/session-manager .
EXPOSE 8080
CMD ["./session-manager"]