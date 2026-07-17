<?php

namespace App\Http\Middleware;

use App\Models\User;
use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Symfony\Component\HttpFoundation\Response;

class TemporaryUserAuthentication
{
    public function handle(Request $request, Closure $next): Response
    {
        $user = User::find($request->header('X-User-ID'));
        if (! $user) {
            return response()->json(['error' => [
                'code' => 'UNAUTHENTICATED', 'message' => 'Utente non autenticato.',
                'request_id' => $request->attributes->get('request_id'),
            ]], 401);
        }
        Auth::setUser($user);
        $request->setUserResolver(fn (): User => $user);

        return $next($request);
    }
}
