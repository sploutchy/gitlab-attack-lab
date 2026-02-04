<?php

namespace App\Services;

class FlagValidationService
{
    /**
     * Validate a submitted flag against a pattern
     */
    public function validateFlag(string $submittedFlag, string $pattern): bool
    {
        if (empty($submittedFlag) || empty($pattern)) {
            return false;
        }

        try {
            $regex = $this->normalizePattern($pattern);
            return (bool) preg_match($regex, trim($submittedFlag));
        } catch (\Exception $e) {
            return false;
        }
    }

    /**
     * Ensure regex has delimiters for preg_match
     */
    private function normalizePattern(string $pattern): string
    {
        $pattern = trim($pattern);

        if ($pattern === '') {
            return $pattern;
        }

        $first = $pattern[0];
        $last = $pattern[strlen($pattern) - 1];

        // If already delimited (e.g. /.../ or #...# or ~...~)
        if (!ctype_alnum($first) && $first === $last) {
            return $pattern;
        }

        $escaped = str_replace('~', '\\~', $pattern);
        return "~{$escaped}~";
    }

    /**
     * Validate flag against any of the scenario's flag patterns
     */
    public function validateAgainstScenario(string $submittedFlag, array $flags): ?int
    {
        foreach ($flags as $index => $flag) {
            if (!isset($flag['pattern'])) {
                continue;
            }

            if ($this->validateFlag($submittedFlag, $flag['pattern'])) {
                return $index;
            }
        }

        return null;
    }

    /**
     * Get flag name if valid
     */
    public function getFlagName(string $submittedFlag, array $flags): ?string
    {
        $index = $this->validateAgainstScenario($submittedFlag, $flags);
        
        if ($index !== null && isset($flags[$index]['name'])) {
            return $flags[$index]['name'];
        }

        return null;
    }
}
