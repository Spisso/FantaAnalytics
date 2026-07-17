<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class LeagueRule extends Model
{
    protected $guarded = [];

    protected function casts(): array
    {
        return [
            'goal_bonus' => 'decimal:2', 'assist_bonus' => 'decimal:2',
            'yellow_card_penalty' => 'decimal:2', 'red_card_penalty' => 'decimal:2',
            'missed_penalty_penalty' => 'decimal:2', 'saved_penalty_bonus' => 'decimal:2',
            'clean_sheet_bonus' => 'decimal:2', 'defence_modifier_enabled' => 'boolean',
            'captain_enabled' => 'boolean', 'custom_rules' => 'array',
        ];
    }

    public function league(): BelongsTo
    {
        return $this->belongsTo(FantasyLeague::class, 'fantasy_league_id');
    }
}
