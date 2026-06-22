#!/usr/bin/env python3
"""Square 库存进货预测 — 主入口（只读，不修改任何 Square 数据）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 确保项目根目录在 path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import Settings
from src.order_export import save_must_order_excel
from src.pipeline import run_forecast
from src.reporter import print_summary, save_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="基于 Square 历史销售数据，预测一个月后需要进货的商品及数量。"
    )
    parser.add_argument(
        "--history-days",
        type=int,
        default=None,
        help="历史数据回溯天数（默认读取 .env 中的 HISTORY_DAYS）",
    )
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=None,
        help="预测未来天数（默认 30 天）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="报告输出目录",
    )
    parser.add_argument(
        "--exclude-not-for-sale",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="排除不在售商品（默认开启）",
    )
    args = parser.parse_args()

    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"配置错误: {exc}")
        return 1

    history_days = args.history_days or settings.history_days
    forecast_days = args.forecast_days or settings.forecast_days

    def on_progress(msg: str, _fraction: float | None = None) -> None:
        print(msg)

    forecast = run_forecast(
        settings,
        history_days=history_days,
        forecast_days=forecast_days,
        on_progress=on_progress,
        lang="en",
        exclude_not_for_sale=args.exclude_not_for_sale,
    )
    result = forecast.df

    print_summary(result, forecast_days)

    if not result.empty:
        report_path = save_report(result, args.output)
        print(f"\nFull report saved: {report_path}")
        must_order_path = save_must_order_excel(result, "en", args.output)
        if must_order_path:
            print(f"Must-order list saved: {must_order_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
