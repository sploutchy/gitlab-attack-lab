<?php

define('LARAVEL_START', microtime(true));

if (isset($_ENV['LARAVEL_MAINTENANCE_DRIVER'])) {
    $migrator = $_ENV['LARAVEL_MAINTENANCE_DRIVER'];

    $file = __DIR__.'/../storage/framework/maintenance.php';

    if ($migrator === 'file' && file_exists($file)) {
        require $file;
    }
} else {
    switch (true) {
        case file_exists($maintenance = __DIR__.'/../storage/framework/maintenance.php'):
            require $maintenance;
            break;
    }
}

require __DIR__.'/../vendor/autoload.php';

$app = require_once __DIR__.'/../bootstrap/app.php';

$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);

$response = $kernel->handle(
    $request = Illuminate\Http\Request::capture()
)->send();

$kernel->terminate($request, $response);
