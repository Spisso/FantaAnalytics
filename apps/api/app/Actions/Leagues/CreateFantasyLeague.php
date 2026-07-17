<?php

namespace App\Actions\Leagues;

use App\Models\FantasyLeague;
use App\Models\User;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class CreateFantasyLeague
{
    public function execute(User $owner, array $data): FantasyLeague
    {
        return DB::transaction(function () use ($owner, $data): FantasyLeague {
            $league = FantasyLeague::create([
                ...$data,
                'owner_id' => $owner->id,
                'slug' => $data['slug'] ?? Str::slug($data['name']),
            ]);
            $league->rules()->create([]);
            $league->rosterRules()->create([]);
            $league->participants()->create([
                'user_id' => $owner->id,
                'display_name' => $owner->name,
                'initial_budget' => $league->starting_budget,
                'remaining_budget' => $league->starting_budget,
                'status' => 'active',
                'seat_number' => 1,
            ]);

            return $league->load(['rules', 'rosterRules', 'participants']);
        });
    }
}
