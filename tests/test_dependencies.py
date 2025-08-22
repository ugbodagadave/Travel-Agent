import os
import ast
import re
import sys
from pathlib import Path

# Heuristic to find the project root. Assumes tests are in a 'tests' subdir.
PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

# Known mappings from a module's import name to its package name in requirements.txt
IMPORT_TO_REQUIREMENT_MAP = {
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
    "fpdf": "fpdf2",
    "PIL": "Pillow",
    "psycopg2": "psycopg2-binary",
    "eth_account": "eth-account",
    "web3": "web3",
}

# Modules to explicitly ignore because they are local packages or not on PyPI
IGNORED_MODULES = {"app"}

def get_stdlib_modules():
    """Returns a set of standard library module names."""
    try:
        # Available in Python 3.10+
        return sys.stdlib_module_names
    except AttributeError:
        # A fallback for older Python versions. This list is not exhaustive
        # but covers common modules.
        print("Warning: Using a fallback list of stdlib modules. Consider upgrading to Python 3.10+ for a more accurate list.")
        return {
            'os', 'sys', 'time', 'uuid', 'json', 're', 'logging', 'threading',
            'datetime', 'collections', 'functools', 'itertools', 'math',
            'pathlib', 'typing', 'abc', 'ast', 'importlib', 'enum'
        }

STD_LIB_MODULES = get_stdlib_modules()

def get_requirements(requirements_path):
    """Parses a requirements.txt file and returns a set of package names."""
    if not requirements_path.is_file():
        return set()
    with open(requirements_path, "r", encoding="utf-8") as f:
        reqs = [
            re.match(r"^\s*([a-zA-Z0-9_.-]+)", line).group(1).lower()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
        return set(reqs)

def get_imported_modules(app_directory):
    """Walks the app directory and uses AST to find all imported modules."""
    imported_modules = set()
    for root, _, files in os.walk(app_directory):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            file_path = Path(root) / file
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=str(file_path))
                except SyntaxError as e:
                    print(f"Warning: Could not parse {file_path} for imports: {e}")
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            top_level_module = alias.name.split(".")[0]
                            imported_modules.add(top_level_module)
                    elif isinstance(node, ast.ImportFrom):
                        # level > 0 indicates a relative import (e.g., from . import utils)
                        if node.level == 0 and node.module:
                            top_level_module = node.module.split(".")[0]
                            imported_modules.add(top_level_module)
    return imported_modules


def test_dependencies_are_in_sync():
    """
    Ensures all modules imported in the 'app' directory are listed in requirements.txt.
    This test prevents deployment failures caused by missing dependencies.
    """
    requirements = get_requirements(REQUIREMENTS_FILE)
    imported_modules = get_imported_modules(APP_DIR)

    missing_deps = set()

    for module in imported_modules:
        # Rule 1: Ignore standard library modules
        if module in STD_LIB_MODULES:
            continue
            
        # Rule 2: Ignore modules that are not external packages
        if module in IGNORED_MODULES:
            continue

        # Rule 3: Check for known name mappings (e.g., 'fpdf' is in 'fpdf2' package)
        module_name_lower = module.lower()
        requirement_name = IMPORT_TO_REQUIREMENT_MAP.get(module_name_lower, module_name_lower)

        # Rule 4: Check if the module or its mapped equivalent is in requirements
        if requirement_name not in requirements:
            missing_deps.add(module)

    assert not missing_deps, (
        f"The following imported modules are missing from requirements.txt: {sorted(list(missing_deps))}. "
        f"Please add them to ensure the deployment does not fail."
    ) 