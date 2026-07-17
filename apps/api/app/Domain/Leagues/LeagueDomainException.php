<?php

namespace App\Domain\Leagues;

use RuntimeException;

class LeagueDomainException extends RuntimeException
{
    public function __construct(public readonly string $errorCode, public readonly int $httpStatus, string $message)
    {
        parent::__construct($message);
    }
}
