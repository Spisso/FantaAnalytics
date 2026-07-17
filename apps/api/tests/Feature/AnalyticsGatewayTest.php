<?php

namespace Tests\Feature;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class AnalyticsGatewayTest extends TestCase
{
    private array $player = [
        'id' => 1,
        'canonical_full_name' => 'Marco Aurora',
        'effective_fantasy_role' => 'P',
        'team' => 'Torino',
        'season' => '2026-27',
    ];

    public function test_api_health_is_independent_from_analytics(): void
    {
        Http::fake(fn () => throw new ConnectionException('offline'));

        $this->getJson('/api/v1/health')
            ->assertOk()
            ->assertExactJson(['service' => 'api', 'status' => 'ok']);
        Http::assertNothingSent();
    }

    public function test_analytics_status_is_healthy(): void
    {
        Http::fake([
            '*/health' => Http::response(['service' => 'analytics', 'status' => 'ok']),
            '*/ready' => Http::response(['database' => true, 'status' => 'ready']),
        ]);

        $this->getJson('/api/v1/analytics/status')
            ->assertOk()
            ->assertExactJson(['service' => 'analytics', 'alive' => true, 'ready' => true]);
    }

    public function test_analytics_status_reports_degraded_readiness(): void
    {
        Http::fake([
            '*/health' => Http::response(['service' => 'analytics', 'status' => 'ok']),
            '*/ready' => Http::response(['database' => false, 'status' => 'unavailable'], 503),
        ]);

        $this->getJson('/api/v1/analytics/status')
            ->assertOk()
            ->assertExactJson(['service' => 'analytics', 'alive' => true, 'ready' => false]);
    }

    public function test_analytics_status_handles_connection_failure_and_timeout(): void
    {
        Http::fake(fn () => throw new ConnectionException('timeout'));

        $this->getJson('/api/v1/analytics/status')
            ->assertOk()
            ->assertExactJson(['service' => 'analytics', 'alive' => false, 'ready' => false]);
    }

    public function test_analytics_status_handles_invalid_json(): void
    {
        Http::fake(['*/health' => Http::response('not-json', 200)]);

        $this->getJson('/api/v1/analytics/status')
            ->assertOk()
            ->assertJson(['alive' => false, 'ready' => false]);
    }

    public function test_players_are_proxied_and_filters_are_allowlisted(): void
    {
        Http::fake(['*/api/v1/players*' => Http::response(['data' => [$this->player], 'count' => 1])]);

        $this->getJson('/api/v1/players?role=P&team=Torino&season=2026-27&limit=10')
            ->assertOk()
            ->assertJsonPath('count', 1)
            ->assertJsonPath('data.0.canonical_full_name', 'Marco Aurora');

        Http::assertSent(fn ($request): bool => str_contains($request->url(), 'role=P')
            && str_contains($request->url(), 'team=Torino')
            && str_contains($request->url(), 'season=2026-27')
            && str_contains($request->url(), 'limit=10'));
    }

    public function test_invalid_filters_return_422_without_calling_analytics(): void
    {
        Http::fake();

        $this->getJson('/api/v1/players?role=X&season=bad&limit=500')
            ->assertUnprocessable()
            ->assertJsonPath('error.code', 'INVALID_FILTERS')
            ->assertJsonStructure(['error' => ['details' => ['role', 'season', 'limit']]]);
        Http::assertNothingSent();
    }

    public function test_player_detail_and_import_runs_follow_contract(): void
    {
        Http::fake([
            '*/api/v1/players/1' => Http::response(['data' => $this->player]),
            '*/api/v1/import-runs' => Http::response([
                'data' => [['id' => 2, 'source' => 'demo', 'season' => '2026-27', 'status' => 'completed']],
                'count' => 1,
            ]),
        ]);

        $this->getJson('/api/v1/players/1')->assertOk()->assertJsonPath('data.id', 1);
        $this->getJson('/api/v1/import-runs')->assertOk()->assertJsonPath('data.0.source', 'demo');
    }

    public function test_upstream_404_is_mapped_without_stack_trace(): void
    {
        Http::fake(['*/api/v1/players/999' => Http::response(['error' => 'missing'], 404)]);

        $this->withHeader('X-Request-ID', 'test-request')
            ->getJson('/api/v1/players/999')
            ->assertNotFound()
            ->assertExactJson([
                'error' => [
                    'code' => 'PLAYER_NOT_FOUND',
                    'message' => 'Giocatore non trovato.',
                    'request_id' => 'test-request',
                ],
            ]);
    }

    public function test_upstream_errors_and_invalid_payload_are_controlled(): void
    {
        Http::fakeSequence()
            ->push(['error' => 'failure'], 500)
            ->push('invalid-json', 200)
            ->push(['error' => 'invalid'], 422);

        $this->getJson('/api/v1/players')->assertStatus(502)->assertJsonPath('error.code', 'ANALYTICS_UPSTREAM_ERROR');
        $this->getJson('/api/v1/players')->assertStatus(502)->assertJsonPath('error.code', 'ANALYTICS_INVALID_RESPONSE');
        $this->getJson('/api/v1/players')->assertStatus(422)->assertJsonPath('error.code', 'ANALYTICS_VALIDATION_ERROR');
    }

    public function test_unavailable_players_return_controlled_503(): void
    {
        Http::fake(fn () => throw new ConnectionException('offline'));

        $this->getJson('/api/v1/players')
            ->assertServiceUnavailable()
            ->assertJsonPath('error.code', 'ANALYTICS_UNAVAILABLE')
            ->assertJsonMissing(['trace']);
    }
}
