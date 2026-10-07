# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest>=8.0",
#     "httpx>=0.27",
#     "respx>=0.22",
# ]
# ///
"""
Red-Green TDD test suite for grokipedia.py.

Run:
    uvx --with-requirements tests/test_grokipedia.py pytest tests/test_grokipedia.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx

# ---------------------------------------------------------------------------
# Resolve script path so tests work regardless of cwd
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SCRIPT_DIR / "grokipedia.py"

# Add parent so we can `import grokipedia`
sys.path.insert(0, str(SCRIPT_DIR))
import grokipedia  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_script(*args: str, env: dict[str, str] | None = None) -> tuple[str, str, int]:
    """Execute grokipedia.py via subprocess and return (stdout, stderr, exit_code)."""
    cmd = ["uv", "run", str(SCRIPT_PATH), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=env,
        timeout=60,
    )
    return result.stdout, result.stderr, result.returncode


@pytest.fixture(autouse=True)
def temp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Send the default results file to a per-test folder, never the real temp dir."""
    monkeypatch.setattr(grokipedia.tempfile, "tempdir", str(tmp_path))
    return tmp_path


def succeeded(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    """The one-line answer a successful run printed, with an empty stderr."""
    out, err = capsys.readouterr()
    assert err == ""
    assert out.endswith("\n") and out.count("\n") == 1
    found = json.loads(out)
    assert found["ok"] is True
    return found


def failed(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    """The answer a failed run left as the last stderr line, with an empty stdout."""
    out, err = capsys.readouterr()
    assert out == ""
    found = json.loads(err.splitlines()[-1])
    assert found["ok"] is False
    return found


def results_text(capsys: pytest.CaptureFixture[str]) -> str:
    """The Markdown file a successful run answered with."""
    file = Path(succeeded(capsys)["file"])
    assert file.is_absolute()
    return file.read_text(encoding="utf-8")


def urls_in(markdown: str) -> list[str]:
    """The result URLs in a results file, in order."""
    return [
        line.removeprefix("- URL: ")
        for line in markdown.splitlines()
        if line.startswith("- URL: ")
    ]


def _capture_payload(
    url: str,
) -> tuple[dict[str, Any], Any]:
    """Set up a respx mock that captures the JSON payload sent to *url*.

    Returns (captured_dict, respx_route) so callers can inspect the payload
    after making the request.
    """
    captured: dict[str, Any] = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json=FAKE_RESPONSE)

    route = respx.post(url).mock(side_effect=_handler)
    return captured, route


# Reusable Tavily API response fixture
FAKE_RESPONSE: dict[str, Any] = {
    "query": "test query",
    "answer": "A test answer from Tavily.",
    "response_time": 1.23,
    "results": [
        {
            "title": "Test Article",
            "url": "https://grokipedia.com/page/Test",
            "content": "This is test content from Grokipedia.",
            "score": 0.95,
            "raw_content": "Full raw content of the test article.",
        },
    ],
}

EMPTY_RESPONSE: dict[str, Any] = {
    "query": "nothing",
    "answer": None,
    "response_time": 0.5,
    "results": [],
}

# Response with None values in result fields -- mirrors real API returning null
NULL_FIELDS_RESPONSE: dict[str, Any] = {
    "query": "nulls",
    "answer": None,
    "response_time": None,
    "results": [
        {
            "title": None,
            "url": None,
            "content": None,
            "score": None,
            "raw_content": None,
        },
    ],
}


# ===================================================================
# CLI Integration Tests (subprocess)
# ===================================================================


class TestCLIHelp:
    """--help must exit 0 and show examples."""

    def test_help_exits_0(self) -> None:
        stdout, _, code = run_script("--help")
        assert code == 0

    def test_help_shows_examples(self) -> None:
        stdout, _, _ = run_script("--help")
        assert "examples:" in stdout

    def test_help_shows_all_flags(self) -> None:
        stdout, _, _ = run_script("--help")
        assert "--max-results" in stdout
        assert "--raw" in stdout
        assert "--output" in stdout
        assert "--verbose" in stdout
        assert "--version" in stdout
        assert "--json" not in stdout

    def test_help_wins_over_a_bad_argument(self) -> None:
        stdout, _, code = run_script("--typo", "--help")
        assert code == 0
        assert stdout.startswith("usage: grokipedia.py")


class TestCLIVersion:
    """--version must exit 0 and print semver."""

    def test_version_exits_0(self) -> None:
        _, _, code = run_script("--version")
        assert code == 0

    def test_version_shows_semver(self) -> None:
        stdout, _, _ = run_script("--version")
        assert stdout == "grokipedia.py 0.2.0\n"


class TestCLIValidation:
    """Bad input must fail fast with exit code 2."""

    def test_no_args_exits_2(self) -> None:
        """Missing query should exit 2 (argparse default)."""
        _, _, code = run_script()
        assert code == 2

    def test_empty_query_exits_2(self) -> None:
        """Empty string query is useless -- should be rejected."""
        _, stderr, code = run_script("")
        assert code == 2
        assert "empty" in stderr.lower() or "query" in stderr.lower()

    def test_whitespace_query_exits_2(self) -> None:
        """Whitespace-only query should be rejected."""
        _, stderr, code = run_script("   ")
        assert code == 2

    def test_max_results_zero_exits_2(self) -> None:
        _, _, code = run_script("test", "-n", "0")
        assert code == 2

    def test_max_results_21_exits_2(self) -> None:
        _, _, code = run_script("test", "-n", "21")
        assert code == 2

    def test_max_results_negative_exits_2(self) -> None:
        _, _, code = run_script("test", "-n", "-1")
        assert code == 2

    def test_max_results_non_integer_exits_2(self) -> None:
        """argparse should reject non-integer."""
        _, _, code = run_script("test", "-n", "abc")
        assert code == 2

    def test_json_flag_is_gone(self) -> None:
        """JSON is the default answer, so --json is an unknown flag."""
        _, _, code = run_script("test", "--json")
        assert code == 2

    def test_validation_errors_answer_on_stderr(self) -> None:
        """A usage error leaves stdout empty and ends stderr with its answer."""
        stdout, stderr, _ = run_script("test", "-n", "0")
        assert stdout == ""  # stdout must be clean
        assert json.loads(stderr.splitlines()[-1]) == {
            "ok": False,
            "errors": ["--max-results must be 1-20, got 0"],
            "help": "grokipedia.py --help",
        }


# ===================================================================
# Unit Tests -- get_api_key
# ===================================================================


class TestGetApiKey:
    """get_api_key must raise ApiKeyError, not sys.exit."""

    def test_missing_chezmoi_raises_api_key_error(self) -> None:
        """If chezmoi is not installed, should raise ApiKeyError."""
        with patch("grokipedia.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(grokipedia.ApiKeyError, match="chezmoi"):
                grokipedia.get_api_key()

    def test_keyring_failure_raises_api_key_error(self) -> None:
        """If keyring lookup fails, should raise ApiKeyError."""
        with patch(
            "grokipedia.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "chezmoi"),
        ):
            with pytest.raises(grokipedia.ApiKeyError, match="keyring"):
                grokipedia.get_api_key()

    def test_keyring_timeout_reports_actionable_error(self) -> None:
        with patch(
            "grokipedia.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="chezmoi", timeout=10),
        ):
            with pytest.raises(grokipedia.ApiKeyError, match="timed out"):
                grokipedia.get_api_key()

    def test_empty_key_raises_api_key_error(self) -> None:
        """Keyring returning empty/whitespace should be rejected."""
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="   \n", stderr=""
        )
        with patch("grokipedia.subprocess.run", return_value=mock_result):
            with pytest.raises(grokipedia.ApiKeyError, match="empty"):
                grokipedia.get_api_key()

    def test_valid_key_returned(self) -> None:
        """Valid key should be returned stripped."""
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="  tvly-abc123  \n", stderr=""
        )
        with patch("grokipedia.subprocess.run", return_value=mock_result):
            assert grokipedia.get_api_key() == "tvly-abc123"

    # --- Gap: error message actionability ---

    def test_unit_file_not_found_error_includes_install_url(self) -> None:
        """Error for missing chezmoi must include the install URL."""
        with patch("grokipedia.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(grokipedia.ApiKeyError, match="chezmoi.io/install"):
                grokipedia.get_api_key()

    def test_unit_subprocess_error_includes_set_command(self) -> None:
        """Error for keyring failure must include the set command."""
        with patch(
            "grokipedia.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "chezmoi"),
        ):
            with pytest.raises(
                grokipedia.ApiKeyError, match="chezmoi secret keyring set"
            ):
                grokipedia.get_api_key()

    def test_unit_empty_key_error_includes_set_command(self) -> None:
        """Error for empty key must include actionable set command."""
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="  \n", stderr=""
        )
        with patch("grokipedia.subprocess.run", return_value=mock_result):
            with pytest.raises(
                grokipedia.ApiKeyError, match="chezmoi secret keyring set"
            ):
                grokipedia.get_api_key()

    # --- Gap: exception chaining ---

    def test_unit_file_not_found_chains_original_exception(self) -> None:
        """ApiKeyError must chain the original FileNotFoundError via __cause__."""
        with patch("grokipedia.subprocess.run", side_effect=FileNotFoundError("nope")):
            with pytest.raises(grokipedia.ApiKeyError) as exc_info:
                grokipedia.get_api_key()
            assert isinstance(exc_info.value.__cause__, FileNotFoundError)

    def test_unit_subprocess_error_chains_original_exception(self) -> None:
        """ApiKeyError must chain the original CalledProcessError via __cause__."""
        with patch(
            "grokipedia.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "chezmoi"),
        ):
            with pytest.raises(grokipedia.ApiKeyError) as exc_info:
                grokipedia.get_api_key()
            assert isinstance(exc_info.value.__cause__, subprocess.CalledProcessError)


# ===================================================================
# Unit Tests -- search_grokipedia
# ===================================================================


class TestSearchGrokipedia:
    """search_grokipedia must build correct payloads and accept api_key."""

    @respx.mock
    def test_payload_includes_domains(self) -> None:
        """include_domains must contain both grokipedia domains."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", api_key="fake-key")
        assert captured["include_domains"] == [
            "grokipedia.com",
            "grokxpedia.us",
        ]

    @respx.mock
    def test_payload_respects_max_results(self) -> None:
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", max_results=10, api_key="fake-key")
        assert captured["max_results"] == 10

    @respx.mock
    def test_api_key_in_auth_header(self) -> None:
        """Bearer token must use the provided api_key."""
        captured_auth: str = ""

        def capture_request(request: httpx.Request) -> httpx.Response:
            nonlocal captured_auth
            captured_auth = request.headers.get("authorization", "")
            return httpx.Response(200, json=FAKE_RESPONSE)

        respx.post(grokipedia.TAVILY_API_URL).mock(side_effect=capture_request)

        grokipedia.search_grokipedia("test", api_key="tvly-secret")
        assert captured_auth == "Bearer tvly-secret"

    @respx.mock
    def test_http_error_propagates(self) -> None:
        """Non-2xx status should raise HTTPStatusError."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            grokipedia.search_grokipedia("test", api_key="bad-key")

    def test_missing_api_key_raises(self) -> None:
        """If api_key is None and get_api_key fails, should raise ApiKeyError."""
        with patch(
            "grokipedia.get_api_key",
            side_effect=grokipedia.ApiKeyError("no key"),
        ):
            with pytest.raises(grokipedia.ApiKeyError):
                grokipedia.search_grokipedia("test")

    # --- NEW: payload field coverage ---

    @respx.mock
    def test_unit_payload_query_field_matches_input(self) -> None:
        """Payload must include the query string passed by the caller."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("quantum computing", api_key="k")
        assert captured["query"] == "quantum computing"

    @respx.mock
    def test_unit_payload_search_depth_is_advanced(self) -> None:
        """search_depth must always be 'advanced'."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", api_key="k")
        assert captured["search_depth"] == "advanced"

    @respx.mock
    def test_unit_payload_include_raw_content_true(self) -> None:
        """include_raw_content must mirror the include_raw parameter."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", include_raw=True, api_key="k")
        assert captured["include_raw_content"] is True

    @respx.mock
    def test_unit_payload_include_raw_content_false(self) -> None:
        """include_raw_content defaults to False."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", api_key="k")
        assert captured["include_raw_content"] is False

    @respx.mock
    def test_unit_payload_include_answer_is_true(self) -> None:
        """include_answer must always be True."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", api_key="k")
        assert captured["include_answer"] is True

    @respx.mock
    def test_unit_payload_topic_is_general(self) -> None:
        """topic must always be 'general'."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", api_key="k")
        assert captured["topic"] == "general"

    @respx.mock
    def test_unit_request_error_propagates(self) -> None:
        """Connection/timeout errors must propagate as RequestError."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            side_effect=httpx.ConnectError("timeout")
        )
        with pytest.raises(httpx.RequestError):
            grokipedia.search_grokipedia("test", api_key="k")

    @respx.mock
    def test_unit_api_key_none_calls_get_api_key(self) -> None:
        """When api_key is None, get_api_key must be invoked."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="resolved-key") as mock_get:
            grokipedia.search_grokipedia("test", api_key=None)
            mock_get.assert_called_once()

    @respx.mock
    def test_unit_api_key_provided_skips_get_api_key(self) -> None:
        """When api_key is provided, get_api_key must NOT be called."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        with patch("grokipedia.get_api_key") as mock_get:
            grokipedia.search_grokipedia("test", api_key="explicit-key")
            mock_get.assert_not_called()

    @respx.mock
    def test_unit_returns_dict_on_success(self) -> None:
        """Return type must be dict on 2xx response."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        result = grokipedia.search_grokipedia("test", api_key="k")
        assert isinstance(result, dict)

    # --- Gap: default parameter values and header completeness ---

    @respx.mock
    def test_unit_default_max_results_is_5_in_payload(self) -> None:
        """When max_results is not specified, payload must default to 5."""
        captured, _ = _capture_payload(grokipedia.TAVILY_API_URL)
        grokipedia.search_grokipedia("test", api_key="k")
        assert captured["max_results"] == 5

    @respx.mock
    def test_unit_content_type_header_is_json(self) -> None:
        """Content-Type header must be application/json."""
        captured_ct: str = ""

        def capture_request(request: httpx.Request) -> httpx.Response:
            nonlocal captured_ct
            captured_ct = request.headers.get("content-type", "")
            return httpx.Response(200, json=FAKE_RESPONSE)

        respx.post(grokipedia.TAVILY_API_URL).mock(side_effect=capture_request)
        grokipedia.search_grokipedia("test", api_key="k")
        assert captured_ct == "application/json"


# ===================================================================
# Unit Tests -- render_markdown
# ===================================================================


class TestRenderMarkdown:
    """render_markdown must handle all edge cases and keep every result."""

    def test_empty_results(self) -> None:
        """Empty results list says so instead of listing nothing."""
        text = grokipedia.render_markdown(EMPTY_RESPONSE)
        assert "No results found on grokipedia.com." in text

    def test_no_answer_key(self) -> None:
        """Missing answer leaves out the summary section."""
        data = {"query": "test", "results": [], "response_time": 0.1}
        assert "## AI summary" not in grokipedia.render_markdown(data)

    def test_answer_becomes_summary(self) -> None:
        text = grokipedia.render_markdown(FAKE_RESPONSE)
        assert "## AI summary\n\nA test answer from Tavily.\n" in text

    def test_result_fields(self) -> None:
        text = grokipedia.render_markdown(FAKE_RESPONSE)
        assert "### 1. Test Article\n" in text
        assert urls_in(text) == ["https://grokipedia.com/page/Test"]
        assert "- Relevance: 0.95\n" in text
        assert "This is test content from Grokipedia.\n" in text

    def test_null_fields_render_fallbacks(self) -> None:
        """null title, url, score, and content must not crash."""
        text = grokipedia.render_markdown(NULL_FIELDS_RESPONSE)
        assert "### 1. No title\n" in text
        assert "- Relevance: N/A\n" in text
        assert urls_in(text) == []

    def test_none_raw_content_with_raw_flag(self) -> None:
        """raw_content: null with raw=True must not crash."""
        text = grokipedia.render_markdown(NULL_FIELDS_RESPONSE, raw=True)
        assert "Raw content" not in text

    def test_raw_content_only_with_raw_flag(self) -> None:
        raw = "Full raw content of the test article."
        assert raw not in grokipedia.render_markdown(FAKE_RESPONSE)
        text = grokipedia.render_markdown(FAKE_RESPONSE, raw=True)
        assert f"#### Raw content\n\n{raw}\n" in text

    def test_long_content_kept_whole(self) -> None:
        """A file has no screen width, so content and raw content stay whole."""
        data = {
            "query": "long",
            "results": [
                {
                    "title": "Long",
                    "url": "https://grokipedia.com/page/Long",
                    "content": "x" * 500,
                    "score": 0.5,
                    "raw_content": "y" * 1000,
                }
            ],
        }
        text = grokipedia.render_markdown(data, raw=True)
        assert "x" * 500 in text
        assert "y" * 1000 in text

    def test_unit_empty_dict_does_not_crash(self) -> None:
        """Completely empty dict must not raise."""
        text = grokipedia.render_markdown({})
        assert text.startswith("# Grokipedia search: Unknown\n")


# ===================================================================
# Unit Tests -- write_results
# ===================================================================


class TestWriteResults:
    """write_results must put the file where the caller can find it."""

    def test_default_goes_to_temp_dir(self, temp_dir: Path) -> None:
        path = grokipedia.write_results("# hi\n", "Quantum computing!")
        assert path.parent == temp_dir.resolve()
        assert path.name.startswith("grokipedia-quantum-computing-")
        assert path.suffix == ".md"
        assert path.read_text(encoding="utf-8") == "# hi\n"

    def test_same_query_twice_keeps_both_files(self) -> None:
        first = grokipedia.write_results("a", "same")
        second = grokipedia.write_results("b", "same")
        assert first != second
        assert first.read_text(encoding="utf-8") == "a"

    def test_query_without_letters_gets_a_name(self) -> None:
        path = grokipedia.write_results("x", "???")
        assert path.name.startswith("grokipedia-search-")

    def test_output_creates_parent_folders(self, tmp_path: Path) -> None:
        wanted = tmp_path / "notes" / "q.md"
        path = grokipedia.write_results("# hi\n", "q", str(wanted))
        assert path == wanted.resolve()
        assert path.read_text(encoding="utf-8") == "# hi\n"


# ===================================================================
# Unit Tests -- parse_arguments
# ===================================================================


class TestParseArguments:
    """build_parser must expose correct defaults and flag mappings."""

    def test_unit_default_max_results_is_5(self) -> None:
        """Default --max-results must be 5 when omitted."""
        args = grokipedia.build_parser().parse_args(["test"])
        assert args.max_results == 5

    def test_unit_raw_flag_sets_attribute(self) -> None:
        """--raw must set raw=True."""
        args = grokipedia.build_parser().parse_args(["test", "--raw"])
        assert args.raw is True

    def test_unit_output_none_by_default(self) -> None:
        """output must default to None, the system temp directory."""
        args = grokipedia.build_parser().parse_args(["test"])
        assert args.output is None

    def test_unit_short_o_flag_sets_output(self) -> None:
        """-o must set output."""
        args = grokipedia.build_parser().parse_args(["test", "-o", "out.md"])
        assert args.output == "out.md"

    def test_unit_raw_false_by_default(self) -> None:
        """raw must default to False."""
        args = grokipedia.build_parser().parse_args(["test"])
        assert args.raw is False

    def test_unit_query_positional_captured(self) -> None:
        """Positional query argument must be captured."""
        args = grokipedia.build_parser().parse_args(["quantum computing"])
        assert args.query == "quantum computing"

    # --- Gap: short and long flag variants ---

    def test_unit_short_n_flag_sets_max_results(self) -> None:
        """-n must set max_results."""
        args = grokipedia.build_parser().parse_args(["test", "-n", "10"])
        assert args.max_results == 10

    def test_unit_long_max_results_flag_sets_value(self) -> None:
        """--max-results must set max_results."""
        args = grokipedia.build_parser().parse_args(["test", "--max-results", "15"])
        assert args.max_results == 15


# ===================================================================
# Unit Tests -- main() integration
# ===================================================================


class TestMainFunction:
    """main() must return correct exit codes for all paths."""

    @respx.mock
    def test_success_returns_0(self) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        # Mock extract endpoint (hybrid lookup for canonical page)
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="fake-key"):
            with patch("sys.argv", ["grokipedia.py", "test query"]):
                assert grokipedia.main() == 0

    @respx.mock
    def test_success_answers_with_the_results_file(
        self, capsys: pytest.CaptureFixture[str], temp_dir: Path
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        # Mock extract endpoint (hybrid lookup for canonical page)
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="fake-key"):
            assert grokipedia.main(["test query"]) == 0
        found = succeeded(capsys)
        assert list(found) == ["ok", "file"]
        file = Path(found["file"])
        assert file.parent == temp_dir.resolve()
        assert "### 1. Test Article" in file.read_text(encoding="utf-8")

    @respx.mock
    def test_output_flag_names_the_file(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        wanted = tmp_path / "out" / "results.md"
        with patch("grokipedia.get_api_key", return_value="fake-key"):
            assert grokipedia.main(["test query", "--output", str(wanted)]) == 0
        assert succeeded(capsys) == {"ok": True, "file": str(wanted.resolve())}
        assert wanted.is_file()

    @respx.mock
    def test_unwritable_output_returns_1(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        blocker = tmp_path / "a-file"
        blocker.write_text("", encoding="utf-8")
        with patch("grokipedia.get_api_key", return_value="fake-key"):
            code = grokipedia.main(["test", "--output", str(blocker / "out.md")])
        assert code == 1
        [error] = failed(capsys)["errors"]
        assert error.startswith("Could not write the results:")
        assert error.endswith("pass --output with a writable file path")

    @respx.mock
    def test_verbose_logs_on_stderr_only(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="fake-key"):
            assert grokipedia.main(["pattern", "-v"]) == 0
        out, err = capsys.readouterr()
        assert json.loads(out)["ok"] is True
        assert "Tavily answered in 1.23s" in err
        assert "added the exact page https://grokipedia.com/page/Pattern" in err

    @respx.mock
    def test_http_401_returns_1(self) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        with patch("grokipedia.get_api_key", return_value="bad-key"):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 1

    @respx.mock
    def test_http_401_names_the_key_command(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        with patch("grokipedia.get_api_key", return_value="bad-key"):
            assert grokipedia.main(["test"]) == 1
        assert failed(capsys)["errors"] == [
            "Tavily API returned HTTP 401; verify the API key: "
            "chezmoi secret keyring get --service=tavily --user=api_key"
        ]

    @respx.mock
    def test_http_429_returns_1(self) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(429, json={"error": "rate limited"})
        )
        with patch("grokipedia.get_api_key", return_value="key"):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 1

    def test_api_key_missing_returns_1(self) -> None:
        with patch(
            "grokipedia.get_api_key",
            side_effect=grokipedia.ApiKeyError("no key"),
        ):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 1

    def test_api_key_error_is_the_answer(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch(
            "grokipedia.get_api_key",
            side_effect=grokipedia.ApiKeyError("no key"),
        ):
            assert grokipedia.main(["test"]) == 1
        assert failed(capsys) == {"ok": False, "errors": ["no key"]}

    @respx.mock
    def test_connection_error_returns_1(self) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        with patch("grokipedia.get_api_key", return_value="key"):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 1

    def test_empty_query_returns_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sys.argv", ["grokipedia.py", ""]):
            assert grokipedia.main() == 2
        assert failed(capsys)["help"] == "grokipedia.py --help"

    def test_whitespace_query_returns_2(self) -> None:
        with patch("sys.argv", ["grokipedia.py", "   "]):
            assert grokipedia.main() == 2

    def test_max_results_out_of_range_returns_2(self) -> None:
        with patch("sys.argv", ["grokipedia.py", "test", "-n", "25"]):
            assert grokipedia.main() == 2

    # --- NEW: missing exit-code and boundary tests ---

    @respx.mock
    def test_unit_http_403_returns_1(self) -> None:
        """HTTP 403 must return exit 1 with auth hint."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(403, json={"error": "forbidden"})
        )
        with patch("grokipedia.get_api_key", return_value="bad-key"):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 1

    @respx.mock
    def test_unit_http_500_returns_1(self) -> None:
        """HTTP 500 (not 401/403/429) must still return exit 1."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(500, text="internal server error")
        )
        with patch("grokipedia.get_api_key", return_value="key"):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 1

    def test_unit_keyboard_interrupt_returns_130(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """KeyboardInterrupt during execution must return 130."""
        with patch("grokipedia.get_api_key", side_effect=KeyboardInterrupt):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 130
        assert failed(capsys)["errors"] == ["interrupted"]

    @respx.mock
    def test_unit_max_results_1_valid_boundary(self) -> None:
        """max_results=1 is the lower boundary and must be accepted."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="key"):
            with patch("sys.argv", ["grokipedia.py", "test", "-n", "1"]):
                assert grokipedia.main() == 0

    @respx.mock
    def test_unit_max_results_20_valid_boundary(self) -> None:
        """max_results=20 is the upper boundary and must be accepted."""
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=FAKE_RESPONSE)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="key"):
            with patch("sys.argv", ["grokipedia.py", "test", "-n", "20"]):
                assert grokipedia.main() == 0

    def test_unit_max_results_0_returns_2(self) -> None:
        """max_results=0 is below minimum and must return exit 2."""
        with patch("sys.argv", ["grokipedia.py", "test", "-n", "0"]):
            assert grokipedia.main() == 2

    # --- Gap: resilience to missing keys in API response ---

    @respx.mock
    def test_unit_response_missing_results_key_still_exits_0(self) -> None:
        """API response with no 'results' key must not crash."""
        no_results_response: dict[str, Any] = {
            "query": "test",
            "answer": "An answer.",
            "response_time": 0.5,
            # "results" key is absent entirely
        }
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=no_results_response)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="key"):
            with patch("sys.argv", ["grokipedia.py", "test"]):
                assert grokipedia.main() == 0


# ===================================================================
# Unit Tests -- normalize_page_title
# ===================================================================


class TestNormalizePageTitle:
    """normalize_page_title must convert queries to Grokipedia URL path segments."""

    def test_single_word_lowercase(self) -> None:
        assert grokipedia.normalize_page_title("pattern") == "Pattern"

    def test_single_word_uppercase(self) -> None:
        assert grokipedia.normalize_page_title("Pattern") == "Pattern"

    def test_multi_word_spaces_to_underscores(self) -> None:
        assert (
            grokipedia.normalize_page_title("quantum computing") == "Quantum_computing"
        )

    def test_preserves_interior_caps(self) -> None:
        """Acronyms like AI should stay uppercase."""
        assert grokipedia.normalize_page_title("AI history") == "AI_history"

    def test_strips_whitespace(self) -> None:
        assert grokipedia.normalize_page_title("  pattern  ") == "Pattern"

    def test_collapses_multiple_spaces(self) -> None:
        assert (
            grokipedia.normalize_page_title("quantum   computing")
            == "Quantum_computing"
        )

    def test_empty_string(self) -> None:
        assert grokipedia.normalize_page_title("") == ""

    # --- NEW: boundary and whitespace variants ---

    def test_unit_whitespace_only_returns_empty(self) -> None:
        """Whitespace-only input must return empty string."""
        assert grokipedia.normalize_page_title("   ") == ""

    def test_unit_single_character_capitalized(self) -> None:
        """Single character must be uppercased."""
        assert grokipedia.normalize_page_title("a") == "A"

    def test_unit_tabs_and_mixed_whitespace(self) -> None:
        """Tabs and newlines must be handled like spaces."""
        assert grokipedia.normalize_page_title("\t foo \n") == "Foo"

    # --- Gap: non-alpha first characters ---

    def test_unit_numeric_first_char_preserved(self) -> None:
        """Digit first char must pass through .upper() as no-op."""
        assert grokipedia.normalize_page_title("42 things") == "42_things"

    def test_unit_hyphenated_words_preserved(self) -> None:
        """Hyphens within words must be preserved (not split)."""
        assert (
            grokipedia.normalize_page_title("well-known pattern")
            == "Well-known_pattern"
        )

    def test_unit_single_uppercase_char_identity(self) -> None:
        """Already-uppercase single char must be identity."""
        assert grokipedia.normalize_page_title("Z") == "Z"


# ===================================================================
# Unit Tests -- extract_exact_page
# ===================================================================


FAKE_EXTRACT_RESPONSE: dict[str, Any] = {
    "results": [
        {
            "url": "https://grokipedia.com/page/Pattern",
            "raw_content": "A pattern is a regularity in the world...",
        }
    ],
    "failed_results": [],
    "response_time": 0.8,
}

FAKE_EXTRACT_FAIL_RESPONSE: dict[str, Any] = {
    "results": [],
    "failed_results": [
        {"url": "https://grokipedia.com/page/Nonexistent", "error": "404"}
    ],
    "response_time": 0.3,
}


class TestExtractExactPage:
    """extract_exact_page must try the canonical URL and return a result dict or None."""

    @respx.mock
    def test_returns_result_when_page_exists(self) -> None:
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None

    @respx.mock
    def test_unit_result_url_matches_canonical(self) -> None:
        """Returned URL must be the constructed canonical URL."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert result["url"] == "https://grokipedia.com/page/Pattern"

    @respx.mock
    def test_unit_result_title_is_human_readable(self) -> None:
        """Returned title must have underscores replaced with spaces."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert result["title"] == "Pattern"

    @respx.mock
    def test_unit_result_has_content_key(self) -> None:
        """Returned dict must include a 'content' key."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert "content" in result

    @respx.mock
    def test_unit_result_score_is_1(self) -> None:
        """Exact match must have score 1.0."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert result["score"] == 1.0

    @respx.mock
    def test_returns_none_when_page_missing(self) -> None:
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        result = grokipedia.extract_exact_page("nonexistent", api_key="fake-key")
        assert result is None

    @respx.mock
    def test_returns_none_on_http_error(self) -> None:
        """Network/API errors should not crash, just return None."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(500, text="server error")
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is None

    @respx.mock
    def test_returns_none_on_connection_error(self) -> None:
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            side_effect=httpx.ConnectError("timeout")
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is None

    @respx.mock
    def test_content_truncated_for_snippet(self) -> None:
        """Content in the result should be a short snippet, not the full page."""
        long_response = {
            "results": [
                {
                    "url": "https://grokipedia.com/page/Pattern",
                    "raw_content": "x" * 10000,
                }
            ],
            "failed_results": [],
            "response_time": 0.5,
        }
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=long_response)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert len(result["content"]) <= 503  # 500 chars + "..."

    # --- NEW: additional branches ---

    def test_unit_empty_query_returns_none(self) -> None:
        """Empty query normalizes to '' which should short-circuit to None."""
        result = grokipedia.extract_exact_page("", api_key="fake-key")
        assert result is None

    @respx.mock
    def test_unit_short_content_not_truncated(self) -> None:
        """Content <= 500 chars must be returned in full without '...'."""
        short_response = {
            "results": [
                {
                    "url": "https://grokipedia.com/page/Pattern",
                    "raw_content": "Short content here.",
                }
            ],
            "failed_results": [],
            "response_time": 0.5,
        }
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=short_response)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert result["content"] == "Short content here."

    @respx.mock
    def test_unit_null_raw_content_fallback_empty_string(self) -> None:
        """raw_content: null in API response must fall back to empty string."""
        null_content_response = {
            "results": [
                {
                    "url": "https://grokipedia.com/page/Pattern",
                    "raw_content": None,
                }
            ],
            "failed_results": [],
            "response_time": 0.5,
        }
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=null_content_response)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert result["raw_content"] == ""

    @respx.mock
    def test_unit_title_underscores_replaced_with_spaces(self) -> None:
        """Multi-word title underscores must be replaced with spaces."""
        multi_word_response = {
            "results": [
                {
                    "url": "https://grokipedia.com/page/Quantum_computing",
                    "raw_content": "About quantum computing...",
                }
            ],
            "failed_results": [],
            "response_time": 0.5,
        }
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=multi_word_response)
        )
        result = grokipedia.extract_exact_page("quantum computing", api_key="fake-key")
        assert result is not None
        assert result["title"] == "Quantum computing"

    @respx.mock
    def test_unit_constructs_correct_canonical_url(self) -> None:
        """URL sent to Tavily must follow GROKIPEDIA_BASE/{Title} pattern."""
        captured_urls: list[str] = []

        def capture_request(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            captured_urls.extend(payload.get("urls", []))
            return httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)

        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(side_effect=capture_request)
        grokipedia.extract_exact_page("quantum computing", api_key="fake-key")
        assert captured_urls == ["https://grokipedia.com/page/Quantum_computing"]

    @respx.mock
    def test_unit_api_key_none_calls_get_api_key(self) -> None:
        """When api_key is None, get_api_key must be invoked."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        with patch("grokipedia.get_api_key", return_value="resolved") as mock_get:
            grokipedia.extract_exact_page("pattern", api_key=None)
            mock_get.assert_called_once()

    # --- Gap: returned dict completeness and missing-key resilience ---

    @respx.mock
    def test_unit_result_dict_has_all_required_keys(self) -> None:
        """Returned dict must contain exactly: title, url, content, score, raw_content."""
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert set(result.keys()) == {"title", "url", "content", "score", "raw_content"}

    @respx.mock
    def test_unit_missing_raw_content_key_in_api_response(self) -> None:
        """API response missing raw_content key must fall back to empty string."""
        no_raw_key_response = {
            "results": [
                {
                    "url": "https://grokipedia.com/page/Pattern",
                    # "raw_content" key is absent entirely
                }
            ],
            "failed_results": [],
            "response_time": 0.5,
        }
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=no_raw_key_response)
        )
        result = grokipedia.extract_exact_page("pattern", api_key="fake-key")
        assert result is not None
        assert result["raw_content"] == ""


# ===================================================================
# Unit Tests -- hybrid merge in main()
# ===================================================================


class TestHybridSearch:
    """main() must inject exact-page result when search misses it."""

    @respx.mock
    def test_null_result_url_does_not_abort_search(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=NULL_FIELDS_RESPONSE)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with (
            patch("grokipedia.get_api_key", return_value="fake-key"),
            patch("sys.argv", ["grokipedia.py", "nulls"]),
        ):
            code = grokipedia.main()

        assert code == 0
        text = results_text(capsys)
        assert "### 1. No title" in text
        assert urls_in(text) == []

    @respx.mock
    def test_null_results_does_not_abort_search(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json={"query": "x", "results": None})
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_FAIL_RESPONSE)
        )
        with (
            patch("grokipedia.get_api_key", return_value="fake-key"),
            patch("sys.argv", ["grokipedia.py", "x"]),
        ):
            code = grokipedia.main()

        assert code == 0
        assert "No results found on grokipedia.com." in results_text(capsys)

    @respx.mock
    def test_exact_page_injected_when_missing_from_search(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """If search doesn't return /page/Pattern, extract should inject it."""
        # Search returns results that DON'T include /page/Pattern
        search_response = {
            "query": "pattern",
            "answer": "Patterns are everywhere.",
            "response_time": 1.0,
            "results": [
                {
                    "title": "Pattern grammar",
                    "url": "https://grokipedia.com/page/pattern_grammar",
                    "content": "About pattern grammar.",
                    "score": 0.96,
                }
            ],
        }
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=search_response)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            return_value=httpx.Response(200, json=FAKE_EXTRACT_RESPONSE)
        )

        with patch("grokipedia.get_api_key", return_value="fake-key"):
            with patch("sys.argv", ["grokipedia.py", "pattern"]):
                code = grokipedia.main()

        assert code == 0
        urls = urls_in(results_text(capsys))
        # Exact match should be first
        assert urls == [
            "https://grokipedia.com/page/Pattern",
            "https://grokipedia.com/page/pattern_grammar",
        ]

    @respx.mock
    def test_no_duplicate_when_search_already_has_page(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """If search already includes the exact page, don't add it twice."""
        search_response = {
            "query": "pattern",
            "answer": None,
            "response_time": 1.0,
            "results": [
                {
                    "title": "Pattern",
                    "url": "https://grokipedia.com/page/Pattern",
                    "content": "A pattern is...",
                    "score": 0.99,
                }
            ],
        }
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=search_response)
        )
        # Extract should NOT be called if search already has it,
        # but even if it is, no duplicate should appear.

        with patch("grokipedia.get_api_key", return_value="fake-key"):
            with patch("sys.argv", ["grokipedia.py", "pattern"]):
                code = grokipedia.main()

        assert code == 0
        urls = urls_in(results_text(capsys))
        assert urls == ["https://grokipedia.com/page/Pattern"]  # no duplicate

    @respx.mock
    def test_extract_failure_does_not_break_search(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """If extract fails, search results should still display normally."""
        search_response = {
            "query": "pattern",
            "answer": None,
            "response_time": 1.0,
            "results": [
                {
                    "title": "Pattern grammar",
                    "url": "https://grokipedia.com/page/pattern_grammar",
                    "content": "Grammar stuff.",
                    "score": 0.96,
                }
            ],
        }
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=search_response)
        )
        respx.post(grokipedia.TAVILY_EXTRACT_URL).mock(
            side_effect=httpx.ConnectError("timeout")
        )

        with patch("grokipedia.get_api_key", return_value="fake-key"):
            with patch("sys.argv", ["grokipedia.py", "pattern"]):
                code = grokipedia.main()

        assert code == 0
        urls = urls_in(results_text(capsys))
        assert len(urls) == 1  # just the search result, no crash

    # --- NEW: case-insensitive URL dedup ---

    @respx.mock
    def test_unit_case_insensitive_url_dedup(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """URL comparison for dedup must be case-insensitive."""
        search_response = {
            "query": "pattern",
            "answer": None,
            "response_time": 1.0,
            "results": [
                {
                    "title": "Pattern",
                    # Mixed case -- should still match canonical URL
                    "url": "https://Grokipedia.com/page/Pattern",
                    "content": "A pattern is...",
                    "score": 0.99,
                }
            ],
        }
        respx.post(grokipedia.TAVILY_API_URL).mock(
            return_value=httpx.Response(200, json=search_response)
        )

        with patch("grokipedia.get_api_key", return_value="fake-key"):
            with patch("sys.argv", ["grokipedia.py", "pattern"]):
                code = grokipedia.main()

        assert code == 0
        urls = urls_in(results_text(capsys))
        # Must not inject a duplicate even though casing differs
        assert len(urls) == 1
