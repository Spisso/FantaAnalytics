<?php

namespace App\Policies;

use App\Models\FantasyLeague;
use App\Models\User;

class FantasyLeaguePolicy
{
    public function view(User $user, FantasyLeague $league): bool
    {
        return $league->owner_id === $user->id || $league->participants()->where('user_id', $user->id)->exists();
    }

    public function update(User $user, FantasyLeague $league): bool
    {
        return $league->owner_id === $user->id;
    }

    public function delete(User $user, FantasyLeague $league): bool
    {
        return $league->owner_id === $user->id;
    }

    public function manage(User $user, FantasyLeague $league): bool
    {
        return $league->owner_id === $user->id;
    }
}
