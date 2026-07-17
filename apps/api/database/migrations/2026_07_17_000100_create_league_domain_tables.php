<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('fantasy_leagues', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('owner_id')->constrained('users')->cascadeOnDelete();
            $table->string('name');
            $table->string('slug');
            $table->string('season', 7);
            $table->unsignedSmallInteger('participant_limit')->default(10);
            $table->unsignedInteger('starting_budget')->default(500);
            $table->unsignedInteger('minimum_bid')->default(1);
            $table->string('status')->default('draft');
            $table->timestamps();
            $table->unique(['owner_id', 'slug']);
        });

        Schema::create('league_rules', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('fantasy_league_id')->unique()->constrained()->cascadeOnDelete();
            $table->decimal('goal_bonus', 5, 2)->default(3);
            $table->decimal('assist_bonus', 5, 2)->default(1);
            $table->decimal('yellow_card_penalty', 5, 2)->default(-0.5);
            $table->decimal('red_card_penalty', 5, 2)->default(-1);
            $table->decimal('missed_penalty_penalty', 5, 2)->default(-3);
            $table->decimal('saved_penalty_bonus', 5, 2)->default(3);
            $table->decimal('clean_sheet_bonus', 5, 2)->default(0);
            $table->string('goals_conceded_rule')->default('minus_one_each');
            $table->boolean('defence_modifier_enabled')->default(false);
            $table->boolean('captain_enabled')->default(false);
            $table->json('custom_rules')->nullable();
            $table->timestamps();
        });

        Schema::create('league_roster_rules', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('fantasy_league_id')->unique()->constrained()->cascadeOnDelete();
            $table->unsignedSmallInteger('goalkeepers')->default(3);
            $table->unsignedSmallInteger('defenders')->default(8);
            $table->unsignedSmallInteger('midfielders')->default(8);
            $table->unsignedSmallInteger('forwards')->default(6);
            $table->timestamps();
        });

        Schema::create('league_participants', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('fantasy_league_id')->constrained()->cascadeOnDelete();
            $table->foreignId('user_id')->nullable()->constrained()->nullOnDelete();
            $table->string('display_name');
            $table->unsignedInteger('initial_budget');
            $table->unsignedInteger('remaining_budget');
            $table->string('status')->default('invited');
            $table->unsignedSmallInteger('seat_number');
            $table->timestamps();
            $table->unique(['fantasy_league_id', 'display_name']);
            $table->unique(['fantasy_league_id', 'seat_number']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('league_participants');
        Schema::dropIfExists('league_roster_rules');
        Schema::dropIfExists('league_rules');
        Schema::dropIfExists('fantasy_leagues');
    }
};
