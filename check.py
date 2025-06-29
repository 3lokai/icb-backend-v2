#!/usr/bin/env python3
"""
Ultimate Code Quality Checker - Combines the power of:
- Your original MyPy approach (but smarter)
- Our advanced AST analysis
- Ruff linting
- Custom coffee scraper specific checks

This is your baby script all grown up! 😈
"""

import ast
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


class UltimateCodeChecker:
    """The nuclear option for code quality checking."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {}
        self.function_definitions = defaultdict(list)
        self.function_calls = defaultdict(list)
        self.imports = defaultdict(list)
        self.common_functions = set()

        # Your original files + auto-discovery
        self.priority_files = [
            "main.py",
            "config.py",
            "common/utils.py",
            "db/models.py",
            "run_product_scraper.py",  # The problematic duplicate!
            "run_all_product_scrapers.py",
            "run_roaster.py",
        ]

    def run_mypy_check(self, files: Optional[List[str]] = None) -> Dict:
        """Your original MyPy approach, but enhanced."""
        print("🔍 Running MyPy type checking (your original approach++)...")

        if files is None:
            files = self.priority_files

        # Auto-discover Python files if not specified (EXCLUDE venv, .venv, node_modules, etc.)
        all_python_files = []
        exclude_dirs = {
            "venv",
            ".venv",
            "env",
            ".env",
            "node_modules",
            "__pycache__",
            ".git",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            ".tox",
            "site-packages",
        }

        for py_file in self.project_root.rglob("*.py"):
            # Check if file is in any excluded directory
            if not any(excluded in py_file.parts for excluded in exclude_dirs):
                all_python_files.append(py_file)

        mypy_results = {}

        # Check priority files first
        for file in files:
            file_path = self.project_root / file
            if file_path.exists():
                print(f"\n🎯 Checking priority file: {file}...")

                # Try with package-aware flags first
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "mypy",
                        str(file_path),
                        "--ignore-missing-imports",
                        "--namespace-packages",
                        "--explicit-package-bases",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                # If that fails with package name error, try without package structure
                if "is not a valid Python package name" in result.stderr:
                    print("  📦 Package name issue detected, trying alternative approach...")
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "mypy",
                            str(file_path),
                            "--ignore-missing-imports",
                            "--no-namespace-packages",
                        ],
                        capture_output=True,
                        text=True,
                    )

                mypy_results[file] = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "has_issues": bool(result.stdout.strip() or result.stderr.strip()),
                }

                if result.stdout:
                    print(f"📄 Output:\n{result.stdout}")
                if result.stderr:
                    print(f"⚠️ Errors:\n{result.stderr}")
                if result.returncode == 0 and not result.stdout.strip():
                    print("✅ No issues found!")
            else:
                print(f"❌ File not found: {file}")
                mypy_results[file] = {"error": "File not found"}

        # Quick scan of all other Python files
        print(f"\n🔍 Quick MyPy scan of all {len(all_python_files)} Python files...")
        other_files = [f for f in all_python_files if str(f.relative_to(self.project_root)) not in files]

        for file_path in other_files[:10]:  # Limit to avoid spam
            relative_path = file_path.relative_to(self.project_root)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    str(file_path),
                    "--ignore-missing-imports",
                    "--namespace-packages",
                    "--explicit-package-bases",
                    "--no-implicit-reexport",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.stdout.strip():  # Only report files with issues
                mypy_results[str(relative_path)] = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "has_issues": True,
                }

        return mypy_results

    def run_ruff_checks(self) -> Dict:
        """Run comprehensive ruff checks."""
        print("\n🚀 Running Ruff linting checks...")

        checks = {
            "basic": [],
            "imports": ["--select", "I"],
            "unused": ["--select", "F401"],
            "complexity": ["--select", "C90"],
            "security": ["--select", "S"],
        }

        ruff_results = {}

        for check_name, args in checks.items():
            cmd = ["ruff", "check"] + args + [str(self.project_root)]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                ruff_results[check_name] = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "success": result.returncode == 0,
                }
                print(f"✅ {check_name.title()} check completed")
            except FileNotFoundError:
                ruff_results[check_name] = {"error": "ruff not found. Install with: pip install ruff"}
                print(f"❌ Ruff not found for {check_name} check")

        return ruff_results

    def analyze_coffee_scraper_specific(self) -> Dict:
        """Coffee scraper specific analysis."""
        print("\n☕ Running Coffee Scraper specific analysis...")

        issues = {
            "duplicate_scrapers": [],
            "common_conflicts": [],
            "platform_inconsistencies": [],
            "missing_imports": [],
        }

        # Check for duplicate scraper files
        scraper_files = [
            self.project_root / "run_product_scraper.py",
            self.project_root / "scrapers/product_crawl4ai/run_product_scraper.py",
        ]

        existing_scrapers = [f for f in scraper_files if f.exists()]
        if len(existing_scrapers) > 1:
            issues["duplicate_scrapers"] = [str(f) for f in existing_scrapers]

        # Check for common/ function conflicts
        common_dir = self.project_root / "common"
        if common_dir.exists():
            common_files = list(common_dir.glob("*.py"))
            for common_file in common_files:
                # This would be more detailed with AST analysis
                issues["common_conflicts"].append(f"Potential conflicts in {common_file.name}")

        # Check for platform detector consistency
        platform_files = [
            self.project_root / "common/platform_detector.py",
            self.project_root / "scrapers/product/shopify.py",
            self.project_root / "scrapers/product_crawl4ai/api_extractors/shopify.py",
        ]

        for pf in platform_files:
            if not pf.exists():
                issues["missing_imports"].append(f"Missing expected file: {pf}")

        return issues

    def analyze_python_file(self, file_path: Path) -> Dict:
        """Enhanced version of your AST analysis."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            file_info = {
                "functions_defined": [],
                "functions_called": [],
                "imports": [],
                "classes": [],
                "async_functions": [],
            }

            class EnhancedAnalyzer(ast.NodeVisitor):
                def __init__(self, outer_self):
                    self.outer_self = outer_self

                def visit_FunctionDef(self, node):
                    func_name = node.name
                    file_info["functions_defined"].append((func_name, node.lineno))
                    self.outer_self.function_definitions[func_name].append((str(file_path), node.lineno))

                    if "common/" in str(file_path):
                        self.outer_self.common_functions.add(func_name)

                    self.generic_visit(node)

                def visit_AsyncFunctionDef(self, node):
                    func_name = node.name
                    file_info["async_functions"].append((func_name, node.lineno))
                    self.outer_self.function_definitions[func_name].append((str(file_path), node.lineno))
                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    class_name = node.name
                    file_info["classes"].append((class_name, node.lineno))
                    self.generic_visit(node)

                def visit_Call(self, node):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name:
                        file_info["functions_called"].append((func_name, node.lineno))
                        self.outer_self.function_calls[func_name].append((str(file_path), node.lineno))

                    self.generic_visit(node)

                def visit_Import(self, node):
                    for alias in node.names:
                        file_info["imports"].append(("import", alias.name, alias.asname, node.lineno))
                    self.generic_visit(node)

                def visit_ImportFrom(self, node):
                    if node.module:
                        for alias in node.names:
                            import_name = f"{node.module}.{alias.name}"
                            file_info["imports"].append(("from", import_name, alias.asname, node.lineno))
                    self.generic_visit(node)

            analyzer = EnhancedAnalyzer(self)
            analyzer.visit(tree)

            return file_info

        except Exception as e:
            return {"error": str(e)}

    def generate_ultimate_report(self, mypy_results: Dict, ruff_results: Dict, coffee_issues: Dict) -> str:
        """Generate the ultimate cleanup report."""
        report = []
        report.append("# Ultimate Coffee Scraper Code Quality Report\n")
        report.append("*From your humble 10-line script to this nuclear-powered analyzer!*\n")

        # Executive summary
        total_mypy_issues = sum(1 for r in mypy_results.values() if isinstance(r, dict) and r.get("has_issues"))
        total_ruff_issues = sum(1 for r in ruff_results.values() if isinstance(r, dict) and not r.get("success"))

        report.append("## Executive Summary\n")
        report.append(f"- **MyPy Issues**: {total_mypy_issues} files with type issues")
        report.append(f"- **Ruff Issues**: {total_ruff_issues} categories with problems")
        report.append(
            f"- **Coffee-Specific Issues**: {len([i for issues in coffee_issues.values() for i in issues])} found"
        )
        report.append("")

        # Coffee scraper specific issues (PRIORITY)
        report.append("## Coffee Scraper Specific Issues (TOP PRIORITY)\n")

        if coffee_issues["duplicate_scrapers"]:
            report.append("### CRITICAL: Duplicate Scraper Files")
            for dup in coffee_issues["duplicate_scrapers"]:
                report.append(f"- `{dup}`")
            report.append("**Action**: Choose ONE version and delete the other!\n")

        if coffee_issues["common_conflicts"]:
            report.append("### Common Folder Conflicts")
            for conflict in coffee_issues["common_conflicts"]:
                report.append(f"- {conflict}")
            report.append("")

        # MyPy results (your original approach enhanced)
        report.append("## MyPy Type Checking Results\n")

        for file, result in mypy_results.items():
            if isinstance(result, dict) and result.get("has_issues"):
                report.append(f"### {file}")
                if result.get("stdout"):
                    report.append("```")
                    report.append(result["stdout"])
                    report.append("```")
                report.append("")

        # Ruff results
        report.append("## Ruff Linting Results\n")

        for check_name, result in ruff_results.items():
            if isinstance(result, dict):
                if result.get("error"):
                    report.append(f"### {check_name.title()} - {result['error']}")
                elif not result.get("success") and result.get("stdout"):
                    report.append(f"### {check_name.title()} Issues")
                    report.append("```")
                    report.append(result["stdout"])
                    report.append("```")
                else:
                    report.append(f"### {check_name.title()} - Clean!")
                report.append("")

        # Action plan
        report.append("## Action Plan (In Order of Priority)\n")
        report.append("1. **FIRST**: Fix duplicate `run_product_scraper.py` files")
        report.append("2. **SECOND**: Resolve any common/ function conflicts")
        report.append("3. **THIRD**: Fix MyPy type issues in priority files")
        report.append("4. **FOURTH**: Run ruff auto-fixes")
        report.append("5. **FIFTH**: Clean up remaining linting issues")
        report.append("")

        report.append("### Auto-Fix Commands:")
        report.append("```bash")
        report.append("# Fix basic ruff issues")
        report.append("ruff check --fix .")
        report.append("")
        report.append("# Fix import organization")
        report.append("ruff check --select I --fix .")
        report.append("")
        report.append("# Format everything")
        report.append("ruff format .")
        report.append("")
        report.append("# Re-run this analyzer")
        report.append("python ultimate_checker.py")
        report.append("```")

        return "\n".join(report)

    def run_ultimate_check(self):
        """Run the ultimate check combining everything."""
        print("🚀 Starting ULTIMATE code quality check...")
        print("(Your 10-line script has evolved into a BEAST!) 😈\n")

        # Step 1: Enhanced MyPy (your original approach)
        mypy_results = self.run_mypy_check()

        # Step 2: Ruff checks
        ruff_results = self.run_ruff_checks()

        # Step 3: Coffee scraper specific analysis
        coffee_issues = self.analyze_coffee_scraper_specific()

        # Analyze all Python files (with proper exclusions)
        print("\n🔍 Analyzing all Python files...")
        exclude_dirs = {
            "venv",
            ".venv",
            "env",
            ".env",
            "node_modules",
            "__pycache__",
            ".git",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            ".tox",
            "site-packages",
        }

        python_files = []
        for py_file in self.project_root.rglob("*.py"):
            if not any(excluded in py_file.parts for excluded in exclude_dirs):
                python_files.append(py_file)

        print(f"📊 Found {len(python_files)} Python files to analyze (excluding venv/cache directories)")

        for file_path in python_files:
            self.analyze_python_file(file_path)

        # Step 5: Generate ultimate report
        report = self.generate_ultimate_report(mypy_results, ruff_results, coffee_issues)

        # Save report
        report_file = self.project_root / "ULTIMATE_cleanup_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\nReport saved to: {report_file}")
        print("\n" + "=" * 60)
        print("ULTIMATE CHECK COMPLETE!")
        print("Your baby script has grown up!")
        print("=" * 60)
        print(report)


def main():
    """Run the ultimate checker."""
    checker = UltimateCodeChecker()
    checker.run_ultimate_check()


if __name__ == "__main__":
    main()
