<?php

namespace App\Services\Analytics\DTO;

class PlayerFilters
{
    public function __construct(
        public readonly ?string $role = null,
        public readonly ?string $team = null,
        public readonly ?string $season = null,
        public readonly ?int $limit = null,
    ) {}

    public static function fromArray(array $values): self
    {
        return new self(
            $values['role'] ?? null,
            $values['team'] ?? null,
            $values['season'] ?? null,
            isset($values['limit']) ? (int) $values['limit'] : null,
        );
    }

    public function toQuery(): array
    {
        return array_filter([
            'role' => $this->role,
            'team' => $this->team,
            'season' => $this->season,
            'limit' => $this->limit,
        ], fn (mixed $value): bool => $value !== null);
    }
}
