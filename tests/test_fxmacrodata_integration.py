import json
import sys

import pandas as pd
import pytest

from alphasift import cli
from alphasift.context import build_llm_context
from alphasift.fxmacrodata_context import build_context
from alphasift.fxmacrodata_context._fxmacrodata_client import Result, FXMacroDataError


class Client:
    def execute(self, operation, arguments):
        return Result(operation, {"data": [{"fixture": "macro-synthetic", "unit": "fixture-unit"}]})


def test_context_is_consumed_by_native_ranking_assembly():
    macro = build_context([{"operation": "release_calendar"}], client=Client())
    text = build_llm_context(snapshot_df=pd.DataFrame(), base_context=macro.text)
    assert "macro-synthetic" in text and "fixture-unit" in text


def test_screen_cli_passes_context_and_retains_original_output(monkeypatch, tmp_path):
    import alphasift.fxmacrodata_context as integration
    request = tmp_path / "requests.json"
    request.write_text(json.dumps({"operation": "release_calendar", "arguments": {"currency": "usd"}}))
    output = tmp_path / "macro.json"
    monkeypatch.setattr(integration, "build_context", lambda requests: build_context(requests, client=Client()))
    class Done(Exception):
        pass
    def screen(strategy, **kwargs):
        assert strategy == "balanced_alpha"
        assert "existing context" in kwargs["llm_context"]
        assert "macro-synthetic" in kwargs["llm_context"]
        raise Done
    monkeypatch.setattr(cli, "screen", screen)
    monkeypatch.setattr(sys, "argv", ["alphasift", "screen", "balanced_alpha", "--context", "existing context", "--fxmacrodata-request", str(request), "--fxmacrodata-output", str(output)])
    with pytest.raises(Done):
        cli.main()
    assert json.loads(output.read_text())["results"][0]["data"]["data"][0]["fixture"] == "macro-synthetic"


def test_opt_out_does_not_fetch_macro_context(monkeypatch):
    import alphasift.fxmacrodata_context as integration
    monkeypatch.setattr(integration, "build_context", lambda *a, **k: pytest.fail("Unexpected network consumer"))
    class Done(Exception):
        pass
    def screen(*args, **kwargs):
        assert kwargs["llm_context"] is None
        raise Done
    monkeypatch.setattr(cli, "screen", screen)
    monkeypatch.setattr(sys, "argv", ["alphasift", "screen", "balanced_alpha", "--no-llm"])
    with pytest.raises(Done):
        cli.main()


@pytest.mark.parametrize("args", [
    ["--no-llm", "--fxmacrodata-request", "unused.json"],
    ["--fxmacrodata-output", "unused.json"],
])
def test_invalid_combinations_stop_before_screening(monkeypatch, args):
    monkeypatch.setattr(cli, "screen", lambda *a, **k: pytest.fail("Invalid macro configuration reached screening"))
    monkeypatch.setattr(sys, "argv", ["alphasift", "screen", "balanced_alpha", *args])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
