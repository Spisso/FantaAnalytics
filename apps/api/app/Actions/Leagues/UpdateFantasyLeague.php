<?php

namespace App\Actions\Leagues;

use App\Domain\Leagues\LeagueDomainException;
use App\Models\FantasyLeague;

class UpdateFantasyLeague
{
    public function execute(FantasyLeague $league, array $data): FantasyLeague
    {
        if (isset($data['participant_limit']) && $data['participant_limit'] < $league->participants()->count()) {
            throw new LeagueDomainException('PARTICIPANT_LIMIT_REACHED', 422, 'Il limite è inferiore ai partecipanti esistenti.');
        }
        $budget = $data['starting_budget'] ?? $league->starting_budget;
        if (($data['minimum_bid'] ?? $league->minimum_bid) > $budget) {
            throw new LeagueDomainException('VALIDATION_ERROR', 422, 'L’offerta minima supera il budget.');
        }
        $league->update($data);

        return $league->refresh();
    }
}
