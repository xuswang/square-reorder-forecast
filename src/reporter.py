"""生成预测报告。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def save_report(df: pd.DataFrame, output_dir: str | Path = "output") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = output_path / f"进货预测_{timestamp}.xlsx"
    csv_path = output_path / f"进货预测_{timestamp}.csv"

    df.to_excel(excel_path, index=False, sheet_name="进货预测")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    return excel_path


def print_summary(df: pd.DataFrame, forecast_days: int) -> None:
    if df.empty:
        print("没有可预测的商品数据。请确认 Square 账户中有历史订单和库存记录。")
        return

    need_reorder = df[df["建议进货量"] > 0]
    urgent = need_reorder[need_reorder["优先级"].isin(["紧急", "高"])]

    print(f"\n{'=' * 60}")
    print(f"  未来 {forecast_days} 天进货预测报告")
    print(f"{'=' * 60}")
    print(f"  商品总数: {len(df)}")
    print(f"  需要进货: {len(need_reorder)} 种")
    print(f"  紧急/高优先级: {len(urgent)} 种")
    print(f"{'=' * 60}\n")

    if need_reorder.empty:
        print("所有商品库存充足，暂无需进货。")
        return

    display_cols = [
        "商品名称",
        "当前库存",
        "日均销量(加权)",
        f"预测{forecast_days}天需求",
        "建议进货量",
        "优先级",
    ]
    cols = [c for c in display_cols if c in need_reorder.columns]
    print(need_reorder[cols].head(20).to_string(index=False))

    if len(need_reorder) > 20:
        print(f"\n... 还有 {len(need_reorder) - 20} 种商品，详见 Excel 报告")
