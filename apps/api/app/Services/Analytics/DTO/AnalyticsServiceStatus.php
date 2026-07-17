<?php

namespace App\Services\Analytics\DTO;

class AnalyticsServiceStatus
{
    public function __construct(
        public readonly bool $alive,
        public readonly bool $ready,
    ) {}

    public function toArray(): array
    {
        return ['service' => 'analytics', 'alive' => $this->alive, 'ready' => $this->ready];
    }
}
