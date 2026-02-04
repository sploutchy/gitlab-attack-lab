<?php

namespace App\Http\Middleware;

use Illuminate\Foundation\Http\Middleware\EncryptCookies as Middleware;

class EncryptCookies extends Middleware
{
    /**
     * The names of the cookies that should not be encrypted.
     */
    protected $except = [
        //
    ];
}
