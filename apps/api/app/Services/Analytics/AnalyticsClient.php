<?php

namespace App\Services\Analytics;

use App\Services\Analytics\DTO\AnalyticsImportRun;
use App\Services\Analytics\DTO\AnalyticsPlayer;
use App\Services\Analytics\DTO\AnalyticsPlayerList;
use App\Services\Analytics\DTO\AnalyticsServiceStatus;
use App\Services\Analytics\DTO\PlayerFilters;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\PendingRequest;
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Throwable;

class AnalyticsClient
{
    private function http(): PendingRequest
    {
        return Http::baseUrl(rtrim((string) config('services.analytics.base_url'), '/'))
            ->acceptJson()
            ->connectTimeout((int) config('services.analytics.connect_timeout'))
            ->timeout((int) config('services.analytics.timeout'))
            ->retry(
                (int) config('services.analytics.retries'),
                100,
                fn (Throwable $exception): bool => $exception instanceof ConnectionException,
                throw: false,
            );
    }

    private function request(string $path, array $query = []): array
    {
        try {
            $response = $this->http()->get($path, $query);
        } catch (ConnectionException $exception) {
            Log::warning('analytics_request_failed', [
                'error_type' => $exception::class,
                'path' => $path,
            ]);
            throw new AnalyticsException(
                'ANALYTICS_UNAVAILABLE',
                503,
                'Il servizio analytics non è disponibile.',
            );
        }

        $this->guardStatus($response);
        $payload = $response->json();
        if (! is_array($payload)) {
            throw new AnalyticsException(
                'ANALYTICS_INVALID_RESPONSE',
                502,
                'Il servizio analytics ha restituito una risposta non valida.',
            );
        }

        return $payload;
    }

    private function guardStatus(Response $response): void
    {
        if ($response->successful()) {
            return;
        }
        if ($response->status() === 404) {
            throw new AnalyticsException('PLAYER_NOT_FOUND', 404, 'Giocatore non trovato.');
        }
        if ($response->status() === 422) {
            throw new AnalyticsException('ANALYTICS_VALIDATION_ERROR', 422, 'Richiesta analytics non valida.');
        }
        if ($response->serverError()) {
            throw new AnalyticsException('ANALYTICS_UPSTREAM_ERROR', 502, 'Errore del servizio analytics.');
        }

        throw new AnalyticsException('ANALYTICS_UNEXPECTED_RESPONSE', 502, 'Risposta analytics inattesa.');
    }

    public function health(): array
    {
        return $this->request('/health');
    }

    public function ready(): array
    {
        return $this->request('/ready');
    }

    public function status(): AnalyticsServiceStatus
    {
        try {
            $health = $this->health();
            $alive = ($health['status'] ?? null) === 'ok';
        } catch (AnalyticsException) {
            return new AnalyticsServiceStatus(false, false);
        }

        try {
            $readiness = $this->ready();
            $ready = ($readiness['database'] ?? false) === true
                && ($readiness['status'] ?? null) === 'ready';
        } catch (AnalyticsException) {
            $ready = false;
        }

        return new AnalyticsServiceStatus($alive, $ready);
    }

    public function players(PlayerFilters $filters): AnalyticsPlayerList
    {
        return AnalyticsPlayerList::fromArray($this->request('/api/v1/players', $filters->toQuery()));
    }

    public function teams(?string $season = null): array
    {
        $payload = $this->request('/api/v1/teams', array_filter(['season' => $season]));
        if (! isset($payload['data'], $payload['count']) || ! is_array($payload['data'])) {
            throw new AnalyticsException('ANALYTICS_INVALID_RESPONSE', 502, 'Risposta analytics non valida.');
        }

        return $payload;
    }

    public function player(string $id): AnalyticsPlayer
    {
        $payload = $this->request('/api/v1/players/'.rawurlencode($id));
        if (! isset($payload['data']) || ! is_array($payload['data'])) {
            throw new AnalyticsException('ANALYTICS_INVALID_RESPONSE', 502, 'Risposta analytics non valida.');
        }

        return AnalyticsPlayer::fromArray($payload['data']);
    }

    public function importRuns(): array
    {
        $payload = $this->request('/api/v1/import-runs');
        if (! isset($payload['data'], $payload['count']) || ! is_array($payload['data'])) {
            throw new AnalyticsException('ANALYTICS_INVALID_RESPONSE', 502, 'Risposta analytics non valida.');
        }
        $runs = array_map(AnalyticsImportRun::fromArray(...), $payload['data']);

        return [
            'data' => array_map(fn (AnalyticsImportRun $run): array => $run->toArray(), $runs),
            'count' => count($runs),
        ];
    }
}
