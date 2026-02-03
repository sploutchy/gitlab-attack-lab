#!/usr/bin/env python3
"""
Validate CI/CD templates and scenario configurations
"""

import os
import sys
import yaml
from pathlib import Path


def validate_templates(lab_config_dir):
    """Validate all CI templates exist and are valid YAML"""
    templates_dir = os.path.join(lab_config_dir, 'ci-templates')
    
    if not os.path.exists(templates_dir):
        print(f"❌ CI templates directory not found: {templates_dir}")
        return False
    
    templates = [f for f in os.listdir(templates_dir) if f.endswith('.yml')]
    
    if not templates:
        print(f"⚠️  No templates found in {templates_dir}")
        return False
    
    print(f"\n📋 Found {len(templates)} CI templates:")
    
    all_valid = True
    for template_file in sorted(templates):
        template_path = os.path.join(templates_dir, template_file)
        try:
            with open(template_path, 'r') as f:
                content = yaml.safe_load(f)
                if not content:
                    print(f"  ❌ {template_file}: Empty file")
                    all_valid = False
                elif not isinstance(content, dict):
                    print(f"  ❌ {template_file}: Invalid structure (must be dict)")
                    all_valid = False
                else:
                    print(f"  ✅ {template_file}: Valid")
        except yaml.YAMLError as e:
            print(f"  ❌ {template_file}: Invalid YAML - {e}")
            all_valid = False
        except Exception as e:
            print(f"  ❌ {template_file}: Error - {e}")
            all_valid = False
    
    return all_valid


def validate_scenarios(lab_config_dir):
    """Validate scenario files reference valid templates"""
    scenarios_dir = os.path.join(lab_config_dir, 'scenarios')
    templates_dir = os.path.join(lab_config_dir, 'ci-templates')
    
    if not os.path.exists(scenarios_dir):
        print(f"❌ Scenarios directory not found: {scenarios_dir}")
        return False
    
    scenarios = [f for f in os.listdir(scenarios_dir) if f.endswith('.yml')]
    
    if not scenarios:
        print(f"⚠️  No scenarios found in {scenarios_dir}")
        return False
    
    print(f"\n📋 Validating {len(scenarios)} scenarios:")
    
    all_valid = True
    for scenario_file in sorted(scenarios):
        scenario_path = os.path.join(scenarios_dir, scenario_file)
        print(f"\n  📄 {scenario_file}:")
        
        try:
            with open(scenario_path, 'r') as f:
                scenario_data = yaml.safe_load(f)
            
            if not scenario_data:
                print(f"    ⚠️  Empty scenario file")
                continue
            
            # Check for deprecated inline ci_cd_file
            with open(scenario_path, 'r') as f:
                content = f.read()
                if 'ci_cd_file:' in content:
                    print(f"    ❌ Uses deprecated 'ci_cd_file' (use 'ci_cd_template' instead)")
                    all_valid = False
            
            # Check projects
            if 'projects' not in scenario_data:
                print(f"    ⚠️  No projects defined")
                continue
            
            for project in scenario_data['projects']:
                project_name = project.get('name', '<unnamed>')
                ci_enabled = project.get('ci_cd_enabled', False)
                ci_template = project.get('ci_cd_template')
                
                if ci_enabled and not ci_template:
                    print(f"    ⚠️  Project '{project_name}': CI/CD enabled but no template specified")
                elif ci_template:
                    # Check if template exists
                    template_path = os.path.join(lab_config_dir, ci_template)
                    if os.path.exists(template_path):
                        print(f"    ✅ Project '{project_name}': Template found ({ci_template})")
                    else:
                        print(f"    ❌ Project '{project_name}': Template not found ({ci_template})")
                        all_valid = False
        
        except yaml.YAMLError as e:
            print(f"    ❌ Invalid YAML: {e}")
            all_valid = False
        except Exception as e:
            print(f"    ❌ Error: {e}")
            all_valid = False
    
    return all_valid


def main():
    # Find lab-config directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    lab_config_dir = os.path.join(project_root, 'lab-config')
    
    if not os.path.exists(lab_config_dir):
        print(f"❌ Lab config directory not found: {lab_config_dir}")
        sys.exit(1)
    
    print("=" * 60)
    print("CI/CD Template Validation")
    print("=" * 60)
    
    templates_valid = validate_templates(lab_config_dir)
    scenarios_valid = validate_scenarios(lab_config_dir)
    
    print("\n" + "=" * 60)
    if templates_valid and scenarios_valid:
        print("✅ All validations passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Validation failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
