#!/usr/bin/env python3
"""
Merge base and scenario YAML files into a single configuration.

Usage:
  python3 merge-scenarios.py --base lab-config/base.yml --scenarios lab-config/scenarios --output /tmp/merged.yml
  python3 merge-scenarios.py --base lab-config/base.yml --scenarios scenarios/a.yml scenarios/b.yml --output /tmp/merged.yml
  python3 merge-scenarios.py --base lab-config/base.yml --scenarios lab-config/scenarios --validate-only
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return data


def gather_scenario_files(scenarios: List[str]) -> List[Path]:
    if len(scenarios) == 1 and Path(scenarios[0]).is_dir():
        scenario_dir = Path(scenarios[0])
        files = sorted(
            [p for p in scenario_dir.iterdir() if p.suffix in {".yml", ".yaml"}]
        )
        if not files:
            raise FileNotFoundError(f"No scenario files found in {scenario_dir}")
        return files
    return [Path(p) for p in scenarios]


def merge_lab(base_lab: Dict[str, Any], scenario_lab: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base_lab)
    merged.update(scenario_lab)
    return merged


def merge_lists(base_list: List[Dict[str, Any]], scenario_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return base_list + scenario_list


def validate_unique(items: List[Dict[str, Any]], key: str, label: str, source_map: Dict[str, str]) -> List[str]:
    errors = []
    seen = {}
    for item in items:
        value = item.get(key)
        if not value:
            continue
        if value in seen:
            errors.append(
                f"Duplicate {label} '{value}' found in {source_map.get(value, 'unknown')} and {item.get('__source__', 'unknown')}"
            )
        else:
            seen[value] = True
            source_map[value] = item.get('__source__', 'unknown')
    return errors


def validate_references(config: Dict[str, Any]) -> List[str]:
    errors = []
    users = {u.get("username") for u in config.get("users", [])}
    groups = {g.get("path") for g in config.get("groups", [])}
    projects = {p.get("path") for p in config.get("projects", [])}

    for group in config.get("groups", []):
        for member in group.get("members", []):
            username = member.get("username")
            if username and username not in users:
                errors.append(f"Group '{group.get('path')}' references missing user '{username}'")

    for project in config.get("projects", []):
        group = project.get("group")
        if group and group not in groups:
            errors.append(f"Project '{project.get('path')}' references missing group '{group}'")

    for runner in config.get("runners", []):
        scope = runner.get("scope")
        target = runner.get("scope_target")
        if scope == "group" and target and target not in groups:
            errors.append(f"Runner '{runner.get('description')}' references missing group '{target}'")
        if scope == "project" and target and target not in projects:
            errors.append(f"Runner '{runner.get('description')}' references missing project '{target}'")

    return errors


def merge_configs(base_config: Dict[str, Any], scenario_configs: List[Tuple[Path, Dict[str, Any]]]) -> Dict[str, Any]:
    merged = {
        "lab": base_config.get("lab", {}),
        "users": base_config.get("users", []),
        "groups": base_config.get("groups", []),
        "projects": base_config.get("projects", []),
        "runners": base_config.get("runners", []),
    }

    for path, scenario in scenario_configs:
        scenario_lab = scenario.get("lab", {})
        if scenario_lab:
            merged["lab"] = merge_lab(merged.get("lab", {}), scenario_lab)

        for section in ["users", "groups", "projects", "runners"]:
            items = scenario.get(section, [])
            for item in items:
                if isinstance(item, dict):
                    item["__source__"] = path.name
            merged[section] = merge_lists(merged.get(section, []), items)

    return merged


def validate_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    source_map = {}

    errors += validate_unique(config.get("users", []), "username", "user", source_map)
    errors += validate_unique(config.get("groups", []), "path", "group", source_map)
    errors += validate_unique(config.get("projects", []), "path", "project", source_map)
    errors += validate_unique(config.get("runners", []), "description", "runner", source_map)
    errors += validate_references(config)

    return errors


def strip_source_markers(config: Dict[str, Any]) -> None:
    for section in ["users", "groups", "projects", "runners"]:
        for item in config.get(section, []):
            if isinstance(item, dict) and "__source__" in item:
                del item["__source__"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge base and scenario YAML files")
    parser.add_argument("--base", required=True, help="Base YAML file path")
    parser.add_argument("--scenarios", nargs="+", required=True, help="Scenario directory or list of scenario files")
    parser.add_argument("--output", help="Output merged YAML file path")
    parser.add_argument("--validate-only", action="store_true", help="Validate only, do not write output")

    args = parser.parse_args()

    base_path = Path(args.base)
    if not base_path.exists():
        print(f"Base file not found: {base_path}", file=sys.stderr)
        return 1

    scenario_files = gather_scenario_files(args.scenarios)
    for path in scenario_files:
        if not path.exists():
            print(f"Scenario file not found: {path}", file=sys.stderr)
            return 1

    base_config = load_yaml(base_path)
    scenario_configs = [(path, load_yaml(path)) for path in scenario_files]

    merged = merge_configs(base_config, scenario_configs)
    errors = validate_config(merged)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    strip_source_markers(merged)

    if args.validate_only:
        print("Validation successful")
        return 0

    if not args.output:
        print("--output is required unless --validate-only is set", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        yaml.safe_dump(merged, f, sort_keys=False)

    print(f"Merged configuration written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
