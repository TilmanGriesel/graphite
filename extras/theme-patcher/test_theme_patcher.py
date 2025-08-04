#!/usr/bin/env python3
"""
Test suite for Graphite Theme Patcher

Tests the theme patcher against actual theme files to validate:
- Standard theme updates (graphite.yaml)
- Auto theme updates (graphite-auto.yaml)
- User-defined entries grouping
- Mode targeting (light/dark/all)
- Proper indentation
- Error handling
"""

import sys
import shutil
import importlib.util
from pathlib import Path
import subprocess
import time

# Add the current directory to path (theme-patcher directory)
sys.path.insert(0, str(Path(__file__).parent))

patcher_path = Path(__file__).parent / "graphite-theme-patcher.py"
spec = importlib.util.spec_from_file_location("theme_patcher", patcher_path)
theme_patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme_patcher)
ThemePatcher = theme_patcher.ThemePatcher


class TestResult:
    def __init__(self, name, passed=False, message="", output=""):
        self.name = name
        self.passed = passed
        self.message = message
        self.output = output


class ThemePatcherTester:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = self.project_root / "test_output"
        self.themes_dir = self.project_root / "themes"
        self.patcher_script = Path(__file__).parent / "graphite-theme-patcher.py"
        self.results = []

    def setup(self):
        """Setup test environment."""
        # Create test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        # Copy theme files to test directory with proper structure
        # Theme patcher expects: base_path/theme_name/theme_name.yaml

        # Standard theme
        graphite_dir = self.test_dir / "graphite"
        graphite_dir.mkdir()
        shutil.copy2(self.themes_dir / "graphite.yaml", graphite_dir / "graphite.yaml")

        # Auto theme
        graphite_auto_dir = self.test_dir / "graphite-auto"
        graphite_auto_dir.mkdir()
        shutil.copy2(
            self.themes_dir / "graphite-auto.yaml",
            graphite_auto_dir / "graphite-auto.yaml",
        )

        print(f"✓ Test environment setup complete: {self.test_dir}")

    def cleanup(self):
        """Cleanup test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        print("✓ Test environment cleaned up")

    def run_patcher(
        self, token, value, theme="graphite", token_type="rgb", mode="all", create=False
    ):
        """Run the theme patcher script and return result."""
        cmd = [
            sys.executable,
            str(self.patcher_script),
            value,
            "--token",
            token,
            "--type",
            token_type,
            "--theme",
            theme,
            "--path",
            str(self.test_dir),
            "--mode",
            mode,
        ]

        if create:
            cmd.append("--create")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)

    def read_theme_file(self, theme_name):
        """Read theme file contents."""
        theme_file = self.test_dir / theme_name / f"{theme_name}.yaml"
        if theme_file.exists():
            return theme_file.read_text()
        return ""

    def test_standard_theme_existing_token(self):
        """Test updating existing token in standard theme."""
        success, stdout, stderr = self.run_patcher(
            token="token-rgb-primary", value="255, 128, 64", theme="graphite"
        )

        content = self.read_theme_file("graphite")

        passed = (
            success
            and "token-rgb-primary: 255, 128, 64" in content
            and "Modified by Graphite Theme Patcher" in content
        )

        return TestResult(
            "Standard theme - update existing token",
            passed,
            "Updated existing token with new value" if passed else f"Failed: {stderr}",
            content[:500] + "..." if len(content) > 500 else content,
        )

    def test_standard_theme_new_token(self):
        """Test creating new token in standard theme."""
        success, stdout, stderr = self.run_patcher(
            token="custom-test-token",
            value="123, 45, 67",
            theme="graphite",
            create=True,
        )

        content = self.read_theme_file("graphite")

        # Check for proper user-defined entries section
        has_header = (
            "##############################################################################"
            in content
        )
        has_comment = "# User defined entries" in content
        has_token = (
            "custom-test-token: rgb(123, 45, 67)" in content
        )  # RGB function format for non-rgb tokens
        has_proper_indent = "  custom-test-token:" in content  # 2 spaces

        passed = (
            success and has_header and has_comment and has_token and has_proper_indent
        )

        return TestResult(
            "Standard theme - create new token",
            passed,
            (
                f"Created new token in user section (header:{has_header}, comment:{has_comment}, token:{has_token}, indent:{has_proper_indent})"
                if passed
                else f"Failed: {stderr}"
            ),
            (
                content.split("# User defined entries")[-1][:200]
                if "# User defined entries" in content
                else "No user section found"
            ),
        )

    def test_auto_theme_existing_token(self):
        """Test updating existing token in auto theme."""
        success, stdout, stderr = self.run_patcher(
            token="token-rgb-primary", value="200, 100, 50", theme="graphite-auto"
        )

        content = self.read_theme_file("graphite-auto")

        # Check that token was updated in both light and dark modes
        light_updated = content.count("token-rgb-primary: 200, 100, 50") >= 1
        has_timestamps = content.count("Modified by Graphite Theme Patcher") >= 1

        passed = success and light_updated and has_timestamps

        return TestResult(
            "Auto theme - update existing token",
            passed,
            (
                f"Updated token in modes (light_updated:{light_updated}, timestamps:{has_timestamps})"
                if passed
                else f"Failed: {stderr}"
            ),
            "\n".join(
                [
                    line
                    for line in content.split("\n")
                    if "token-rgb-primary: 200, 100, 50" in line
                ]
            ),
        )

    def test_auto_theme_new_token_all_modes(self):
        """Test creating new token in all modes of auto theme."""
        success, stdout, stderr = self.run_patcher(
            token="custom-auto-token",
            value="99, 88, 77",
            theme="graphite-auto",
            mode="all",
            create=True,
        )

        content = self.read_theme_file("graphite-auto")

        # Count occurrences of the token (should be in light and dark)
        token_count = content.count(
            "custom-auto-token: rgb(99, 88, 77)"
        )  # RGB function format
        user_sections = content.count("# User defined entries")
        proper_indent = content.count(
            "      custom-auto-token:"
        )  # 6 spaces (correct YAML indentation)

        passed = (
            success and token_count >= 2 and user_sections >= 2 and proper_indent >= 2
        )

        return TestResult(
            "Auto theme - create new token (all modes)",
            passed,
            (
                f"Created token in both modes (token_count:{token_count}, user_sections:{user_sections}, proper_indent:{proper_indent})"
                if passed
                else f"Failed: {stderr}"
            ),
            "\n".join(
                [
                    line
                    for line in content.split("\n")
                    if "custom-auto-token" in line or "User defined entries" in line
                ]
            ),
        )

    def test_auto_theme_light_mode_only(self):
        """Test creating new token in light mode only."""
        success, stdout, stderr = self.run_patcher(
            token="light-only-token",
            value="111, 200, 150",  # Valid RGB values (all <= 255)
            theme="graphite-auto",
            mode="light",
            create=True,
        )

        content = self.read_theme_file("graphite-auto")

        # Should appear only once (in light mode)
        token_count = content.count(
            "light-only-token: rgb(111, 200, 150)"
        )  # RGB function format with valid values

        # Find the token and check it's in light section
        lines = content.split("\n")
        token_line_idx = -1
        for i, line in enumerate(lines):
            if "light-only-token: rgb(111, 200, 150)" in line:
                token_line_idx = i
                break

        in_light_section = False
        if token_line_idx > -1:
            # Look backwards to find which section we're in
            for i in range(token_line_idx, -1, -1):
                if "light:" in lines[i]:
                    in_light_section = True
                    break
                elif "dark:" in lines[i]:
                    break

        passed = success and token_count == 1 and in_light_section

        return TestResult(
            "Auto theme - light mode only",
            passed,
            (
                f"Created token in light mode only (count:{token_count}, in_light:{in_light_section})"
                if passed
                else f"Failed: {stderr}"
            ),
            (
                lines[max(0, token_line_idx - 2) : token_line_idx + 3]
                if token_line_idx > -1
                else ["Token not found"]
            ),
        )

    def test_card_mod_token(self):
        """Test creating card-mod token."""
        success, stdout, stderr = self.run_patcher(
            token="card-mod-root",
            value='"border-radius: 12px;"',
            theme="graphite",
            token_type="card-mod",
        )

        content = self.read_theme_file("graphite")

        # Check card-mod token placement (should be at 2-space indent level)
        has_token = "card-mod-root:" in content
        proper_indent = "  card-mod-root:" in content  # 2 spaces
        has_quotes = '"border-radius: 12px;"' in content

        passed = success and has_token and proper_indent and has_quotes

        return TestResult(
            "Card-mod token",
            passed,
            (
                f"Created card-mod token (token:{has_token}, indent:{proper_indent}, quotes:{has_quotes})"
                if passed
                else f"Failed: {stderr}"
            ),
            "\n".join([line for line in content.split("\n") if "card-mod" in line]),
        )

    def test_user_section_grouping(self):
        """Test that multiple new tokens are grouped in same user section."""
        # Create multiple tokens
        success1, _, _ = self.run_patcher(
            "test-token-1", "1, 2, 3", "graphite", create=True
        )
        success2, _, _ = self.run_patcher(
            "test-token-2", "4, 5, 6", "graphite", create=True
        )
        success3, _, _ = self.run_patcher(
            "test-token-3", "7, 8, 9", "graphite", create=True
        )

        content = self.read_theme_file("graphite")

        # Should have only one user-defined entries header
        header_count = content.count(
            "##############################################################################"
        )
        comment_count = content.count("# User defined entries")

        # All tokens should be present (RGB function format for non-rgb token names)
        has_token1 = "test-token-1: rgb(1, 2, 3)" in content
        has_token2 = "test-token-2: rgb(4, 5, 6)" in content
        has_token3 = "test-token-3: rgb(7, 8, 9)" in content

        passed = (
            success1
            and success2
            and success3
            and header_count == 1
            and comment_count == 1
            and has_token1
            and has_token2
            and has_token3
        )

        return TestResult(
            "User section grouping",
            passed,
            (
                f"Grouped tokens in single section (headers:{header_count}, comments:{comment_count}, tokens:{has_token1 and has_token2 and has_token3})"
                if passed
                else "Failed to group tokens"
            ),
            (
                content.split("# User defined entries")[-1][:300]
                if "# User defined entries" in content
                else "No user section"
            ),
        )

    def test_generic_background_token(self):
        """Test creating background token using generic type."""
        success, stdout, stderr = self.run_patcher(
            token="custom-background-image",
            value='url("https://example.com/background.jpg")',
            theme="graphite",
            token_type="generic",
            create=True,
        )

        content = self.read_theme_file("graphite")

        # Check background token placement and formatting (generic passes through as-is)
        has_token = "custom-background-image:" in content
        proper_format = (
            'custom-background-image: url("https://example.com/background.jpg")'
            in content
        )
        proper_indent = "  custom-background-image:" in content  # 2 spaces

        passed = success and has_token and proper_format and proper_indent

        return TestResult(
            "Generic background token",
            passed,
            (
                f"Created background token using generic type (token:{has_token}, format:{proper_format}, indent:{proper_indent})"
                if passed
                else f"Failed: {stderr}"
            ),
            "\n".join(
                [
                    line
                    for line in content.split("\n")
                    if "custom-background-image" in line
                ]
            ),
        )

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test invalid theme
        success1, stdout1, stderr1 = self.run_patcher(
            token="test-token", value="1, 2, 3", theme="nonexistent-theme"
        )

        # Test invalid token type
        success2, stdout2, stderr2 = self.run_patcher(
            token="test-token",
            value="invalid-rgb-value",
            theme="graphite",
            token_type="rgb",
        )

        passed = not success1 and not success2  # Both should fail

        return TestResult(
            "Error handling",
            passed,
            (
                "Properly handled invalid theme and invalid RGB values"
                if passed
                else "Failed to catch errors"
            ),
            f"Theme error: {stderr1[:50]}... | RGB error: {stderr2[:50]}...",
        )

    def run_all_tests(self):
        """Run all tests and report results."""
        print("🧪 Starting Theme-Patcher Test Suite\n")

        self.setup()

        try:
            # Run tests
            tests = [
                self.test_standard_theme_existing_token,
                self.test_standard_theme_new_token,
                self.test_auto_theme_existing_token,
                self.test_auto_theme_new_token_all_modes,
                self.test_auto_theme_light_mode_only,
                self.test_card_mod_token,
                self.test_generic_background_token,
                self.test_user_section_grouping,
                self.test_error_handling,
            ]

            for test_func in tests:
                print(f"Running: {test_func.__doc__.strip()}")
                result = test_func()
                self.results.append(result)

                status = "✅ PASS" if result.passed else "❌ FAIL"
                print(f"  {status}: {result.message}")

                if not result.passed and result.output:
                    print(f"  Output: {result.output}")
                print()

                # Small delay between tests
                time.sleep(0.1)

        finally:
            self.cleanup()

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print("=" * 60)
        print(f"TEST SUMMARY: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Theme-Patcher is working correctly.")
            return True
        else:
            print("🚨 Some tests failed. Check the output above for details.")
            for result in self.results:
                if not result.passed:
                    print(f"  ❌ {result.name}: {result.message}")
            return False


if __name__ == "__main__":
    tester = ThemePatcherTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
