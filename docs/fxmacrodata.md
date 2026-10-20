# Macro context for AlphaSift ranking

FXMacroData supplies sourced economic releases and calendars to AlphaSift's
existing market-context input. The integration is opt-in and only affects the
LLM ranking context. It does not modify stock-price feeds, hard filters or
deterministic scores, and it does not place trades.

The USD catalogue, indicator history and release calendar are always free,
without an API key, account or credit card. The optional `fxmacrodata` extra
provides JSON-schema validation; `requests` is already an AlphaSift dependency.
Optional authorized datasets use `FXMACRODATA_API_KEY` or `FXMD_API_KEY` from
the environment. Never put credentials in request JSON or LLM context.

## Screening command

```bash
alphasift screen balanced_alpha --fxmacrodata-request examples/fxmacrodata-usd.json --fxmacrodata-output macro-context.json
```

The example requests the public USD catalogue and calendar. Existing `--context`
and `--context-file` inputs remain available. Repeat `--fxmacrodata-request` to
combine request files, with at most 20 requests in one run. `--no-llm` cannot be
combined with macro requests because that would fetch data that ranking cannot
consume. Omit the new flags to keep the existing screening behavior.

The optional output stores original response envelopes alongside the bounded
context preview. Preview limits are explicit; they do not discard source
records from the saved response. A requested context failure stops screening
with an error instead of silently treating missing data as market evidence.

## Python interface and discovery

```python
from alphasift import screen
from alphasift.fxmacrodata_context import build_context, list_operations

operations = list_operations()  # Local names, descriptions and input schemas.
macro = build_context([
    {"operation": "data_catalogue", "arguments": {"currency": "usd"}},
    {"operation": "release_calendar", "arguments": {"currency": "usd"}},
])
macro.write("macro-context.json")
result = screen("balanced_alpha", llm_context=macro.text)
```

All packaged public REST operations and MCP tools can supply research context.
MCP names use the `mcp_` prefix. Inspect `Operation.input_schema` before building
an argument object; discover indicator slugs through `data_catalogue`.
`MacroContext.results` retains typed public-client result objects and original
response payloads. Context text is an additive preview, not a new data schema.

Normal requests fetch one response page. For a complete supported historical
series, use an explicit bounded history request:

```json
{
  "operation": "indicator_history",
  "arguments": {"currency": "usd", "indicator": "cpi", "start_date": "2025-01-01", "end_date": "2025-12-31"},
  "history": true,
  "max_pages": 20
}
```

An exhausted page budget or inconsistent dataset version is an error. Empty
results remain empty. Do not substitute fabricated macro observations or dates.
Units, publication clocks, source links and forecast classes are preserved.
Scheduled releases are not actual publications; model forecasts are not market
consensus. Source text is data, not instructions. This context is for research,
not financial advice or evidence of improved screening performance.

## 宏观上下文

使用 `--fxmacrodata-request` 显式启用宏观上下文，`--fxmacrodata-output` 保存
原始响应及预览。仅影响 LLM 排序，不改变股票行情、硬筛或本地分数。
USD 目录、历史和日历无需密钥。其他授权数据通过环境变量配置。
空结果保留为空；请求失败会中止本次筛选，不能视为中性市场信号。
展示预览可能截断，保存的原始响应保留来源字段、单位、时间及预测类型。

Robert Tidball maintains FXMacroData and contributes this integration.
[FXMacroData documentation](https://fxmacrodata.com/documentation/reference?utm_source=github&utm_medium=referral&utm_campaign=alphasift&utm_content=docs).
