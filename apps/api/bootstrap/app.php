<?php

use App\Domain\Leagues\LeagueDomainException;
use App\Http\Middleware\RequestId;
use App\Http\Middleware\TemporaryUserAuthentication;
use App\Services\Analytics\AnalyticsException;
use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Database\Eloquent\ModelNotFoundException;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->api(prepend: [RequestId::class]);
        $middleware->alias(['temporary.auth' => TemporaryUserAuthentication::class]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->render(function (AnalyticsException $exception, Request $request) {
            return response()->json([
                'error' => [
                    'code' => $exception->errorCode,
                    'message' => $exception->getMessage(),
                    'request_id' => $request->attributes->get('request_id'),
                ],
            ], $exception->httpStatus);
        });
        $exceptions->render(function (LeagueDomainException $exception, Request $request) {
            return response()->json(['error' => [
                'code' => $exception->errorCode,
                'message' => $exception->getMessage(),
                'request_id' => $request->attributes->get('request_id'),
            ]], $exception->httpStatus);
        });
        $exceptions->render(function (AuthorizationException $exception, Request $request) {
            return response()->json(['error' => [
                'code' => 'LEAGUE_FORBIDDEN', 'message' => 'Accesso alla lega non consentito.',
                'request_id' => $request->attributes->get('request_id'),
            ]], 403);
        });
        $exceptions->render(function (ModelNotFoundException $exception, Request $request) {
            return response()->json(['error' => [
                'code' => 'LEAGUE_NOT_FOUND', 'message' => 'Lega non trovata.',
                'request_id' => $request->attributes->get('request_id'),
            ]], 404);
        });
        $exceptions->render(function (ValidationException $exception, Request $request) {
            $code = str_contains($request->path(), 'roster-rules') ? 'INVALID_ROSTER_RULES'
                : (str_contains($request->path(), '/rules') ? 'INVALID_LEAGUE_RULES' : 'VALIDATION_ERROR');

            return response()->json(['error' => [
                'code' => $code, 'message' => 'Dati non validi.',
                'request_id' => $request->attributes->get('request_id'), 'details' => $exception->errors(),
            ]], 422);
        });
    })->create();
