<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class LeagueRosterRule extends Model
{
    protected $guarded = [];

    public function league(): BelongsTo
    {
        return $this->belongsTo(FantasyLeague::class, 'fantasy_league_id');
    }
}
