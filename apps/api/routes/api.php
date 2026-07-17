<?php

use App\Http\Controllers\Api\V1\AnalyticsController;
use App\Http\Controllers\Api\V1\HealthController;
use App\Http\Controllers\Api\V1\LeagueController;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function (): void {
    Route::get('/health', HealthController::class);
    Route::get('/analytics/status', [AnalyticsController::class, 'status']);
    Route::get('/players', [AnalyticsController::class, 'players']);
    Route::get('/players/{id}', [AnalyticsController::class, 'player'])->whereNumber('id');
    Route::get('/import-runs', [AnalyticsController::class, 'importRuns']);
    Route::middleware('temporary.auth')->group(function (): void {
        Route::apiResource('leagues', LeagueController::class);
        Route::get('leagues/{league}/rules', [LeagueController::class, 'rules']);
        Route::put('leagues/{league}/rules', [LeagueController::class, 'updateRules']);
        Route::get('leagues/{league}/roster-rules', [LeagueController::class, 'rosterRules']);
        Route::put('leagues/{league}/roster-rules', [LeagueController::class, 'updateRosterRules']);
        Route::get('leagues/{league}/participants', [LeagueController::class, 'participants']);
        Route::post('leagues/{league}/participants', [LeagueController::class, 'addParticipant']);
        Route::patch('leagues/{league}/participants/{participant}', [LeagueController::class, 'updateParticipant']);
        Route::delete('leagues/{league}/participants/{participant}', [LeagueController::class, 'removeParticipant']);
    });
});
