<?php

return [
    'name' => env('APP_NAME', 'GitLab Attack Lab'),
    'env' => env('APP_ENV', 'production'),
    'debug' => env('APP_DEBUG', false),
    'url' => env('APP_URL', ''),
    'asset_url' => env('ASSET_URL', ''),
    'timezone' => 'UTC',
    'locale' => 'en',
    'fallback_locale' => 'en',
    'faker_locale' => 'en_US',
    'key' => env('APP_KEY'),
    'cipher' => 'AES-256-CBC',
    'log' => env('LOG_CHANNEL', 'single'),
    'log_level' => env('LOG_LEVEL', 'debug'),

    'scenarios_path' => env('SCENARIOS_PATH', base_path('../lab-config/scenarios')),
];
