<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;

class AnalyticsContractTest extends TestCase
{
    public function test_gateway_dependencies_exist_in_versioned_openapi_contract(): void
    {
        $contractPath = dirname(__DIR__, 4).'/contracts/openapi/analytics-read-api.v1.json';
        $contract = json_decode((string) file_get_contents($contractPath), true, flags: JSON_THROW_ON_ERROR);

        foreach (['/health', '/ready', '/api/v1/players', '/api/v1/teams', '/api/v1/players/{id}', '/api/v1/import-runs'] as $path) {
            $this->assertArrayHasKey($path, $contract['paths']);
            $this->assertArrayHasKey('get', $contract['paths'][$path]);
        }
    }
}
