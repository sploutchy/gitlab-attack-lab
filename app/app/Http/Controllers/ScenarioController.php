<?php

namespace App\Http\Controllers;

use App\Services\ScenarioService;
use App\Services\FlagValidationService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;
use Parsedown;

class ScenarioController extends Controller
{
    public function __construct(
        private ScenarioService $scenarioService,
        private FlagValidationService $flagValidator
    ) {}

    /**
     * Show all scenarios
     */
    public function index(): View
    {
        $scenarios = $this->scenarioService->getAllScenarios();
        
        return view('index', [
            'scenarios' => $scenarios,
        ]);
    }

    /**
     * Show a single scenario
     */
    public function show(string $slug): View
    {
        $scenario = $this->scenarioService->getScenarioBySlug($slug);
        
        if (!$scenario) {
            abort(404, "Scenario not found: {$slug}");
        }

        // Parse markdown to HTML
        $parsedown = new Parsedown();
        $htmlContent = $parsedown->text($scenario['content']);

        // Parse markdown in hints
        if (isset($scenario['hints']) && is_array($scenario['hints'])) {
            foreach ($scenario['hints'] as &$hint) {
                if (isset($hint['content'])) {
                    $hint['content'] = $parsedown->text($hint['content']);
                }
            }
        }

        // Parse markdown in solution
        if (isset($scenario['solution']) && isset($scenario['solution']['content'])) {
            $scenario['solution']['content'] = $parsedown->text($scenario['solution']['content']);
        }

        // Get found flags from session
        $foundFlags = session("scenario.{$slug}.found_flags", []);

        return view('scenario', [
            'scenario' => $scenario,
            'htmlContent' => $htmlContent,
            'foundFlags' => $foundFlags,
            'difficultyColor' => $this->scenarioService->getDifficultyColor($scenario['difficulty']),
        ]);
    }

    /**
     * Validate a submitted flag (AJAX)
     */
    public function validateFlag(Request $request, string $slug): JsonResponse
    {
        $flag = $request->input('flag');
        $scenario = $this->scenarioService->getScenarioBySlug($slug);

        if (!$scenario) {
            return response()->json([
                'success' => false,
                'message' => 'Scenario not found',
            ], 404);
        }

        if (empty($flag)) {
            return response()->json([
                'success' => false,
                'message' => 'Please enter a flag',
            ]);
        }

        // Check if flag matches any of the scenario's patterns
        $flagIndex = $this->flagValidator->validateAgainstScenario($flag, $scenario['flags']);

        if ($flagIndex === null) {
            return response()->json([
                'success' => false,
                'message' => 'Incorrect flag. Try again or check the hints in the scenario.',
            ]);
        }

        // Get found flags from session
        $sessionKey = "scenario.{$slug}.found_flags";
        $foundFlags = session($sessionKey, []);

        // Check if already found
        $flagName = $scenario['flags'][$flagIndex]['name'] ?? "Flag {$flagIndex}";
        
        if (in_array($flagName, $foundFlags)) {
            return response()->json([
                'success' => false,
                'message' => "You've already found this flag: {$flagName}",
            ]);
        }

        // Add to found flags
        $foundFlags[] = $flagName;
        session([$sessionKey => $foundFlags]);

        return response()->json([
            'success' => true,
            'message' => "✓ Correct! Flag found: {$flagName}",
            'found_count' => count($foundFlags),
            'total_flags' => count($scenario['flags']),
        ]);
    }
}
