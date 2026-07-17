<?php

namespace App\Http\Requests;

use App\Services\Analytics\DTO\PlayerFilters;
use Illuminate\Contracts\Validation\Validator;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Http\Exceptions\HttpResponseException;

class PlayerIndexRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'role' => ['sometimes', 'string', 'in:P,D,C,A'],
            'team' => ['sometimes', 'string', 'max:100'],
            'season' => ['sometimes', 'string', 'regex:/^\d{4}-\d{2}$/'],
            'limit' => ['sometimes', 'integer', 'between:1,200'],
        ];
    }

    public function filters(): PlayerFilters
    {
        return PlayerFilters::fromArray($this->validated());
    }

    protected function failedValidation(Validator $validator): void
    {
        throw new HttpResponseException(response()->json([
            'error' => [
                'code' => 'INVALID_FILTERS',
                'message' => 'I filtri richiesti non sono validi.',
                'request_id' => $this->attributes->get('request_id'),
                'details' => $validator->errors()->toArray(),
            ],
        ], 422));
    }
}
