#!/usr/bin/env python3
"""
Real AST Code Analyzer - Actually analyze your code for function issues.
This will find the undefined functions and common/ conflicts you mentioned.
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict


class RealCodeAnalyzer:
    """Actually analyze the code structure and find real issues."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.function_definitions = defaultdict(list)  # func_name -> [(file, line, class_context)]
        self.function_calls = defaultdict(list)  # func_name -> [(file, line)]
        self.imports = defaultdict(list)  # module -> [(file, imported_items)]
        self.undefined_functions = []
        self.duplicate_functions = []
        self.common_conflicts = []
        self.all_files_analyzed = []

    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single Python file using AST."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                return {"skipped": "empty"}

            tree = ast.parse(content, filename=str(file_path))

            file_info = {"functions_defined": [], "functions_called": [], "imports": [], "classes": [], "issues": []}

            class DeepAnalyzer(ast.NodeVisitor):
                def __init__(self, outer_self):
                    self.outer_self = outer_self
                    self.current_class = None
                    self.current_function = None

                def visit_ClassDef(self, node):
                    old_class = self.current_class
                    self.current_class = node.name
                    file_info["classes"].append(node.name)
                    self.generic_visit(node)
                    self.current_class = old_class

                def visit_FunctionDef(self, node):
                    func_name = node.name
                    context = f"{self.current_class}.{func_name}" if self.current_class else func_name

                    file_info["functions_defined"].append(
                        {"name": func_name, "line": node.lineno, "context": context, "class": self.current_class}
                    )

                    # Track in global registry
                    self.outer_self.function_definitions[func_name].append(
                        {"file": str(file_path), "line": node.lineno, "context": context, "class": self.current_class}
                    )

                    old_function = self.current_function
                    self.current_function = func_name
                    self.generic_visit(node)
                    self.current_function = old_function

                def visit_Call(self, node):
                    func_name = None

                    # Handle different call types
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                        # Also track the full attribute call
                        if isinstance(node.func.value, ast.Name):
                            full_name = f"{node.func.value.id}.{node.func.attr}"
                            self.outer_self.function_calls[full_name].append(
                                {"file": str(file_path), "line": node.lineno, "context": self.current_function}
                            )

                    if func_name:
                        file_info["functions_called"].append(
                            {"name": func_name, "line": node.lineno, "context": self.current_function}
                        )

                        self.outer_self.function_calls[func_name].append(
                            {"file": str(file_path), "line": node.lineno, "context": self.current_function}
                        )

                    self.generic_visit(node)

                def visit_Import(self, node):
                    for alias in node.names:
                        file_info["imports"].append(
                            {"type": "import", "module": alias.name, "as": alias.asname, "line": node.lineno}
                        )
                        self.outer_self.imports[alias.name].append(
                            {"file": str(file_path), "as": alias.asname, "line": node.lineno}
                        )

                def visit_ImportFrom(self, node):
                    if node.module:
                        for alias in node.names:
                            file_info["imports"].append(
                                {
                                    "type": "from",
                                    "module": node.module,
                                    "name": alias.name,
                                    "as": alias.asname,
                                    "line": node.lineno,
                                }
                            )

                            import_key = f"{node.module}.{alias.name}"
                            self.outer_self.imports[import_key].append(
                                {"file": str(file_path), "as": alias.asname, "line": node.lineno}
                            )

            analyzer = DeepAnalyzer(self)
            analyzer.visit(tree)

            return file_info

        except SyntaxError as e:
            return {"error": f"Syntax error: {e}"}
        except Exception as e:
            return {"error": f"Analysis error: {e}"}

    def find_undefined_functions(self):
        """Find function calls with no definitions."""
        print("🔍 Finding undefined functions...")

        # Python builtins and common library functions to ignore
        builtins = {
            "print",
            "len",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "reversed",
            "open",
            "max",
            "min",
            "sum",
            "all",
            "any",
            "isinstance",
            "hasattr",
            "getattr",
            "setattr",
            "super",
            "type",
            "abs",
            "round",
            "bool",
            "append",
            "extend",
            "insert",
            "remove",
            "pop",
            "clear",
            "index",
            "count",
            "sort",
            "reverse",
            "copy",
            "get",
            "keys",
            "values",
            "items",
            "update",
            "split",
            "join",
            "strip",
            "replace",
            "format",
            "startswith",
            "endswith",
            "find",
            "lower",
            "upper",
            "title",
            "capitalize",
            "loads",
            "dumps",
            "load",
            "dump",
            "now",
            "sleep",
            "exists",
            "makedirs",
            "run",
            "call",
            "check_output",
            "Popen",  # subprocess
            "get",
            "post",
            "put",
            "delete",  # requests
            "info",
            "debug",
            "warning",
            "error",
            "critical",  # logging
            # Add more as needed
        }

        defined_functions = set(self.function_definitions.keys())

        for func_name, calls in self.function_calls.items():
            if func_name not in defined_functions and func_name not in builtins:
                # Skip if it looks like an imported function
                is_likely_import = any(func_name in import_name for import_name in self.imports.keys())

                if not is_likely_import:
                    self.undefined_functions.append({"function": func_name, "calls": calls, "call_count": len(calls)})

    def find_duplicate_functions(self):
        """Find functions defined multiple times."""
        print("🔍 Finding duplicate functions...")

        for func_name, definitions in self.function_definitions.items():
            if len(definitions) > 1:
                # Check if any are in common/ folder
                common_defs = [d for d in definitions if "common/" in d["file"] or d["file"].endswith("common")]
                other_defs = [d for d in definitions if d not in common_defs]

                self.duplicate_functions.append(
                    {
                        "function": func_name,
                        "definitions": definitions,
                        "count": len(definitions),
                        "has_common_conflict": bool(common_defs and other_defs),
                        "common_defs": common_defs,
                        "other_defs": other_defs,
                    }
                )

    def find_common_conflicts(self):
        """Find functions in common/ that are redefined elsewhere."""
        print("🔍 Finding common/ folder conflicts...")

        common_functions = {}

        # First, collect all functions defined in common/
        for func_name, definitions in self.function_definitions.items():
            for defn in definitions:
                if "common/" in defn["file"] or defn["file"].endswith("common"):
                    if func_name not in common_functions:
                        common_functions[func_name] = []
                    common_functions[func_name].append(defn)

        # Now check if these are redefined elsewhere
        for func_name, common_defs in common_functions.items():
            other_defs = [d for d in self.function_definitions[func_name] if d not in common_defs]

            if other_defs:
                self.common_conflicts.append(
                    {
                        "function": func_name,
                        "common_definitions": common_defs,
                        "other_definitions": other_defs,
                        "conflict_count": len(other_defs),
                    }
                )

    def analyze_project(self):
        """Analyze the entire project."""
        print(f"🚀 Starting deep AST analysis of {self.project_root}")

        # Find all Python files (excluding venv, cache, etc.)
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

        print(f"📊 Found {len(python_files)} Python files to analyze")

        # Analyze each file
        for i, file_path in enumerate(python_files):
            if i % 10 == 0:
                print(f"📄 Analyzing file {i + 1}/{len(python_files)}: {file_path.name}")

            result = self.analyze_file(file_path)
            self.all_files_analyzed.append({"file": str(file_path.relative_to(self.project_root)), "result": result})

        # Find issues
        self.find_undefined_functions()
        self.find_duplicate_functions()
        self.find_common_conflicts()

    def generate_report(self) -> str:
        """Generate detailed analysis report."""
        report = []
        report.append("# 🔍 REAL Code Analysis Report")
        report.append("*Actually analyzing your AST for function issues*\n")

        # Summary
        report.append("## 📊 Summary")
        report.append(f"- **Files analyzed**: {len(self.all_files_analyzed)}")
        report.append(f"- **Functions defined**: {len(self.function_definitions)}")
        report.append(f"- **Undefined function calls**: {len(self.undefined_functions)}")
        report.append(f"- **Duplicate functions**: {len(self.duplicate_functions)}")
        report.append(f"- **Common/ conflicts**: {len(self.common_conflicts)}")
        report.append("")

        # Undefined functions (CRITICAL)
        if self.undefined_functions:
            report.append("## 🚨 CRITICAL: Undefined Functions")
            report.append("*These function calls have no definitions anywhere in your codebase*\n")

            for issue in sorted(self.undefined_functions, key=lambda x: x["call_count"], reverse=True):
                report.append(f"### ❌ `{issue['function']}()` ({issue['call_count']} calls)")
                for call in issue["calls"]:
                    rel_path = Path(call["file"]).relative_to(self.project_root)
                    context = f" (in {call['context']})" if call["context"] else ""
                    report.append(f"- Called in `{rel_path}:{call['line']}`{context}")
                report.append("")

        # Common folder conflicts (HIGH PRIORITY)
        if self.common_conflicts:
            report.append("## 🎯 HIGH PRIORITY: Common/ Folder Conflicts")
            report.append("*Functions defined in common/ that are redefined elsewhere*\n")

            for conflict in self.common_conflicts:
                report.append(f"### ⚠️ `{conflict['function']}()`")

                report.append("**Common/ definitions:**")
                for defn in conflict["common_definitions"]:
                    rel_path = Path(defn["file"]).relative_to(self.project_root)
                    report.append(f"- `{rel_path}:{defn['line']}`")

                report.append("**Other definitions:**")
                for defn in conflict["other_definitions"]:
                    rel_path = Path(defn["file"]).relative_to(self.project_root)
                    report.append(f"- `{rel_path}:{defn['line']}`")
                report.append("")

        # Duplicate functions
        if self.duplicate_functions:
            report.append("## 🔄 Duplicate Function Definitions")

            for dup in sorted(self.duplicate_functions, key=lambda x: x["count"], reverse=True):
                emoji = "🔥" if dup["has_common_conflict"] else "⚠️"
                report.append(f"### {emoji} `{dup['function']}()` ({dup['count']} definitions)")

                for defn in dup["definitions"]:
                    rel_path = Path(defn["file"]).relative_to(self.project_root)
                    context = f" [{defn['context']}]" if defn["context"] != defn["file"] else ""
                    report.append(f"- `{rel_path}:{defn['line']}`{context}")
                report.append("")

        # Quick fixes
        report.append("## 🛠️ Quick Fix Recommendations")

        if self.undefined_functions:
            report.append("### Undefined Functions:")
            report.append("1. Check if these are supposed to be imported from other modules")
            report.append("2. Look for typos in function names")
            report.append("3. Add missing function definitions")
            report.append("")

        if self.common_conflicts:
            report.append("### Common/ Conflicts:")
            report.append("1. Remove duplicate definitions outside common/")
            report.append("2. Import from common/ instead of redefining")
            report.append("3. Rename functions if they serve different purposes")
            report.append("")

        return "\n".join(report)

    def save_report(self, filename: str = "REAL_CODE_ANALYSIS.md"):
        """Save the analysis report."""
        report = self.generate_report()

        report_path = self.project_root / filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 Real analysis report saved to: {report_path}")
        return report_path


def main():
    """Run the real code analyzer."""
    analyzer = RealCodeAnalyzer()
    analyzer.analyze_project()

    report_path = analyzer.save_report()

    # Print summary to console
    print("\n" + "=" * 60)
    print("🎯 REAL CODE ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"📊 Files analyzed: {len(analyzer.all_files_analyzed)}")
    print(f"❌ Undefined functions: {len(analyzer.undefined_functions)}")
    print(f"🎯 Common/ conflicts: {len(analyzer.common_conflicts)}")
    print(f"🔄 Duplicate functions: {len(analyzer.duplicate_functions)}")
    print(f"\n📄 Full report: {report_path}")

    if analyzer.undefined_functions:
        print(f"\n🚨 CRITICAL: {len(analyzer.undefined_functions)} undefined functions found!")
        for func in analyzer.undefined_functions[:3]:  # Show top 3
            print(f"   - {func['function']}() ({func['call_count']} calls)")
        if len(analyzer.undefined_functions) > 3:
            print(f"   - ... and {len(analyzer.undefined_functions) - 3} more")


if __name__ == "__main__":
    main()
