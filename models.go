package main

import "time"

type Payment struct {
    ID         int       `json:"id"`
    ProducerID string    `json:"producer_id"`
    ConsumerID string    `json:"consumer_id"`
    KWh        float64   `json:"kwh"`
    SatsAmount int       `json:"sats_amount"`
    Invoice    string    `json:"invoice"`
    Status     string    `json:"status"`
    CreatedAt  time.Time `json:"created_at"`
}
