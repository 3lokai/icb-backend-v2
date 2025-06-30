#!/usr/bin/env python3
"""
Error Triage Script - Because 8000 lines of errors is too much for human sanity.
Let's break this down into bite-sized, fixable chunks!
"""

import re
from collections import defaultdict
from pathlib import Path


class ErrorTriageManager:
    """Sanity-saving error triage for overwhelming reports."""

    def __init__(self, report_file: str = "ULTIMATE_cleanup_report.md"):
        self.report_file = Path(report_file)
        self.errors_by_type = defaultdict(list)
        self.errors_by_file = defaultdict(list)
        self.fixable_count = 0
        self.critical_count = 0

    def parse_massive_report(self):
        """Parse the 8000-line monster and categorize errors."""
        if not self.report_file.exists():
            print(f"Report file {self.report_file} not found!")
            return

        print(f"📖 Parsing {self.report_file.stat().st_size // 1024}KB report...")

        with open(self.report_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract different error sections
        self.extract_mypy_errors(content)
        self.extract_ruff_errors(content)
        self.extract_critical_issues(content)

    def extract_mypy_errors(self, content: str):
        """Extract and categorize MyPy errors."""
        mypy_section = re.search(r"## MyPy Type Checking Results(.*?)(?=##|$)", content, re.DOTALL)
        if not mypy_section:
            return

        mypy_content = mypy_section.group(1)

        # Common MyPy error patterns
        error_patterns = {
            "missing_imports": r"Cannot find implementation or library stub for module",
            "undefined_vars": r"Name .* is not defined",
            "type_errors": r"Incompatible types in assignment",
            "attr_errors": r"has no attribute",
            "arg_errors": r"Too many arguments|Too few arguments",
            "return_errors": r"Incompatible return value type",
        }

        for error_type, pattern in error_patterns.items():
            matches = re.findall(pattern, mypy_content, re.IGNORECASE)
            self.errors_by_type[f"mypy_{error_type}"] = matches

    def extract_ruff_errors(self, content: str):
        """Extract and categorize Ruff errors."""
        ruff_section = re.search(r"## Ruff Linting Results(.*?)(?=##|$)", content, re.DOTALL)
        if not ruff_section:
            return

        ruff_content = ruff_section.group(1)

        # Common Ruff error codes
        ruff_patterns = {
            "unused_imports": r"F401.*imported but unused",
            "undefined_names": r"F821.*undefined name",
            "import_order": r"I001.*Import block is un-sorted",
            "line_length": r"E501.*line too long",
            "unused_vars": r"F841.*local variable.*is assigned to but never used",
            "bare_except": r"E722.*do not use bare.*except",
        }

        for error_type, pattern in ruff_patterns.items():
            matches = re.findall(pattern, ruff_content, re.IGNORECASE)
            self.errors_by_type[f"ruff_{error_type}"] = matches

    def extract_critical_issues(self, content: str):
        """Find the CRITICAL issues that need immediate attention."""
        critical_patterns = {
            "duplicate_files": r"CRITICAL.*Duplicate",
            "common_conflicts": r"COMMON FOLDER CONFLICT",
            "undefined_functions": r"undefined.*function",
            "circular_imports": r"circular.*import",
        }

        for issue_type, pattern in critical_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                self.critical_count += len(matches)
                self.errors_by_type[f"critical_{issue_type}"] = matches

    def count_auto_fixable(self):
        """Count how many errors can be auto-fixed."""
        auto_fixable = ["ruff_unused_imports", "ruff_import_order", "ruff_unused_vars"]

        self.fixable_count = sum(len(self.errors_by_type.get(error_type, [])) for error_type in auto_fixable)

    def generate_triage_report(self):
        """Generate a triage report summarizing all errors."""
        report = []

        # Count totals
        total_errors = sum(len(v) if isinstance(v, list) else int(v) for v in self.errors_by_type.values())
        report.append(f"**Total Issues Found**: {total_errors}")
        report.append(f"**Auto-Fixable**: {self.fixable_count}")
        report.append(f"**Critical Issues**: {self.critical_count}")
        report.append("")

        # Priority 1: CRITICAL (Fix First)
        report.append("## PRIORITY 1: CRITICAL ISSUES (Fix These First!)\n")
        critical_issues = {k: v for k, v in self.errors_by_type.items() if k.startswith("critical_")}

        if critical_issues:
            for issue, matches in critical_issues.items():
                issue_name = issue.replace("critical_", "").replace("_", " ").title()
                count = len(matches) if isinstance(matches, list) else matches
                report.append(f"- **{issue_name}**: {count} issues")
        else:
            report.append("✅ No critical structural issues found!")
        report.append("")

        # Priority 2: AUTO-FIXABLE (Easy Wins)
        report.append("## PRIORITY 2: AUTO-FIXABLE ISSUES (Easy Wins!)\n")
        report.append("These can be fixed automatically with ruff:")
        report.append("")

        auto_fixable_issues = {
            "ruff_unused_imports": "Unused Imports",
            "ruff_import_order": "Import Order",
            "ruff_unused_vars": "Unused Variables",
        }
        for error_type, description in auto_fixable_issues.items():
            value = self.errors_by_type.get(error_type, [])
            count = len(value) if isinstance(value, list) else value
            if count > 0:
                report.append(f"- **{description}**: {count} issues")

        report.append("\n**Auto-fix commands:**")
        report.append("```bash")
        report.append("# Fix imports and unused code")
        report.append("ruff check --select I,F401,F841 --fix .")
        report.append("")
        report.append("# Format everything")
        report.append("ruff format .")
        report.append("```")
        report.append("")

        # Priority 3: MyPy Issues
        report.append("## PRIORITY 3: MYPY TYPE ERRORS\n")
        mypy_issues = {k: v for k, v in self.errors_by_type.items() if k.startswith("mypy_")}
        for issue, matches in sorted(
            mypy_issues.items(), key=lambda x: len(x[1]) if isinstance(x[1], list) else x[1], reverse=True
        ):
            issue_name = issue.replace("mypy_", "").replace("_", " ").title()
            count = len(matches) if isinstance(matches, list) else matches
            report.append(f"- **{issue_name}**: {count} issues")
        report.append("")

        # Priority 4: OTHER RUFF ISSUES
        report.append("## PRIORITY 4: OTHER LINTING ISSUES\n")
        other_ruff = {
            k: v for k, v in self.errors_by_type.items() if k.startswith("ruff_") and k not in auto_fixable_issues
        }
        for issue, matches in sorted(
            other_ruff.items(), key=lambda x: len(x[1]) if isinstance(x[1], list) else x[1], reverse=True
        ):
            issue_name = issue.replace("ruff_", "").replace("_", " ").title()
            count = len(matches) if isinstance(matches, list) else matches
            report.append(f"- **{issue_name}**: {count} issues")
        report.append("")

        # Action Plan
        report.append("## SANITY-SAVING ACTION PLAN\n")
        report.append("**Don't try to fix everything at once!** Here's a sane approach:")
        report.append("")
        report.append("### Week 1: Critical Issues")
        report.append("1. Fix duplicate `run_product_scraper.py` files")
        report.append("2. Resolve common/ folder conflicts")
        report.append("3. Fix any circular imports")
        report.append("")
        report.append("### Week 2: Auto-fixes")
        report.append("1. Run `ruff check --fix .` to auto-fix imports/unused code")
        report.append("2. Run `ruff format .` to fix formatting")
        report.append("3. Re-run analysis to see progress")
        report.append("")
        report.append("### Week 3+: Gradual Cleanup")
        report.append("1. Pick one file at a time for MyPy issues")
        report.append("2. Focus on files you actively work on")
        report.append("3. Don't aim for perfection - aim for progress!")
        report.append("")

        report.append("**Remember**: A codebase with some linting issues that works is better than")
        report.append("a perfectly linted codebase that's broken from over-refactoring! 😄")

        return "\n".join(report)

    def run_triage(self):
        """Run the full triage process."""
        print("🚑 EMERGENCY TRIAGE MODE ACTIVATED!")
        print("8000 lines of errors detected - deploying sanity-saving measures...")
        print("")

        self.parse_massive_report()
        self.count_auto_fixable()

        triage_report = self.generate_triage_report()

        # Save triage report
        triage_file = Path("ERROR_TRIAGE_REPORT.md")
        with open(triage_file, "w", encoding="utf-8") as f:
            f.write(triage_report)

        print(f"📄 Sanity-saving triage report saved to: {triage_file}")
        print("\n" + "=" * 50)
        print("TRIAGE COMPLETE - YOU CAN BREATHE NOW!")
        print("=" * 50)
        print(triage_report)


def main():
    """Run error triage to make 8000 lines manageable."""
    triager = ErrorTriageManager()
    triager.run_triage()


if __name__ == "__main__":
    main()
