#!/usr/bin/env python3
"""
Run payslip validation tests and automatically update expected values in test files
based on actual computed values from test failures.
"""

import argparse
import re
import subprocess
from pathlib import Path

# ANSI colors
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
DIM    = "\033[2m"

ODOO_BIN = "/Users/romc/Desktop/odoo-src/odoo/odoo-bin"
ADDONS_PATH = "/Users/romc/Desktop/odoo-src/odoo/addons/,/Users/romc/Desktop/odoo-src/enterprise/"
DB_NAME = "odoo"
TEST_TAGS = "/test_l10n_be_hr_payroll_account"


def run_tests(tags):
    print(f"\n{CYAN}🔄 Running tests:{RESET} {DIM}{tags}{RESET}", flush=True)
    result = subprocess.run(
        [
            ODOO_BIN,
            f"--addons-path={ADDONS_PATH}",
            "-d", DB_NAME,
            "--test-tags", tags,
            "--stop-after-init",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


def get_results_var_name(file_lines, line_no):
    """
    Given the 1-indexed line number of a self._validate_payslip(...) call,
    return the name of the dict variable passed as the second argument.
    """
    line = file_lines[line_no - 1]
    m = re.search(r'self\._validate_payslip\(\s*\w+\s*,\s*(\w+)', line)
    return m.group(1) if m else "payslip_results"


def parse_failures(output):
    """
    Parse failures from test output.
    Returns list of (file_path, validate_line_no, var_name, actual_values_str, class_name, method_name) tuples.
    """
    failures = []

    # Match traceback lines pointing to _validate_payslip calls in any test file
    traceback_pattern = re.compile(
        r'File "(.*?test_l10n_be_hr_payroll_account/tests/[^"]+\.py)", line (\d+), in (\w+)\s*\n\s*self\._validate_payslip\('
    )

    # Match "Payslip Actual Values:" blocks (Odoo always uses "payslip_results" here)
    actual_values_pattern = re.compile(
        r'Payslip Actual Values:\s*\n(\s*payslip_results\s*=\s*\{[^\n]+\})'
    )

    traceback_matches = list(traceback_pattern.finditer(output))
    actual_matches = list(actual_values_pattern.finditer(output))

    print(f"{YELLOW}⚠️  Found {len(traceback_matches)} failing _validate_payslip call(s){RESET}")
    print(f"{DIM}   ({len(actual_matches)} 'Payslip Actual Values' block(s) in output){RESET}")

    # Extract class names per test method from ERROR lines: "ERROR test.module.ClassName.method_name"
    error_pattern = re.compile(r'ERROR [\w.]+\.(\w+)\.(\w+)')
    method_to_class = {m.group(2): m.group(1) for m in error_pattern.finditer(output)}

    used_actual = set()
    for tb_match in traceback_matches:
        file_path = Path(tb_match.group(1))
        line_no = int(tb_match.group(2))
        method_name = tb_match.group(3)
        class_name = method_to_class.get(method_name, "TestPayslipValidation")
        file_lines = file_path.read_text().splitlines() if file_path.exists() else []
        var_name = get_results_var_name(file_lines, line_no)
        for i, av_match in enumerate(actual_matches):
            if i in used_actual:
                continue
            if av_match.start() > tb_match.start():
                used_actual.add(i)
                actual_values_str = av_match.group(1).strip()
                failures.append((file_path, line_no, var_name, actual_values_str, class_name, method_name))
                break
        else:
            print(f"{RED}⚠️  WARNING:{RESET} could not find actual values for {file_path.name}:{line_no}")

    return failures


def find_assignment_line(file_lines, before_line_no, var_name, search_range=50):
    """
    Search backwards from before_line_no (1-indexed) to find
    the most recent '<var_name> = {' assignment.
    Returns 0-indexed line index or None.
    """
    start = min(before_line_no - 1, len(file_lines) - 1)
    for i in range(start, max(-1, start - search_range), -1):
        stripped = file_lines[i].strip()
        if re.match(rf'{re.escape(var_name)}\s*=\s*\{{', stripped):
            return i
    return None


def apply_fixes(failures):
    # Group by file
    by_file = {}
    for file_path, line_no, var_name, actual_values_str, *_ in failures:
        by_file.setdefault(file_path, []).append((line_no, var_name, actual_values_str))

    total_changes = 0
    for file_path, file_failures in by_file.items():
        if not file_path.exists():
            print(f"{RED}⚠️  WARNING:{RESET} file not found: {file_path}")
            continue

        lines = file_path.read_text().splitlines(keepends=True)
        file_changes = []

        for validate_line_no, var_name, actual_values_str in file_failures:
            idx = find_assignment_line(lines, validate_line_no, var_name)
            if idx is None:
                print(f"{RED}⚠️  WARNING:{RESET} could not find '{var_name}' assignment before {file_path.name}:{validate_line_no}")
                continue

            old_line = lines[idx]
            indent = len(old_line) - len(old_line.lstrip())
            # Odoo always prints "payslip_results = {...}" — rename to the actual variable
            normalized = re.sub(r'^\w+\s*=\s*', f'{var_name} = ', actual_values_str)
            new_line = " " * indent + normalized + "\n"

            if old_line == new_line:
                continue

            file_changes.append((idx, old_line.rstrip(), new_line.rstrip()))
            lines[idx] = new_line

        if file_changes:
            print(f"\n{BOLD}{file_path.name}{RESET}: {GREEN}✏️  {len(file_changes)} fix(es){RESET}")
            for idx, old, new in file_changes:
                print(f"  {DIM}Line {idx+1}:{RESET}")
                old_dict = re.search(r'\{.*\}', old)
                new_dict = re.search(r'\{.*\}', new)
                if old_dict and new_dict:
                    old_d = dict(re.findall(r"'(\w+(?:\.\w+)*)'\s*:\s*(-?[\d.]+)", old_dict.group()))
                    new_d = dict(re.findall(r"'(\w+(?:\.\w+)*)'\s*:\s*(-?[\d.]+)", new_dict.group()))
                    diffs = {k: (old_d.get(k), new_d[k]) for k in new_d if old_d.get(k) != new_d[k]}
                    for key, (old_val, new_val) in diffs.items():
                        print(f"    {DIM}{key}:{RESET} {RED}{old_val}{RESET} → {GREEN}{new_val}{RESET}")
            file_path.write_text("".join(lines))
            total_changes += len(file_changes)

    return total_changes



def build_tags(failures):
    """Build a test-tags string targeting only the methods that failed."""
    return ",".join(
        sorted({f".{method}" for *_, method in failures})
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run payslip validation tests and automatically update expected values based on actual computed values from test failures."
    )
    parser.add_argument(
        "--test-tags",
        default=TEST_TAGS,
        dest="test_tags",
        help=f"Test tags to pass to --test-tags (default: {TEST_TAGS})",
    )
    args = parser.parse_args()

    tags = args.test_tags
    iteration = 0
    while True:
        iteration += 1
        print(f"\n{BOLD}{CYAN}{'─' * 40}{RESET}")
        print(f"{BOLD}{CYAN}  Iteration {iteration}{RESET}")
        print(f"{BOLD}{CYAN}{'─' * 40}{RESET}")
        output = run_tests(tags)

        failures = parse_failures(output)

        if not failures:
            print(f"\n{GREEN}✅ No payslip failures found — all tests pass (or no parseable failures).{RESET}\n")
            break

        total = apply_fixes(failures)

        if not total:
            print(f"\n{RED}❌ Failures found but no lines were updated — stopping to avoid infinite loop.{RESET}")
            print(f"{DIM}Still-failing tests:{RESET}\n  {build_tags(failures)}\n")
            break

        tags = build_tags(failures)
        failed_methods = {method for *_, method in failures}
        print(f"\n{GREEN}✅ Iteration {iteration} done:{RESET} {total} line(s) updated. Re-running {len(failed_methods)} failed test(s)...\n")


if __name__ == "__main__":
    main()
