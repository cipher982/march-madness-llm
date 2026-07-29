import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(0o755)


def test_entrypoint_retries_infisical_without_leaking_response(tmp_path: Path) -> None:
    attempts = tmp_path / "attempts"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    _write_executable(
        bin_dir / "curl",
        f"""#!/bin/sh
count=$(cat {attempts} 2>/dev/null || echo 0)
count=$((count + 1))
printf '%s' "$count" > {attempts}
if [ "$count" -lt 3 ]; then
  exit 22
fi
printf '%s' '{{"accessToken":"test-token"}}'
""",
    )
    _write_executable(bin_dir / "sleep", "#!/bin/sh\nexit 0\n")
    _write_executable(
        bin_dir / "infisical",
        '#!/bin/sh\nprintf \'token=%s args=%s\\n\' "$INFISICAL_TOKEN" "$*"\n',
    )

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "INFISICAL_CLIENT_ID": "client-id",
            "INFISICAL_CLIENT_SECRET": "client-secret",
            "INFISICAL_AUTH_MAX_ATTEMPTS": "3",
            "INFISICAL_AUTH_RETRY_SECONDS": "0",
        }
    )

    result = subprocess.run(
        ["sh", str(Path(__file__).parents[1] / "entrypoint.sh"), "test-command"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert attempts.read_text() == "3"
    assert "token=test-token" in result.stdout
    assert "test-command" in result.stdout
    assert "client-secret" not in result.stdout
    assert "client-secret" not in result.stderr
    assert result.stderr.count("retrying") == 2
