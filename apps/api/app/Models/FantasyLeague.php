<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;

class FantasyLeague extends Model
{
    use HasFactory;

    protected $guarded = [];

    public function owner(): BelongsTo
    {
        return $this->belongsTo(User::class, 'owner_id');
    }

    public function rules(): HasOne
    {
        return $this->hasOne(LeagueRule::class);
    }

    public function rosterRules(): HasOne
    {
        return $this->hasOne(LeagueRosterRule::class);
    }

    public function participants(): HasMany
    {
        return $this->hasMany(LeagueParticipant::class);
    }
}
