@extends('layouts.app')

@section('title', $scenario['title'] . ' - GitLab Attack Lab')

@section('content')
<div class="container mx-auto px-4 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Content -->
        <div class="lg:col-span-2">
            <!-- Header -->
            <div class="mb-8">
                <div class="flex items-center gap-4 mb-4">
                    <h1 class="text-4xl font-bold">{{ $scenario['title'] }}</h1>
                    <span class="badge {{ $difficultyColor }} badge-lg">
                        {{ ucfirst($scenario['difficulty']) }}
                    </span>
                </div>
                <a href="/" class="link link-primary text-sm">← Back to Scenarios</a>
            </div>

            <!-- Scenario Content (Markdown) -->
            <div class="prose prose-invert max-w-none bg-base-200 rounded-lg p-8 mb-8">
                <div class="markdown-content">
                    {!! $htmlContent !!}
                </div>
            </div>

            <!-- Hints Accordion -->
            @if(isset($scenario['hints']) && count($scenario['hints']) > 0)
            <div class="card bg-base-200 shadow-xl mb-8">
                <div class="card-body">
                    <h2 class="card-title mb-4">💡 Hints</h2>
                    <div class="space-y-2">
                        @foreach($scenario['hints'] as $index => $hint)
                        <div class="collapse collapse-arrow border border-base-300 bg-base-100">
                            <input type="checkbox" id="hint-{{ $index }}" class="peer" />
                            <label for="hint-{{ $index }}" class="collapse-title cursor-pointer font-medium text-sm">
                                {{ $hint['title'] ?? "Hint " . ($index + 1) }}
                            </label>
                            <div class="collapse-content peer-checked:block hidden">
                                <div class="prose prose-invert max-w-none text-base-content/80 pt-2">
                                    <style>
                                        .solution-content ol, .hint-content ol { list-style-type: decimal !important; margin-left: 1.5rem !important; }
                                        .solution-content ol li, .hint-content ol li { margin-left: 0.5rem !important; }
                                        .solution-content ul, .hint-content ul { list-style-type: disc !important; margin-left: 1.5rem !important; }
                                        .solution-content ul li, .hint-content ul li { margin-left: 0.5rem !important; }
                                    </style>
                                    <div class="hint-content">
                                        {!! $hint['content'] !!}
                                    </div>
                                </div>
                            </div>
                        </div>
                        @endforeach
                    </div>
                </div>
            </div>
            @endif

            <!-- Flag Submission Form -->
            <div class="card bg-base-200 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title flex items-center gap-2">
                        🚩 Submit Flag
                        <span class="badge badge-primary">
                            {{ count($foundFlags) }}/{{ count($scenario['flags']) }} Found
                        </span>
                    </h2>

                    @if(count($foundFlags) >= count($scenario['flags']))
                    <!-- All flags found — completion banner -->
                    <div class="alert alert-success mt-6">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span class="font-semibold">All flags found! Scenario complete 🎉</span>
                    </div>
                    @else
                    <div x-data="flagSubmissionForm()" 
                         x-init="scenarioSlug = '{{ $scenario['slug'] }}'"
                         class="mt-6 space-y-4">

                        <!-- Message Alert -->
                        <div x-show="message" 
                             :class="messageType === 'success' ? 'alert-success' : messageType === 'error' ? 'alert-error' : 'alert-info'"
                             class="alert flag-success">
                            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span x-text="message"></span>
                        </div>

                        <!-- Flag Input -->
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Enter the flag you found:</span>
                            </label>
                            <input 
                                type="text" 
                                placeholder="flag{...}"
                                x-model="flag"
                                @keydown.enter="submitFlag()"
                                :disabled="loading"
                                class="input input-bordered w-full"
                            />
                            <label class="label">
                                <span class="label-text-alt text-xs text-base-content/50">
                                    The flag format is usually <code>flag{...}</code>
                                </span>
                            </label>
                        </div>

                        <!-- Submit Button -->
                        <button 
                            @click="submitFlag()"
                            :disabled="loading"
                            class="btn btn-primary w-full"
                        >
                            <span x-show="!loading">Submit Flag</span>
                            <span x-show="loading" class="loading loading-spinner loading-sm"></span>
                        </button>
                    </div>
                    @endif

                    <!-- Found Flags List -->
                    @if(count($foundFlags) > 0)
                        <div class="mt-8 pt-8 border-t">
                            <h3 class="font-bold mb-4">✓ Flags Found</h3>
                            <div class="space-y-2">
                                @foreach($foundFlags as $foundFlag)
                                    <div class="badge badge-success gap-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline w-4 h-4 stroke-current"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                        {{ $foundFlag }}
                                    </div>
                                @endforeach
                            </div>
                        </div>
                    @endif
                </div>
            </div>

            <!-- Solution Accordion -->
            @if(isset($scenario['solution']))
            <div class="card bg-base-200 shadow-xl mt-8">
                <div class="card-body">
                    <div class="collapse collapse-arrow border border-base-300 bg-base-100">
                        <input type="checkbox" id="solution-accordion" class="peer" />
                        <label for="solution-accordion" class="collapse-title cursor-pointer font-medium text-lg flex items-center gap-2">
                            💡 {{ $scenario['solution']['title'] ?? 'Solution' }}
                        </label>
                        <div class="collapse-content peer-checked:block hidden">
                            <div class="prose prose-invert max-w-none text-base-content/80 pt-4">
                                <style>
                                    .solution-content ol, .hint-content ol { list-style-type: decimal !important; margin-left: 1.5rem !important; }
                                    .solution-content ol li, .hint-content ol li { margin-left: 0.5rem !important; }
                                    .solution-content ul, .hint-content ul { list-style-type: disc !important; margin-left: 1.5rem !important; }
                                    .solution-content ul li, .hint-content ul li { margin-left: 0.5rem !important; }
                                </style>
                                <div class="solution-content">
                                    {!! $scenario['solution']['content'] !!}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            @endif

            <!-- Next Scenario -->
            <div class="flex justify-end mt-8">
                @if($nextScenario)
                    <a id="next-scenario-btn" href="/scenarios/{{ $nextScenario['slug'] }}" class="btn btn-primary gap-2">
                        Next: {{ $nextScenario['title'] }}
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </a>
                @else
                    <a id="next-scenario-btn" href="/" class="btn btn-primary gap-2">
                        Back to Scenarios
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-4 h-4 stroke-current">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </a>
                @endif
            </div>
        </div>

        <!-- Sidebar -->
        <div class="lg:col-span-1 space-y-6">
            <!-- Flag List -->
            <div class="card bg-base-200 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-lg">Flags to Find</h2>
                    <div class="space-y-2 mt-4">
                        @forelse($scenario['flags'] as $index => $flag)
                            <div class="flex items-center gap-2 p-2 bg-base-100 rounded">
                                @if(in_array($flag['name'] ?? "Flag {$index}", $foundFlags))
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-5 h-5 text-success"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                                @else
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 text-base-content/30 stroke-current"><circle cx="12" cy="12" r="10" stroke-width="2"/></svg>
                                @endif
                                <span class="text-sm">
                                    {{ $flag['name'] ?? "Flag " . ($index + 1) }}
                                </span>
                            </div>
                        @empty
                            <p class="text-sm text-base-content/50">No flags defined</p>
                        @endforelse
                    </div>
                </div>
            </div>

            <!-- Progress -->
            <div class="card bg-base-200 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-lg">Progress</h2>
                    <progress class="progress progress-primary w-full" value="{{ count($foundFlags) }}" max="{{ count($scenario['flags']) }}"></progress>
                    <p class="text-sm text-base-content/70 mt-2">
                        {{ count($foundFlags) }} of {{ count($scenario['flags']) }} flags found
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Update flag counter on flag found event
    window.addEventListener('flag-found', (event) => {
        location.reload();
    });
</script>
@endsection
