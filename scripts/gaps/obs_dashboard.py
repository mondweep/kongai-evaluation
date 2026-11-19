"""Gap 5: a custom dashboard via /v2/dashboards (AI cost per consumer, tokens over time, MCP tool calls, latency by route)."""
import json
from kapi import call, EU, CP
TR = {"type": "relative", "time_range": "24h"}
F = [{"field": "control_plane", "operator": "in", "value": [CP]}]
def tile(col, row, query, chart, cols=3, rows=2):
    return {"type": "chart", "layout": {"position": {"col": col, "row": row}, "size": {"cols": cols, "rows": rows}},
            "definition": {"query": query, "chart": chart}}
tiles = [
  tile(0, 0, {"datasource": "llm_usage", "metrics": ["cost"], "dimensions": ["consumer"], "time_range": TR, "filters": F},
       {"type": "horizontal_bar", "chart_title": "AI cost by consumer (24h)"}),
  tile(3, 0, {"datasource": "llm_usage", "metrics": ["total_tokens"], "dimensions": ["time", "ai_request_model"], "time_range": TR, "granularity": "hourly"},
       {"type": "timeseries_line", "chart_title": "Tokens by requested model"}),
  tile(0, 2, {"datasource": "agentic_usage", "metrics": ["request_count"], "dimensions": ["mcp_tool_name"], "time_range": TR},
       {"type": "donut", "chart_title": "MCP tool calls"}),
  tile(3, 2, {"datasource": "api_usage", "metrics": ["response_latency_p95"], "dimensions": ["route"], "time_range": TR, "limit": 10},
       {"type": "vertical_bar", "chart_title": "p95 latency by route"}),
  tile(0, 4, {"datasource": "api_usage", "metrics": ["error_rate"], "time_range": TR},
       {"type": "single_value", "chart_title": "Error rate (24h)", "decimal_points": 2}, cols=2, rows=1),
]
s, b = call("POST", f"{EU}/v2/dashboards", {"name": "obs-eval AI and MCP overview", "definition": {"tiles": tiles}, "labels": {"eval": "obs-eval"}})
print(s, json.dumps(b)[:1200])
R = {"create": {"status": s, "body": b}}
if s >= 400 and "labels" in json.dumps(b):
    s, b = call("POST", f"{EU}/v2/dashboards", {"name": "obs-eval AI and MCP overview", "definition": {"tiles": tiles}})
    print("retry", s, json.dumps(b)[:600]); R["create_no_labels"] = {"status": s, "body": b}
if s in (200, 201):
    R["get"] = call("GET", f"{EU}/v2/dashboards/{b['id']}")[0]
json.dump(R, open("../../results/gap5-observability.json", "w"), indent=2)
