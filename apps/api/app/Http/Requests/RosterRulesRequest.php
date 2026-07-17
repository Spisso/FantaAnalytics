<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class RosterRulesRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'goalkeepers' => ['required', 'integer', 'between:1,10'],
            'defenders' => ['required', 'integer', 'between:1,20'],
            'midfielders' => ['required', 'integer', 'between:1,20'],
            'forwards' => ['required', 'integer', 'between:1,20'],
        ];
    }
}
