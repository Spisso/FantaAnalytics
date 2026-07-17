<?php

namespace App\Services\Analytics;

use RuntimeException;

class AnalyticsException extends RuntimeException
{
    public function __construct(
        public readonly string $errorCode,
        public readonly int $httpStatus,
        string $message,
    ) {
        parent::__construct($message);
    }
}
