<?php

namespace App\Services\Analytics\DTO;

use App\Services\Analytics\AnalyticsException;

class AnalyticsImportRun
{
    public function __construct(private readonly array $attributes) {}

    public static function fromArray(array $attributes): self
    {
        foreach (['id', 'source', 'season', 'status'] as $field) {
            if (! array_key_exists($field, $attributes)) {
                throw new AnalyticsException('ANALYTICS_INVALID_RESPONSE', 502, 'Risposta analytics non valida.');
            }
        }

        return new self($attributes);
    }

    public function toArray(): array
    {
        return $this->attributes;
    }
}
