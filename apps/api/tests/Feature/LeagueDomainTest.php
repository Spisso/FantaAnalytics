<?php

namespace Tests\Feature;

use App\Actions\Leagues\CreateFantasyLeague;
use App\Models\User;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class LeagueDomainTest extends TestCase
{
    use RefreshDatabase;

    private User $owner;

    protected function setUp(): void
    {
        parent::setUp();
        $this->owner = User::factory()->create();
    }

    private function headers(?User $user = null): array
    {
        return ['X-User-ID' => (string) ($user ?? $this->owner)->id];
    }

    private function payload(array $overrides = []): array
    {
        return [...[
            'name' => 'Lega Test', 'season' => '2026-27', 'participant_limit' => 4,
            'starting_budget' => 500, 'minimum_bid' => 1,
        ], ...$overrides];
    }

    public function test_creation_builds_complete_aggregate_and_hides_password(): void
    {
        $response = $this->withHeaders($this->headers())->postJson('/api/v1/leagues', $this->payload());
        $response->assertCreated()->assertJsonPath('data.rules.goal_bonus', '3.00')
            ->assertJsonPath('data.roster_rules.goalkeepers', 3)
            ->assertJsonCount(1, 'data.participants');
        $this->assertDatabaseHas('league_participants', ['user_id' => $this->owner->id, 'seat_number' => 1]);
        $this->assertArrayNotHasKey('password', $this->owner->toArray());
    }

    public function test_creation_rolls_back_on_duplicate_owner_slug(): void
    {
        $action = app(CreateFantasyLeague::class);
        $action->execute($this->owner, $this->payload(['slug' => 'same']));
        try {
            $action->execute($this->owner, $this->payload(['slug' => 'same']));
        } catch (UniqueConstraintViolationException) {
        }
        $this->assertDatabaseCount('fantasy_leagues', 1);
        $this->assertDatabaseCount('league_rules', 1);
    }

    public function test_owner_crud_and_external_user_is_forbidden(): void
    {
        $league = app(CreateFantasyLeague::class)->execute($this->owner, $this->payload());
        $external = User::factory()->create();
        $this->withHeaders($this->headers($external))->getJson("/api/v1/leagues/{$league->id}")
            ->assertForbidden()->assertJsonPath('error.code', 'LEAGUE_FORBIDDEN');
        $this->withHeaders($this->headers())->patchJson("/api/v1/leagues/{$league->id}", ['name' => 'Nuovo nome'])
            ->assertOk()->assertJsonPath('data.name', 'Nuovo nome');
        $this->withHeaders($this->headers($external))->deleteJson("/api/v1/leagues/{$league->id}")->assertForbidden();
        $this->withHeaders($this->headers())->deleteJson("/api/v1/leagues/{$league->id}")->assertNoContent();
    }

    public function test_registered_participant_can_read_but_not_update(): void
    {
        $league = app(CreateFantasyLeague::class)->execute($this->owner, $this->payload());
        $member = User::factory()->create();
        $league->participants()->create(['user_id' => $member->id, 'display_name' => 'Membro', 'initial_budget' => 500, 'remaining_budget' => 500, 'status' => 'active', 'seat_number' => 2]);
        $this->withHeaders($this->headers($member))->getJson("/api/v1/leagues/{$league->id}")->assertOk();
        $this->withHeaders($this->headers($member))->patchJson("/api/v1/leagues/{$league->id}", ['name' => 'No'])->assertForbidden();
    }

    public function test_rules_and_roster_rules_update_and_validate(): void
    {
        $league = app(CreateFantasyLeague::class)->execute($this->owner, $this->payload());
        $this->withHeaders($this->headers())->putJson("/api/v1/leagues/{$league->id}/rules", [
            'goal_bonus' => 4, 'defence_modifier_enabled' => true, 'custom_rules' => ['bonus' => 1],
        ])->assertOk()->assertJsonPath('data.defence_modifier_enabled', true);
        $this->withHeaders($this->headers())->putJson("/api/v1/leagues/{$league->id}/rules", ['red_card_penalty' => 2])
            ->assertUnprocessable()->assertJsonPath('error.code', 'INVALID_LEAGUE_RULES');
        $this->withHeaders($this->headers())->putJson("/api/v1/leagues/{$league->id}/roster-rules", [
            'goalkeepers' => 2, 'defenders' => 7, 'midfielders' => 7, 'forwards' => 5,
        ])->assertOk()->assertJsonPath('data.forwards', 5);
        $this->withHeaders($this->headers())->putJson("/api/v1/leagues/{$league->id}/roster-rules", [
            'goalkeepers' => 0, 'defenders' => 0, 'midfielders' => 0, 'forwards' => 0,
        ])->assertUnprocessable()->assertJsonPath('error.code', 'INVALID_ROSTER_RULES');
    }

    public function test_guest_participants_duplicates_limit_and_owner_removal(): void
    {
        $league = app(CreateFantasyLeague::class)->execute($this->owner, $this->payload(['participant_limit' => 2]));
        $url = "/api/v1/leagues/{$league->id}/participants";
        $guest = $this->withHeaders($this->headers())->postJson($url, ['display_name' => 'Ospite', 'seat_number' => 2])
            ->assertCreated()->assertJsonPath('data.user_id', null)->json('data');
        $this->withHeaders($this->headers())->postJson($url, ['display_name' => 'Altro', 'seat_number' => 3])
            ->assertUnprocessable()->assertJsonPath('error.code', 'PARTICIPANT_LIMIT_REACHED');
        $ownerParticipant = $league->participants()->where('user_id', $this->owner->id)->firstOrFail();
        $this->withHeaders($this->headers())->deleteJson("{$url}/{$ownerParticipant->id}")
            ->assertUnprocessable()->assertJsonPath('error.code', 'OWNER_CANNOT_BE_REMOVED');
        $this->withHeaders($this->headers())->deleteJson("{$url}/{$guest['id']}")->assertNoContent();
    }

    public function test_duplicate_name_and_seat_are_controlled(): void
    {
        $league = app(CreateFantasyLeague::class)->execute($this->owner, $this->payload());
        $url = "/api/v1/leagues/{$league->id}/participants";
        $this->withHeaders($this->headers())->postJson($url, ['display_name' => 'Ospite', 'seat_number' => 2])->assertCreated();
        $this->withHeaders($this->headers())->postJson($url, ['display_name' => 'Ospite', 'seat_number' => 3])
            ->assertUnprocessable()->assertJsonPath('error.code', 'PARTICIPANT_DUPLICATE');
    }
}
