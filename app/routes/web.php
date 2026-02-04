<?php

use App\Http\Controllers\ScenarioController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ScenarioController::class, 'index'])->name('home');
Route::get('/scenarios/{slug}', [ScenarioController::class, 'show'])->name('scenario.show');
Route::post('/scenarios/{slug}/validate', [ScenarioController::class, 'validateFlag'])->name('flag.validate');
