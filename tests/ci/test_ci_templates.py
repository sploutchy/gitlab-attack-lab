#!/usr/bin/env python3
"""
Tests for CI/CD template validation and loading.
"""

import os
import sys
import tempfile
import unittest
import importlib.util

import pytest
import yaml


pytestmark = pytest.mark.ci

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "scripts", "populate-gitlab.py")

spec = importlib.util.spec_from_file_location("populate_gitlab", SCRIPT_PATH)
populate_gitlab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(populate_gitlab)
GitLabPopulator = populate_gitlab.GitLabPopulator


class TestCITemplates(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.populator = GitLabPopulator(
            gitlab_url="http://test.local",
            admin_token="test-token",
            config_base_path=self.temp_dir,
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_existing_template(self):
        template_path = os.path.join(self.temp_dir, "test-template.yml")
        with open(template_path, "w", encoding="utf-8") as handle:
            handle.write(
                """
stages:
  - test

test_job:
  stage: test
  script:
    - echo \"Testing\"
"""
            )

        assert self.populator._validate_ci_template("test-template.yml") is True

    def test_validate_missing_template(self):
        assert self.populator._validate_ci_template("nonexistent-template.yml") is False

    def test_validate_empty_template(self):
        template_path = os.path.join(self.temp_dir, "empty-template.yml")
        with open(template_path, "w", encoding="utf-8") as handle:
            handle.write("")

        assert self.populator._validate_ci_template("empty-template.yml") is False

    def test_validate_invalid_yaml(self):
        template_path = os.path.join(self.temp_dir, "invalid-template.yml")
        with open(template_path, "w", encoding="utf-8") as handle:
            handle.write("stages:\n  - test\ninvalid yaml syntax here: [unclosed\n")

        assert self.populator._validate_ci_template("invalid-template.yml") is False

    def test_load_template_file(self):
        template_path = os.path.join(self.temp_dir, "load-test.yml")
        with open(template_path, "w", encoding="utf-8") as handle:
            handle.write(
                """stages:
  - build

build_job:
  stage: build
  script:
    - echo \"Building\"
"""
            )

        result = self.populator._load_ci_template_file("load-test.yml")
        assert result is not None
        assert "build_job" in result

    def test_load_missing_template(self):
        assert self.populator._load_ci_template_file("missing.yml") is None


class TestCITemplateIntegration(unittest.TestCase):
    def setUp(self):
        self.lab_config_dir = os.path.join(PROJECT_ROOT, "lab-config")

    def test_all_scenario_templates_exist(self):
        scenarios_dir = os.path.join(self.lab_config_dir, "scenarios")
        template_refs = set()

        for scenario_file in os.listdir(scenarios_dir):
            if not scenario_file.endswith(".yml"):
                continue
            scenario_path = os.path.join(scenarios_dir, scenario_file)
            with open(scenario_path, "r", encoding="utf-8") as handle:
                scenario_data = yaml.safe_load(handle)
            if not scenario_data:
                continue
            for project in scenario_data.get("projects", []):
                if "ci_cd_template" in project:
                    template_refs.add(project["ci_cd_template"])

        for template_ref in template_refs:
            assert os.path.exists(os.path.join(self.lab_config_dir, template_ref)), template_ref

    def test_all_templates_are_valid_yaml(self):
        templates_dir = os.path.join(self.lab_config_dir, "ci-templates")

        for template_file in os.listdir(templates_dir):
            if not template_file.endswith(".yml"):
                continue
            with open(os.path.join(templates_dir, template_file), "r", encoding="utf-8") as handle:
                content = yaml.safe_load(handle)
            assert content is not None, f"Template {template_file} is empty"
            assert isinstance(content, dict), f"Template {template_file} should be a dictionary"

    def test_no_inline_ci_cd_files(self):
        scenarios_dir = os.path.join(self.lab_config_dir, "scenarios")

        for scenario_file in os.listdir(scenarios_dir):
            if not scenario_file.endswith(".yml"):
                continue
            content = open(os.path.join(scenarios_dir, scenario_file), "r", encoding="utf-8").read()
            assert "ci_cd_file:" not in content, scenario_file
