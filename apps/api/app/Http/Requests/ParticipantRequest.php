<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class ParticipantRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'user_id' => ['sometimes', 'nullable', 'integer', 'exists:users,id'],
            'display_name' => [$this->isMethod('post') ? 'required' : 'sometimes', 'string', 'max:100'],
            'seat_number' => [$this->isMethod('post') ? 'required' : 'sometimes', 'integer', 'min:1'],
            'remaining_budget' => ['sometimes', 'integer', 'min:0'],
            'status' => ['sometimes', Rule::in(['invited', 'active', 'removed'])],
        ];
    }
}
