<?php

namespace Database\Seeders;

use App\Models\FantasyLeague;
use App\Models\User;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        $owner = User::updateOrCreate(['email' => 'demo@fantaanalytics.local'], [
            'name' => 'Demo Owner', 'password' => 'demo-password', 'locale' => 'it', 'timezone' => 'Europe/Rome',
        ]);
        $league = FantasyLeague::updateOrCreate(['owner_id' => $owner->id, 'slug' => 'lega-demo'], [
            'name' => 'Lega Demo', 'season' => '2026-27', 'participant_limit' => 10,
            'starting_budget' => 500, 'minimum_bid' => 1, 'status' => 'draft',
        ]);
        $league->rules()->updateOrCreate([], []);
        $league->rosterRules()->updateOrCreate([], []);
        foreach (range(1, 10) as $seat) {
            $league->participants()->updateOrCreate(['seat_number' => $seat], [
                'user_id' => $seat === 1 ? $owner->id : null,
                'display_name' => $seat === 1 ? $owner->name : "Partecipante {$seat}",
                'initial_budget' => 500, 'remaining_budget' => 500,
                'status' => $seat === 1 ? 'active' : 'invited',
            ]);
        }
    }
}
