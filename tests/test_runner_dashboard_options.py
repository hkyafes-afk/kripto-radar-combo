"""CLI contract tests for continuous PAPER dashboard publishing."""
import subprocess
import sys


def test_runner_help_exposes_periodic_dashboard_options():
    result = subprocess.run(
        [sys.executable, "-m", "runner.main", "--help"],
        check=True, capture_output=True, text=True,
    )
    assert "--dashboard-interval" in result.stdout
    assert "--checkpoint-interval" in result.stdout


def test_runner_rejects_dashboard_interval_below_safe_minimum():
    result = subprocess.run(
        [sys.executable, "-m", "runner.main", "--dashboard-interval", "0.5"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "--dashboard-interval must be between 1 and 300 seconds" in result.stderr

def test_ops_shell_scripts_parse():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for script in (
        "ops/publish-dashboard-state.sh",
        "ops/install-user-services.sh",
        "ops/setup-deploy-key.sh",
    ):
        subprocess.run(["bash", "-n", str(root / script)], check=True)
