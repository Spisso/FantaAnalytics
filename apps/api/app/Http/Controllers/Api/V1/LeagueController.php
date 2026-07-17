<?php

namespace App\Http\Controllers\Api\V1;

use App\Actions\Leagues\AddLeagueParticipant;
use App\Actions\Leagues\CreateFantasyLeague;
use App\Actions\Leagues\RemoveLeagueParticipant;
use App\Actions\Leagues\UpdateFantasyLeague;
use App\Actions\Leagues\UpdateLeagueRules;
use App\Actions\Leagues\UpdateRosterRules;
use App\Domain\Leagues\LeagueDomainException;
use App\Http\Controllers\Controller;
use App\Http\Requests\LeagueRequest;
use App\Http\Requests\LeagueRulesRequest;
use App\Http\Requests\ParticipantRequest;
use App\Http\Requests\RosterRulesRequest;
use App\Http\Resources\FantasyLeagueResource;
use App\Models\FantasyLeague;
use App\Models\LeagueParticipant;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;

class LeagueController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $id = $request->user()->id;
        $leagues = FantasyLeague::query()->where('owner_id', $id)
            ->orWhereHas('participants', fn ($query) => $query->where('user_id', $id))->get();

        return response()->json(['data' => FantasyLeagueResource::collection($leagues)]);
    }

    public function store(LeagueRequest $request, CreateFantasyLeague $action): JsonResponse
    {
        return (new FantasyLeagueResource($action->execute($request->user(), $request->validated())))
            ->response()->setStatusCode(201);
    }

    public function show(FantasyLeague $league): FantasyLeagueResource
    {
        $this->authorizeLeague('view', $league);

        return new FantasyLeagueResource($league->load(['rules', 'rosterRules', 'participants']));
    }

    public function update(LeagueRequest $request, FantasyLeague $league, UpdateFantasyLeague $action): FantasyLeagueResource
    {
        $this->authorizeLeague('update', $league);

        return new FantasyLeagueResource($action->execute($league, $request->validated()));
    }

    public function destroy(FantasyLeague $league): JsonResponse
    {
        $this->authorizeLeague('delete', $league);
        $league->delete();

        return response()->json([], 204);
    }

    public function rules(FantasyLeague $league): JsonResponse
    {
        $this->authorizeLeague('view', $league);

        return response()->json(['data' => $league->rules]);
    }

    public function updateRules(LeagueRulesRequest $request, FantasyLeague $league, UpdateLeagueRules $action): JsonResponse
    {
        $this->authorizeLeague('manage', $league);

        return response()->json(['data' => $action->execute($league, $request->validated())]);
    }

    public function rosterRules(FantasyLeague $league): JsonResponse
    {
        $this->authorizeLeague('view', $league);

        return response()->json(['data' => $league->rosterRules]);
    }

    public function updateRosterRules(RosterRulesRequest $request, FantasyLeague $league, UpdateRosterRules $action): JsonResponse
    {
        $this->authorizeLeague('manage', $league);

        return response()->json(['data' => $action->execute($league, $request->validated())]);
    }

    public function participants(FantasyLeague $league): JsonResponse
    {
        $this->authorizeLeague('view', $league);

        return response()->json(['data' => $league->participants]);
    }

    public function addParticipant(ParticipantRequest $request, FantasyLeague $league, AddLeagueParticipant $action): JsonResponse
    {
        $this->authorizeLeague('manage', $league);

        return response()->json(['data' => $action->execute($league, $request->validated())], 201);
    }

    public function updateParticipant(ParticipantRequest $request, FantasyLeague $league, LeagueParticipant $participant): JsonResponse
    {
        $this->authorizeLeague('manage', $league);
        $this->ensureParticipant($league, $participant);
        if (($request->validated('remaining_budget') ?? $participant->remaining_budget) > $participant->initial_budget) {
            throw new LeagueDomainException('VALIDATION_ERROR', 422, 'Il budget residuo supera il budget iniziale.');
        }
        try {
            $participant->update($request->validated());
        } catch (UniqueConstraintViolationException) {
            throw new LeagueDomainException('PARTICIPANT_DUPLICATE', 422, 'Nome o posto già utilizzato nella lega.');
        }

        return response()->json(['data' => $participant->refresh()]);
    }

    public function removeParticipant(FantasyLeague $league, LeagueParticipant $participant, RemoveLeagueParticipant $action): JsonResponse
    {
        $this->authorizeLeague('manage', $league);
        $this->ensureParticipant($league, $participant);
        $action->execute($participant);

        return response()->json([], 204);
    }

    private function ensureParticipant(FantasyLeague $league, LeagueParticipant $participant): void
    {
        abort_unless($participant->fantasy_league_id === $league->id, 404);
    }

    private function authorizeLeague(string $ability, FantasyLeague $league): void
    {
        if (Gate::denies($ability, $league)) {
            throw new LeagueDomainException('LEAGUE_FORBIDDEN', 403, 'Accesso alla lega non consentito.');
        }
    }
}
