<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class FantasyLeagueResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id, 'owner_id' => $this->owner_id, 'name' => $this->name,
            'slug' => $this->slug, 'season' => $this->season,
            'participant_limit' => $this->participant_limit, 'starting_budget' => $this->starting_budget,
            'minimum_bid' => $this->minimum_bid, 'status' => $this->status,
            'rules' => $this->whenLoaded('rules'), 'roster_rules' => $this->whenLoaded('rosterRules'),
            'participants' => $this->whenLoaded('participants'),
        ];
    }
}
