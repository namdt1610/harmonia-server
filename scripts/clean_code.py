#!/usr/bin/env python3
import subprocess
from pathlib import Path

def clean_python_files():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Find all Python files
    python_files = list(project_root.rglob("*.py"))
    
    # Exclude certain directories
    excluded_dirs = {'venv', '.git', '__pycache__', 'migrations'}
    python_files = [f for f in python_files if not any(excluded in str(f) for excluded in excluded_dirs)]
    
    print(f"Found {len(python_files)} Python files to clean")
    
    for file_path in python_files:
        print(f"\nCleaning {file_path}")
        try:
            # Run autoflake to remove unused imports and variables
            subprocess.run([
                'autoflake',
                '--in-place',
                '--remove-all-unused-imports',
                '--remove-unused-variables',
                '--recursive',
                str(file_path)
            ], check=True)
            print(f"✓ Cleaned {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error cleaning {file_path}: {e}")

if __name__ == "__main__":
    clean_python_files() 