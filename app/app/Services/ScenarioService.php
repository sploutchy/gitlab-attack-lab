<?php

namespace App\Services;

use Illuminate\Support\Collection;
use Symfony\Component\Yaml\Yaml;

class ScenarioService
{
    /**
     * Load all scenarios from markdown files
     */
    public function getAllScenarios(): Collection
    {
        $scenariosPath = config('app.scenarios_path', '/app/scenarios');
        
        if (!is_dir($scenariosPath)) {
            return collect();
        }

        $scenarios = collect();
        $files = glob("{$scenariosPath}/*.md");

        foreach ($files as $file) {
            $scenario = $this->loadScenario($file);
            if ($scenario) {
                $scenarios->push($scenario);
            }
        }

        return $scenarios->sortBy('order')->values();
    }

    /**
     * Get a single scenario by slug
     */
    public function getScenarioBySlug(string $slug): ?array
    {
        $scenariosPath = config('app.scenarios_path', '/app/scenarios');
        $files = glob("{$scenariosPath}/*.md");

        foreach ($files as $file) {
            $scenario = $this->loadScenario($file);
            if ($scenario && $scenario['slug'] === $slug) {
                return $scenario;
            }
        }

        return null;
    }

    /**
     * Load a single scenario from markdown file
     */
    private function loadScenario(string $filePath): ?array
    {
        if (!file_exists($filePath)) {
            return null;
        }

        $content = file_get_contents($filePath);
        
        // Extract YAML frontmatter
        if (!preg_match('/^---\n(.*?)\n---\n(.*)$/s', $content, $matches)) {
            return null;
        }

        try {
            $frontmatter = Yaml::parse($matches[1]);
            $markdown = $matches[2];
        } catch (\Exception $e) {
            return null;
        }

        if (!isset($frontmatter['id']) || !isset($frontmatter['title'])) {
            return null;
        }

        $slug = $this->generateSlug($frontmatter['id']);

        return [
            'id' => $frontmatter['id'],
            'slug' => $slug,
            'title' => $frontmatter['title'],
            'difficulty' => $frontmatter['difficulty'] ?? 'beginner',
            'order' => $frontmatter['order'] ?? 999,
            'content' => $markdown,
            'flags' => $frontmatter['flags'] ?? [],
            'hints' => $frontmatter['hints'] ?? [],
            'solution' => $frontmatter['solution'] ?? null,
            'file_path' => $filePath,
        ];
    }

    /**
     * Generate URL-friendly slug from ID
     */
    private function generateSlug(string $id): string
    {
        return strtolower(str_replace('_', '-', $id));
    }

    /**
     * Get difficulty color for badge
     */
    public function getDifficultyColor(string $difficulty): string
    {
        return match($difficulty) {
            'beginner' => 'badge-success',
            'intermediate' => 'badge-warning',
            'advanced' => 'badge-error',
            default => 'badge-info',
        };
    }
}
