<?php

namespace App\Actions\Leagues;

use App\Domain\Leagues\LeagueDomainException;
use App\Models\LeagueParticipant;

class RemoveLeagueParticipant
{
    public function execute(LeagueParticipant $participant): void
    {
        if ($participant->user_id === $participant->league->owner_id) {
            throw new LeagueDomainException('OWNER_CANNOT_BE_REMOVED', 422, 'Il proprietario non può essere rimosso.');
        }
        $participant->delete();
    }
}
