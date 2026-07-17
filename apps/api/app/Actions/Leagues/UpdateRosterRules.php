<?php

namespace App\Actions\Leagues;

use App\Models\FantasyLeague;
use App\Models\LeagueRosterRule;

class UpdateRosterRules
{
    public function execute(FantasyLeague $league, array $data): LeagueRosterRule
    {
        $league->rosterRules()->update($data);

        return $league->rosterRules->refresh();
    }
}
