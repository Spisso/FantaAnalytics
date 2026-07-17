<?php

namespace App\Actions\Leagues;

use App\Models\FantasyLeague;
use App\Models\LeagueRule;

class UpdateLeagueRules
{
    public function execute(FantasyLeague $league, array $data): LeagueRule
    {
        $league->rules()->update($data);

        return $league->rules->refresh();
    }
}
