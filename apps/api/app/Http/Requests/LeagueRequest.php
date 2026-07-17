<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class LeagueRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        $required = $this->isMethod('post') ? 'required' : 'sometimes';

        return [
            'name' => [$required, 'string', 'max:120'],
            'slug' => ['sometimes', 'string', 'max:120'],
            'season' => [$required, 'regex:/^\d{4}-\d{2}$/'],
            'participant_limit' => [$required, 'integer', 'between:1,50'],
            'starting_budget' => [$required, 'integer', 'min:1'],
            'minimum_bid' => [$required, 'integer', 'min:1', 'lte:starting_budget'],
            'status' => ['sometimes', Rule::in(['draft', 'active', 'auction', 'completed', 'archived'])],
        ];
    }
}
