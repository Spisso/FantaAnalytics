<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class LeagueRulesRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'goal_bonus' => ['sometimes', 'numeric', 'between:-20,20'],
            'assist_bonus' => ['sometimes', 'numeric', 'between:-20,20'],
            'yellow_card_penalty' => ['sometimes', 'numeric', 'between:-20,0'],
            'red_card_penalty' => ['sometimes', 'numeric', 'between:-20,0'],
            'missed_penalty_penalty' => ['sometimes', 'numeric', 'between:-20,0'],
            'saved_penalty_bonus' => ['sometimes', 'numeric', 'between:0,20'],
            'clean_sheet_bonus' => ['sometimes', 'numeric', 'between:0,20'],
            'goals_conceded_rule' => ['sometimes', Rule::in(['minus_one_each', 'none'])],
            'defence_modifier_enabled' => ['sometimes', 'boolean'],
            'captain_enabled' => ['sometimes', 'boolean'],
            'custom_rules' => ['sometimes', 'nullable', 'array'],
        ];
    }
}
