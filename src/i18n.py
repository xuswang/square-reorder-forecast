"""Bilingual UI strings (default: English)."""

from __future__ import annotations

import pandas as pd

LANG_EN = "en"
LANG_ZH = "zh"
DEFAULT_LANG = LANG_EN

# Internal priority keys (from forecast model)
PRIORITY_KEYS = ["urgent", "high", "medium", "low", "ok"]
PRIORITY_INTERNAL = {
    "urgent": "紧急",
    "high": "高",
    "medium": "中",
    "low": "低",
    "ok": "充足",
}
PRIORITY_INTERNAL_REV = {v: k for k, v in PRIORITY_INTERNAL.items()}

PRIORITY_COLORS = {
    "紧急": "#e74c3c",
    "高": "#e67e22",
    "中": "#f1c40f",
    "低": "#3498db",
    "充足": "#2ecc71",
}
PRIORITY_ORDER_INTERNAL = ["紧急", "高", "中", "低", "充足"]

STRINGS: dict[str, dict[str, str]] = {
    "page_title": {"en": "Reorder Forecast", "zh": "进货预测"},
    "app_title": {"en": "📦 Square Reorder Forecast", "zh": "📦 Square 进货预测"},
    "app_subtitle": {
        "en": "Forecast upcoming inventory needs from historical sales and current stock.",
        "zh": "基于历史销售与当前库存，预测未来需要进货的商品及数量。",
    },
    "lang_label": {"en": "Language", "zh": "语言"},
    "settings": {"en": "⚙️ Settings", "zh": "⚙️ 设置"},
    "api_credentials": {"en": "API Credentials", "zh": "API 凭证"},
    "api_hint": {
        "en": "Get credentials from [Square Developer](https://developer.squareup.com/apps)",
        "zh": "从 [Square Developer](https://developer.squareup.com/apps) 获取",
    },
    "access_token": {"en": "Access Token", "zh": "Access Token"},
    "token_placeholder": {"en": "EAAA...", "zh": "EAAA..."},
    "token_help": {
        "en": "Production or Sandbox Access Token",
        "zh": "Production 或 Sandbox Access Token",
    },
    "token_privacy": {
        "en": "🔐 Your Access Token stays on this device. "
        "It is sent **only** to Square's official API — never stored on or uploaded to any other server.",
        "zh": "🔐 Access Token **完全留在本地**，仅用于直连 Square 官方 API，"
        "不会上传或保存到任何第三方服务器。",
    },
    "environment": {"en": "Environment", "zh": "环境"},
    "location_id": {"en": "Location ID (optional)", "zh": "门店 Location ID（可选）"},
    "location_placeholder": {
        "en": "Leave blank to use the first location",
        "zh": "留空则自动使用第一个门店",
    },
    "forecast_params": {"en": "Forecast Parameters", "zh": "预测参数"},
    "readonly_notice": {
        "en": "🔒 Read-only — inventory and orders are never modified",
        "zh": "🔒 只读模式 — 不会修改库存或订单",
    },
    "history_days": {"en": "History window (days)", "zh": "历史数据天数"},
    "forecast_days": {"en": "Forecast horizon (days)", "zh": "预测未来天数"},
    "safety_stock_z": {"en": "Safety stock factor", "zh": "安全库存系数"},
    "safety_stock_help": {
        "en": "Higher = more conservative. 1.65 ≈ 95% service level",
        "zh": "越高越保守，1.65 ≈ 95% 服务水平",
    },
    "exclude_not_for_sale": {
        "en": "Exclude not-for-sale products",
        "zh": "排除不在售商品",
    },
    "exclude_not_for_sale_help": {
        "en": "Skip archived, delisted, sold-out, or non-sellable items in Square catalog",
        "zh": "跳过 Square 目录中已归档、下架、售罄或不可售的商品",
    },
    "metric_excluded": {"en": "Excluded (not for sale)", "zh": "已排除(停售)"},
    "run_forecast": {"en": "🚀 Run Forecast", "zh": "🚀 开始预测"},
    "err_missing_token": {"en": "Please enter a Square Access Token", "zh": "请填写 Square Access Token"},
    "err_invalid_env": {
        "en": "Environment must be production or sandbox",
        "zh": "环境请选择 production 或 sandbox",
    },
    "preparing": {"en": "Preparing...", "zh": "准备中..."},
    "fetching": {
        "en": "Fetching data from Square and running forecast...",
        "zh": "正在从 Square 拉取数据并计算...",
    },
    "done": {"en": "Done", "zh": "完成"},
    "forecast_complete": {"en": "Forecast complete!", "zh": "预测完成！"},
    "forecast_failed": {"en": "Forecast failed: {error}", "zh": "预测失败: {error}"},
    "empty_hint": {
        "en": "Enter your Square API credentials on the left and click **Run Forecast**.",
        "zh": "在左侧填写 Square API 并点击 **开始预测** 生成报告。",
    },
    "steps_title": {"en": "**Getting started**", "zh": "**使用步骤**"},
    "step_1": {
        "en": "1. Enter your **Access Token** from the Square Developer Dashboard",
        "zh": "1. 在左侧填入 **Access Token**（从 Square Developer Dashboard 获取）",
    },
    "step_2": {
        "en": "2. Choose **production** or **sandbox**",
        "zh": "2. 选择 **production** 或 **sandbox** 环境",
    },
    "step_3": {
        "en": "3. Adjust parameters and click **Run Forecast**",
        "zh": "3. 调整预测参数后点击 **开始预测**",
    },
    "features_title": {"en": "**Features**", "zh": "**功能说明**"},
    "feature_1": {
        "en": "- Read-only sync of Square sales and inventory",
        "zh": "- 自动从 Square 读取订单销量与库存（只读）",
    },
    "feature_2": {
        "en": "- Weighted daily sales + safety stock model",
        "zh": "- 加权日均销量 + 安全库存模型",
    },
    "feature_3": {
        "en": "- Search, filter, charts, and Excel export",
        "zh": "- 支持搜索、筛选、图表分析与 Excel 导出",
    },
    "metric_total_products": {"en": "Total products", "zh": "商品总数"},
    "metric_need_reorder": {"en": "Need reorder", "zh": "需要进货"},
    "metric_urgent_high": {"en": "Urgent / High", "zh": "紧急/高优先"},
    "metric_total_qty": {"en": "Suggested reorder qty", "zh": "建议进货总量"},
    "metric_horizon": {"en": "Forecast horizon", "zh": "预测周期"},
    "metric_days": {"en": "{n} days", "zh": "{n} 天"},
    "meta_caption": {
        "en": "Location `{loc}` · {history}d history · {sales:,} sales records · {inv:,} in stock",
        "zh": "门店 `{loc}` · 历史 {history} 天 · {sales:,} 条销量记录 · {inv:,} 种有库存",
    },
    "chart_no_reorder": {
        "en": "All products are sufficiently stocked.",
        "zh": "所有商品库存充足，无需进货。",
    },
    "chart_priority_dist": {"en": "Priority distribution", "zh": "优先级分布"},
    "chart_top15": {"en": "Top 15 reorder suggestions", "zh": "建议进货 Top 15"},
    "chart_scatter": {
        "en": "Stock vs forecast demand (bubble size = reorder qty)",
        "zh": "库存 vs 预测需求（气泡大小 = 建议进货量）",
    },
    "tab_charts": {"en": "📊 Charts", "zh": "📊 图表分析"},
    "tab_stockout": {"en": "⏳ Stock runway", "zh": "⏳ 售罄预测"},
    "tab_list": {"en": "📋 Reorder list", "zh": "📋 进货清单"},
    "stockout_title": {"en": "Stock runway by product", "zh": "各商品预计售罄时间"},
    "stockout_desc": {
        "en": "Assumes **no restocking** — based on current stock and weighted daily sales only. "
        "Sorted by estimated stockout date (earliest first).",
        "zh": "假设 **完全不补货** — 仅根据当前库存和加权日均销量估算。"
        "按 **预计售罄日期** 升序排列（最早卖完的在最前）。",
    },
    "stockout_no_restock_banner": {
        "en": "📌 No-restock scenario: when each product is expected to sell out at the current sales rate.",
        "zh": "📌 零补货场景：在不进货的情况下，各商品预计何时卖完。",
    },
    "output_mode": {"en": "Output focus", "zh": "输出重点"},
    "output_stockout_first": {
        "en": "Stockout first (no restock)",
        "zh": "先售罄预测（不补货）",
    },
    "output_full": {"en": "Full reorder forecast", "zh": "完整进货预测"},
    "output_both": {"en": "Both", "zh": "两者都要"},
    "output_mode_help": {
        "en": "Choose what to show first after analysis runs",
        "zh": "选择分析完成后优先展示的内容",
    },
    "show_reorder_section": {
        "en": "Show reorder forecast & purchase list",
        "zh": "展开查看进货预测与补货清单",
    },
    "stockout_sheet": {"en": "Stockout (no restock)", "zh": "售罄预测(不补货)"},
    "stockout_filename": {
        "en": "stockout_no_restock_{ts}.xlsx",
        "zh": "售罄预测_不补货_{ts}.xlsx",
    },
    "stockout_saved": {
        "en": "Stockout list auto-saved: `{path}`",
        "zh": "售罄预测已自动保存：`{path}`",
    },
    "stockout_search": {"en": "Search products", "zh": "搜索商品"},
    "stockout_only_with_date": {
        "en": "Only products with an estimate",
        "zh": "仅显示可估算的商品",
    },
    "stockout_count": {
        "en": "Showing {shown} products · {urgent} out of stock or within 7 days",
        "zh": "共 {shown} 种商品 · {urgent} 种已断货或 7 天内售罄",
    },
    "stockout_download": {
        "en": "⬇️ Download stock runway CSV",
        "zh": "⬇️ 下载售罄预测 CSV",
    },
    "col_stockout_date": {"en": "Est. stockout date", "zh": "预计售罄日"},
    "list_title": {"en": "Reorder list", "zh": "进货清单"},
    "search_placeholder": {"en": "Filter by product name...", "zh": "输入关键词过滤..."},
    "search_label": {"en": "Search products", "zh": "搜索商品名称"},
    "priority_filter": {"en": "Priority filter", "zh": "优先级筛选"},
    "only_reorder": {"en": "Show reorder only", "zh": "仅显示需要进货"},
    "showing_count": {
        "en": "Showing {shown} / {total} products",
        "zh": "显示 {shown} / {total} 种商品",
    },
    "download_excel": {"en": "⬇️ Download Excel (all)", "zh": "⬇️ 下载 Excel（全部）"},
    "download_csv": {"en": "⬇️ Download CSV (filtered)", "zh": "⬇️ 下载 CSV（筛选结果）"},
    "save_output": {"en": "💾 Save to output folder", "zh": "💾 保存到 output 文件夹"},
    "saved_to": {"en": "Saved: {path}", "zh": "已保存: {path}"},
    "excel_sheet": {"en": "Reorder Forecast", "zh": "进货预测"},
    "excel_filename": {"en": "reorder_forecast_{ts}.xlsx", "zh": "进货预测_{ts}.xlsx"},
    "csv_filename": {"en": "reorder_forecast_filtered_{ts}.csv", "zh": "进货预测_筛选_{ts}.csv"},
    "copyright": {
        "en": "© Xushen Wang. All rights reserved.",
        "zh": "© Xushen Wang. 版权所有。",
    },
    # Progress messages
    "prog_connecting": {"en": "Connecting to Square API...", "zh": "正在连接 Square API..."},
    "prog_connected": {"en": "Connected to location {loc}", "zh": "已连接门店 {loc}"},
    "prog_fetch_orders": {
        "en": "Fetching sales orders ({days} days)...",
        "zh": "拉取近 {days} 天销售订单...",
    },
    "prog_orders_done": {
        "en": "Loaded {records} daily sales records ({products} products)",
        "zh": "已获取 {records} 条日销量记录（{products} 种商品）",
    },
    "prog_fetch_inventory": {"en": "Fetching current inventory...", "zh": "拉取当前库存..."},
    "prog_inventory_done": {
        "en": "Loaded inventory for {count} products",
        "zh": "已获取 {count} 种商品库存",
    },
    "prog_fetch_names": {
        "en": "Loading {count} product names...",
        "zh": "获取 {count} 个商品名称...",
    },
    "prog_names_done": {"en": "Product names loaded", "zh": "商品名称加载完成"},
    "prog_running_model": {"en": "Running forecast model...", "zh": "运行预测模型..."},
    "prog_complete": {"en": "Forecast complete", "zh": "预测完成"},
    # Column headers
    "col_product": {"en": "Product", "zh": "商品名称"},
    "col_sku": {"en": "SKU", "zh": "SKU"},
    "col_stock": {"en": "Current stock", "zh": "当前库存"},
    "col_days_left": {
        "en": "Days until stockout",
        "zh": "库存可售天数",
    },
    "col_days_left_na": {"en": "—", "zh": "—"},
    "col_total_sales": {"en": "Sales ({days}d)", "zh": "近{days}天总销量"},
    "col_active_days": {"en": "Days with sales", "zh": "有销售天数"},
    "col_daily_rate": {"en": "Weighted daily avg", "zh": "日均销量(加权)"},
    "col_forecast": {
        "en": "Demand in next {days}d",
        "zh": "未来{days}天预计销量",
    },
    "col_safety": {"en": "Safety stock", "zh": "安全库存"},
    "col_reorder": {
        "en": "Reorder qty (next {days}d)",
        "zh": "建议进货量(未来{days}天)",
    },
    "col_priority": {"en": "Priority", "zh": "优先级"},
    "col_for_sale": {"en": "For sale", "zh": "在售状态"},
    "status_for_sale": {"en": "For sale", "zh": "在售"},
    "status_not_for_sale": {"en": "Not for sale", "zh": "停售"},
    # Priority labels
    "pri_urgent": {"en": "Urgent", "zh": "紧急"},
    "pri_high": {"en": "High", "zh": "高"},
    "pri_medium": {"en": "Medium", "zh": "中"},
    "pri_low": {"en": "Low", "zh": "低"},
    "pri_ok": {"en": "OK", "zh": "充足"},
    "chart_priority": {"en": "Priority", "zh": "优先级"},
    "chart_count": {"en": "Count", "zh": "数量"},
    # Must-order export
    "must_order_title": {"en": "📌 Must Order Now", "zh": "📌 必须立即下单"},
    "must_order_desc": {
        "en": "Urgent / high-priority items and out-of-stock products. "
        "Fill in **lead time** and **shipping method** (e.g. international express vs slow freight).",
        "zh": "紧急/高优先级及已断货商品。请在 Excel 中填写 **到货周期** 和 **运输方式**（如国际快递、海运慢货等）。",
    },
    "must_order_count": {
        "en": "**{count}** products must be ordered now",
        "zh": "共 **{count}** 种商品必须立即下单",
    },
    "must_order_download": {
        "en": "⬇️ Download Must-Order Excel",
        "zh": "⬇️ 下载必须下单 Excel",
    },
    "must_order_empty": {
        "en": "No urgent orders right now — all critical items are stocked.",
        "zh": "当前没有必须立即下单的商品。",
    },
    "must_order_saved": {
        "en": "Must-order list auto-saved: `{path}`",
        "zh": "必须下单清单已自动保存：`{path}`",
    },
    "mo_filename": {
        "en": "must_order_{ts}.xlsx",
        "zh": "必须下单_{ts}.xlsx",
    },
    "mo_sheet_name": {"en": "Must Order", "zh": "必须下单"},
    "mo_guide_sheet": {"en": "Guide", "zh": "填写说明"},
    "mo_empty": {"en": "No items", "zh": "无商品"},
    "mo_col_product": {"en": "Product", "zh": "产品名"},
    "mo_col_sku": {"en": "SKU", "zh": "SKU"},
    "mo_col_stock": {"en": "Current Stock", "zh": "现有库存"},
    "mo_col_days_left": {"en": "Days until stockout", "zh": "库存可售天数"},
    "mo_col_reorder": {
        "en": "Reorder qty (forecast period)",
        "zh": "建议进货量(预测周期)",
    },
    "mo_col_priority": {"en": "Priority", "zh": "优先级"},
    "mo_col_lead_time": {"en": "Lead Time (days)", "zh": "到货周期(天)"},
    "mo_col_shipping": {"en": "Shipping Method", "zh": "运输方式"},
    "mo_col_notes": {"en": "Notes", "zh": "备注"},
    "mo_guide_title": {"en": "How to fill this order list", "zh": "填写说明"},
    "mo_guide_shipping_header": {"en": "Shipping options", "zh": "运输方式选项"},
    "mo_guide_shipping_desc": {
        "en": "Select from dropdown in the Shipping Method column",
        "zh": "在「运输方式」列从下拉菜单选择",
    },
    "mo_guide_lead_header": {"en": "Lead time", "zh": "到货周期"},
    "mo_guide_lead_desc": {
        "en": "Estimated days until goods arrive",
        "zh": "预计多少天能到货",
    },
    "mo_guide_tip": {
        "en": "Tip: Order slow-shipping / international items earlier than fast-moving stock.",
        "zh": "提示：海运/国际快递等慢货请比快销品更早下单。",
    },
    "mo_shipping_validation": {
        "en": "Please choose a shipping method from the list",
        "zh": "请从列表中选择运输方式",
    },
}

PRIORITY_I18N_KEYS = {
    "紧急": "pri_urgent",
    "高": "pri_high",
    "中": "pri_medium",
    "低": "pri_low",
    "充足": "pri_ok",
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    entry = STRINGS.get(key, {})
    text = entry.get(lang) or entry.get(LANG_EN) or key
    if kwargs:
        return text.format(**kwargs)
    return text


def priority_label(internal: str, lang: str) -> str:
    i18n_key = PRIORITY_I18N_KEYS.get(internal, internal)
    return t(i18n_key, lang)


def priority_display_order(lang: str) -> list[str]:
    return [priority_label(p, lang) for p in PRIORITY_ORDER_INTERNAL]


def priority_from_display(display: str, lang: str) -> str | None:
    for internal in PRIORITY_ORDER_INTERNAL:
        if priority_label(internal, lang) == display:
            return internal
    return None


def _internal_col_map(history_days: int, forecast_days: int) -> dict[str, str]:
    return {
        "商品名称": "col_product",
        "SKU": "col_sku",
        "在售状态": "col_for_sale",
        "当前库存": "col_stock",
        "库存可售天数": "col_days_left",
        "预计售罄日": "col_stockout_date",
        f"近{history_days}天总销量": "col_total_sales",
        "有销售天数": "col_active_days",
        "日均销量(加权)": "col_daily_rate",
        f"预测{forecast_days}天需求": "col_forecast",
        "安全库存": "col_safety",
        "建议进货量": "col_reorder",
        "优先级": "col_priority",
    }


def forecast_col_internal(forecast_days: int) -> str:
    return f"预测{forecast_days}天需求"


def localize_dataframe(
    df: pd.DataFrame,
    lang: str,
    history_days: int,
    forecast_days: int,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    if "优先级" in out.columns:
        out["优先级"] = out["优先级"].map(lambda p: priority_label(p, lang))
    if "在售状态" in out.columns:
        out["在售状态"] = out["在售状态"].map(
            lambda s: t("status_for_sale", lang) if s == "在售" else t("status_not_for_sale", lang)
        )
    days_col = "库存可售天数"
    if days_col in out.columns:
        out[days_col] = out[days_col].apply(
            lambda d: t("col_days_left_na", lang) if d is None or (isinstance(d, float) and pd.isna(d)) else d
        )
    stockout_col = "预计售罄日"
    if stockout_col in out.columns:
        out[stockout_col] = out[stockout_col].apply(
            lambda d: t("col_days_left_na", lang)
            if d is None or (isinstance(d, float) and pd.isna(d))
            else pd.Timestamp(d).strftime("%Y-%m-%d")
        )
    col_map = _internal_col_map(history_days, forecast_days)
    rename: dict[str, str] = {}
    for internal, i18n_key in col_map.items():
        if internal in out.columns:
            days = history_days if internal.startswith("近") else forecast_days
            if i18n_key in ("col_forecast", "col_reorder"):
                rename[internal] = t(i18n_key, lang, days=forecast_days)
            else:
                rename[internal] = t(i18n_key, lang, days=days)
    return out.rename(columns=rename)


def reorder_qty_col(lang: str, forecast_days: int) -> str:
    return t("col_reorder", lang, days=forecast_days)


def product_col(lang: str) -> str:
    return t("col_product", lang)


def priority_col(lang: str) -> str:
    return t("col_priority", lang)


def forecast_col_display(lang: str, forecast_days: int) -> str:
    return t("col_forecast", lang, days=forecast_days)
