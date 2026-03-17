@extends('layouts.app')

@section('title', 'GitLab Attack Lab - Home')

@section('content')
<div class="container mx-auto px-4 py-12">
    <!-- Welcome Section -->
    <div class="text-center mb-12">
        <h1 class="text-5xl font-bold mb-4">GitLab Attack Lab - For Pipeleek</h1>
        <p class="text-lg text-base-content/70 mb-6">
            Learn and practice GitLab CI/CD security misconfigurations through interactive scenarios
        </p>
        <div class="stats shadow">
            <div class="stat">
                <div class="stat-title">Total Scenarios</div>
                <div class="stat-value text-primary">{{ count($scenarios) }}</div>
            </div>
            <div class="stat">
                <div class="stat-title">Difficulty Levels</div>
                <div class="stat-value text-secondary">3</div>
            </div>
        </div>
    </div>

    <!-- Scenarios Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        @forelse($scenarios as $scenario)
            @php $isCompleted = $completedScenarios[$scenario['slug']] ?? false; @endphp
            @if($isCompleted)
            <a href="/scenarios/{{ $scenario['slug'] }}"
               class="card bg-base-200 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 overflow-hidden"
               style="border-left: 4px solid hsl(var(--su));">
            @else
            <a href="/scenarios/{{ $scenario['slug'] }}"
               class="card bg-base-200 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200">
            @endif
                <div class="card-body">
                    {{-- Completed banner --}}
                    @if($isCompleted)
                    <div class="flex items-center gap-2 mb-3 -mt-1">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-4 h-4 text-success shrink-0"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                        <span class="text-xs font-bold text-success uppercase tracking-widest">Completed</span>
                    </div>
                    @endif

                    {{-- Title row --}}
                    <div class="flex items-start justify-between mb-2">
                        <div class="min-w-0">
                            <div class="text-xs font-semibold text-primary uppercase tracking-wide">Scenario {{ $scenario['order'] }}</div>
                            <h2 class="card-title text-lg">{{ $scenario['title'] }}</h2>
                        </div>
                        <span class="badge @if($scenario['difficulty'] === 'beginner') badge-success @elseif($scenario['difficulty'] === 'intermediate') badge-warning @else badge-error @endif shrink-0 ml-2">
                            {{ ucfirst($scenario['difficulty']) }}
                        </span>
                    </div>

                    {{-- Flag status --}}
                    @if($isCompleted)
                    <p class="text-sm font-medium mb-4" style="color:hsl(var(--su));">
                        All {{ count($scenario['flags'] ?? []) }} flag{{ count($scenario['flags'] ?? []) !== 1 ? 's' : '' }} found ✓
                    </p>
                    @else
                    <p class="text-sm text-base-content/70 mb-4">
                        @if(isset($scenario['flags']))
                            <strong>{{ count($scenario['flags']) }}</strong> flag{{ count($scenario['flags']) !== 1 ? 's' : '' }} to find
                        @else
                            No flags defined
                        @endif
                    </p>
                    @endif

                    {{-- CTA button --}}
                    <div class="card-actions justify-end">
                        @if($isCompleted)
                            <button class="btn btn-success btn-sm">
                                Review Scenario ✓
                            </button>
                        @else
                            <button class="btn btn-primary btn-sm">
                                Start Scenario →
                            </button>
                        @endif
                    </div>
                </div>
            </a>
        @empty
            <div class="alert alert-info col-span-full">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <div>
                    <h3 class="font-bold">No scenarios available</h3>
                    <div class="text-sm">Please check your scenario files in <code>lab-config/scenarios/</code></div>
                </div>
            </div>
        @endforelse
    </div>

    <!-- Getting Started -->
    <div class="divider my-12"></div>
    
    <div class="bg-base-200 rounded-lg p-8">
        <h2 class="text-2xl font-bold mb-4">🎯 How to Use</h2>
        <ol class="list-decimal list-inside space-y-3">
            <li>Select a scenario from the list above</li>
            <li>Read the scenario description and objectives</li>
            <li>Follow the steps to find flags in the GitLab instance</li>
            <li>Submit flags using the form at the bottom of the scenario page</li>
            <li>Verify your flags and progress</li>
        </ol>
    </div>
</div>
@endsection
