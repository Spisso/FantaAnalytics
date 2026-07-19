<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\PlayerIndexRequest;
use App\Services\Analytics\AnalyticsClient;
use Illuminate\Http\JsonResponse;

class AnalyticsController extends Controller
{
    public function __construct(private readonly AnalyticsClient $analytics) {}

    public function status(): JsonResponse
    {
        return response()->json($this->analytics->status()->toArray());
    }

    public function players(PlayerIndexRequest $request): JsonResponse
    {
        return response()->json($this->analytics->players($request->filters())->toArray());
    }

    public function teams(PlayerIndexRequest $request): JsonResponse
    {
        return response()->json($this->analytics->teams($request->validated('season')));
    }

    public function player(string $id): JsonResponse
    {
        return response()->json(['data' => $this->analytics->player($id)->toArray()]);
    }

    public function importRuns(): JsonResponse
    {
        return response()->json($this->analytics->importRuns());
    }
}
