#!/usr/bin/env python3
"""
Tests for CI/CD template validation and loading
"""

import os
import sys
import unittest
import tempfile
import yaml
import importlib.util
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import with proper name (script is populate-gitlab.py with hyphen)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "populate_gitlab",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'populate-gitlab.py')
)
populate_gitlab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(populate_gitlab)
GitLabPopulator = populate_gitlab.GitLabPopulator


class TestCITemplates(unittest.TestCase):
    """Test CI/CD template functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.populator = GitLabPopulator(
            gitlab_url="http://test.local",
            admin_token="test-token",
            config_base_path=self.temp_dir
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_existing_template(self):
        """Test validation of existing CI template"""
        template_content = """
stages:
  - test

test_job:
  stage: test
  script:
    - echo "Testing"
"""
        template_path = os.path.join(self.temp_dir, "test-template.yml")
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        # Test with relative path
        result = self.populator._validate_ci_template("test-template.yml")
        self.assertTrue(result, "Valid template should pass validation")
    
    def test_validate_missing_template(self):
        """Test validation of missing CI template"""
        result = self.populator._validate_ci_template("nonexistent-template.yml")
        self.assertFalse(result, "Missing template should fail validation")
    
    def test_validate_empty_template(self):
        """Test validation of empty CI template"""
        template_path = os.path.join(self.temp_dir, "empty-template.yml")
        with open(template_path, 'w') as f:
            f.write("")
        
        result = self.populator._validate_ci_template("empty-template.yml")
        self.assertFalse(result, "Empty template should fail validation")
    
    def test_validate_invalid_yaml(self):
        """Test validation of invalid YAML template"""
        template_content = """
stages:
  - test
invalid yaml syntax here: [unclosed
"""
        template_path = os.path.join(self.temp_dir, "invalid-template.yml")
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        result = self.populator._validate_ci_template("invalid-template.yml")
        self.assertFalse(result, "Invalid YAML should fail validation")
    
    def test_load_template_file(self):
        """Test loading CI template content"""
        template_content = """stages:
  - build

build_job:
  stage: build
  script:
    - echo "Building"
"""
        template_path = os.path.join(self.temp_dir, "load-test.yml")
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        result = self.populator._load_ci_template_file("load-test.yml")
        self.assertIsNotNone(result, "Should load template content")
        self.assertIn("build_job", result, "Content should contain job definition")
    
    def test_load_missing_template(self):
        """Test loading missing CI template"""
        result = self.populator._load_ci_template_file("missing.yml")
        self.assertIsNone(result, "Should return None for missing template")


class TestCITemplateIntegration(unittest.TestCase):
    """Integration tests for CI templates in scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Get the lab-config directory path
        self.lab_config_dir = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'lab-config'
        )
    
    def test_all_scenario_templates_exist(self):
        """Test that all CI templates referenced in scenarios exist"""
        scenarios_dir = os.path.join(self.lab_config_dir, 'scenarios')
        templates_dir = os.path.join(self.lab_config_dir, 'ci-templates')
        
        if not os.path.exists(scenarios_dir):
            self.skipTest("Scenarios directory not found")
        
        # Collect all template references
        template_refs = set()
        for scenario_file in os.listdir(scenarios_dir):
            if scenario_file.endswith('.yml'):
                scenario_path = os.path.join(scenarios_dir, scenario_file)
                with open(scenario_path, 'r') as f:
                    try:
                        scenario_data = yaml.safe_load(f)
                        if scenario_data and 'projects' in scenario_data:
                            for project in scenario_data['projects']:
                                if 'ci_cd_template' in project:
                                    template_refs.add(project['ci_cd_template'])
                    except yaml.YAMLError as e:
                        self.fail(f"Failed to parse {scenario_file}: {e}")
        
        # Verify each template exists
        for template_ref in template_refs:
            template_path = os.path.join(self.lab_config_dir, template_ref)
            self.assertTrue(
                os.path.exists(template_path),
                f"Template not found: {template_ref}"
            )
    
    def test_all_templates_are_valid_yaml(self):
        """Test that all CI templates are valid YAML"""
        templates_dir = os.path.join(self.lab_config_dir, 'ci-templates')
        
        if not os.path.exists(templates_dir):
            self.skipTest("CI templates directory not found")
        
        for template_file in os.listdir(templates_dir):
            if template_file.endswith('.yml'):
                template_path = os.path.join(templates_dir, template_file)
                with open(template_path, 'r') as f:
                    try:
                        content = yaml.safe_load(f)
                        self.assertIsNotNone(content, f"Template {template_file} is empty")
                        self.assertIsInstance(content, dict, f"Template {template_file} should be a dictionary")
                    except yaml.YAMLError as e:
                        self.fail(f"Template {template_file} has invalid YAML: {e}")
    
    def test_no_inline_ci_cd_files(self):
        """Test that no scenarios use inline ci_cd_file (deprecated)"""
        scenarios_dir = os.path.join(self.lab_config_dir, 'scenarios')
        
        if not os.path.exists(scenarios_dir):
            self.skipTest("Scenarios directory not found")
        
        for scenario_file in os.listdir(scenarios_dir):
            if scenario_file.endswith('.yml'):
                scenario_path = os.path.join(scenarios_dir, scenario_file)
                with open(scenario_path, 'r') as f:
                    content = f.read()
                    self.assertNotIn(
                        'ci_cd_file:',
                        content,
                        f"Scenario {scenario_file} should not use inline ci_cd_file (use ci_cd_template instead)"
                    )


if __name__ == '__main__':
    unittest.main()
