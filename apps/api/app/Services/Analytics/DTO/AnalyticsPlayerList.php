<?php

namespace App\Services\Analytics\DTO;

use App\Services\Analytics\AnalyticsException;

class AnalyticsPlayerList
{
    /** @param array<int, AnalyticsPlayer> $players */
    public function __construct(private readonly array $players) {}

    public static function fromArray(array $payload): self
    {
        if (! isset($payload['data'], $payload['count']) || ! is_array($payload['data'])) {
            throw new AnalyticsException('ANALYTICS_INVALID_RESPONSE', 502, 'Risposta analytics non valida.');
        }

        return new self(array_map(AnalyticsPlayer::fromArray(...), $payload['data']));
    }

    public function toArray(): array
    {
        return [
            'data' => array_map(fn (AnalyticsPlayer $player): array => $player->toArray(), $this->players),
            'count' => count($this->players),
        ];
    }
}
