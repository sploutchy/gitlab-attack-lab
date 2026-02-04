<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'GitLab Attack Lab')</title>
    @php
        $manifest = json_decode(file_get_contents(public_path('build/manifest.json')), true);
        $cssFile = $manifest['resources/css/app.css']['file'] ?? '';
        $jsFile = $manifest['resources/js/app.js']['file'] ?? '';
    @endphp
    @if($cssFile)
    <link rel="stylesheet" href="/build/{{ $cssFile }}">
    @endif
    @if($jsFile)
    <script type="module" src="/build/{{ $jsFile }}"></script>
    @endif
</head>
<body class="bg-base-100">
    <div class="navbar bg-base-200 shadow-lg">
        <div class="flex-1">
            <a href="/" class="btn btn-ghost text-xl font-bold">
                🏴‍☠️ GitLab Attack Lab
            </a>
        </div>
    </div>

    <main class="min-h-screen">
        @yield('content')
    </main>

    <footer class="footer footer-center bg-base-200 text-base-content p-4 mt-12">
        <p>🎓 Learn GitLab CI/CD Security through hands-on scenarios</p>
    </footer>
</body>
</html>
