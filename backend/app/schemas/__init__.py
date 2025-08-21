"""
Pydantic schemas for request/response validation.
Dynamically exports all schemas from all schema modules.
"""

import os
import importlib
import inspect
from pathlib import Path

# Get the directory of this __init__.py file
SCHEMAS_DIR = Path(__file__).parent

# Dictionary to store all imported classes
_all_schemas = {}

# List of module names to import from (exclude __init__.py and __pycache__)
schema_modules = []
for file in SCHEMAS_DIR.glob("*.py"):
    if file.name != "__init__.py" and not file.name.startswith("_"):
        module_name = file.stem
        schema_modules.append(module_name)

# Import all classes from each schema module
for module_name in schema_modules:
    try:
        # Import the module
        module = importlib.import_module(f".{module_name}", package="app.schemas")
        
        # Get all classes from the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Only import classes defined in this module (not imported ones)
            if obj.__module__ == f"app.schemas.{module_name}":
                _all_schemas[name] = obj
                # Make it available at package level
                globals()[name] = obj
                
    except ImportError as e:
        print(f"Warning: Could not import schemas from {module_name}: {e}")
        continue

# Generate __all__ list for explicit exports
__all__ = list(_all_schemas.keys())

# Sort for consistency
__all__.sort()

print(f"Loaded {len(__all__)} schemas from {len(schema_modules)} modules")