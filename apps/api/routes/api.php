<?php

use App\Http\Controllers\Api\V1\AnalyticsController;
use App\Http\Controllers\Api\V1\HealthController;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function (): void {
    Route::get('/health', HealthController::class);
    Route::get('/analytics/status', [AnalyticsController::class, 'status']);
    Route::get('/players', [AnalyticsController::class, 'players']);
    Route::get('/players/{id}', [AnalyticsController::class, 'player'])->whereNumber('id');
    Route::get('/import-runs', [AnalyticsController::class, 'importRuns']);
});
