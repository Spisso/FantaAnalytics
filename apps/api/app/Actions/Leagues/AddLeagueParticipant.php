<?php

namespace App\Actions\Leagues;

use App\Domain\Leagues\LeagueDomainException;
use App\Models\FantasyLeague;
use App\Models\LeagueParticipant;
use Illuminate\Database\UniqueConstraintViolationException;

class AddLeagueParticipant
{
    public function execute(FantasyLeague $league, array $data): LeagueParticipant
    {
        if ($league->participants()->count() >= $league->participant_limit) {
            throw new LeagueDomainException('PARTICIPANT_LIMIT_REACHED', 422, 'Limite partecipanti raggiunto.');
        }
        if (($data['remaining_budget'] ?? $league->starting_budget) > $league->starting_budget) {
            throw new LeagueDomainException('VALIDATION_ERROR', 422, 'Il budget residuo supera il budget iniziale.');
        }
        try {
            return $league->participants()->create([
                ...$data,
                'initial_budget' => $league->starting_budget,
                'remaining_budget' => $data['remaining_budget'] ?? $league->starting_budget,
            ]);
        } catch (UniqueConstraintViolationException) {
            throw new LeagueDomainException('PARTICIPANT_DUPLICATE', 422, 'Nome o posto già utilizzato nella lega.');
        }
    }
}
