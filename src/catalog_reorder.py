"""根据 Square 库存导出 + 不必进货清单，生成建议进货表。"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd

from src.i18n import priority_label, t

PRIORITY_SORT = {"紧急": 0, "Urgent": 0, "高": 1, "High": 1, "中": 2, "Medium": 2, "低": 3, "Low": 3}


def norm_sku(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    try:
        return str(int(float(text)))
    except (TypeError, ValueError):
        return text


def _norm_name(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _find_column(columns: list[str], *candidates: str) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for cand in candidates:
        key = cand.lower()
        if key in lowered:
            return lowered[key]
    for col in columns:
        low = col.lower()
        for cand in candidates:
            if cand.lower() in low:
                return col
    return None


def _read_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower()
    buffer = io.BytesIO(file_bytes)
    if name.endswith(".csv"):
        return pd.read_csv(buffer)
    return pd.read_excel(buffer)


def parse_square_catalog(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """解析 Square 目录/库存 Excel 导出。"""
    raw = _read_upload(file_bytes, filename)
    if raw.empty:
        raise ValueError("ERR_CATALOG_EMPTY")

    # Square 导出：首行是列名标签
    first_cell = str(raw.iloc[0, 0]) if raw.shape[1] else ""
    if first_cell in ("Reference Handle", "参考句柄") or "Item Name" in str(raw.iloc[0].values):
        raw.columns = raw.iloc[0]
        raw = raw.iloc[1:].reset_index(drop=True)

    cols = [str(c) for c in raw.columns]
    name_col = _find_column(cols, "Item Name", "商品名称", "Product")
    sku_col = _find_column(cols, "SKU")
    stock_col = _find_column(
        cols,
        "Current Quantity TOKIMO",
        "Current Quantity",
        "Current stock",
        "当前库存",
    )
    alert_col = _find_column(cols, "Stock Alert Count TOKIMO", "Stock Alert Count", "库存预警")
    vendor_col = _find_column(cols, "Default Vendor Name", "Vendor", "供应商")
    archived_col = _find_column(cols, "Archived", "已归档")
    sellable_col = _find_column(cols, "Sellable", "可售")

    if not name_col or not stock_col:
        raise ValueError("ERR_CATALOG_COLUMNS")

    out = pd.DataFrame(
        {
            "name": raw[name_col].map(_norm_name),
            "sku": raw[sku_col].map(norm_sku) if sku_col else "",
            "stock": pd.to_numeric(raw[stock_col], errors="coerce").fillna(0).astype(int),
            "alert": (
                pd.to_numeric(raw[alert_col], errors="coerce").fillna(5).astype(int)
                if alert_col
                else 5
            ),
            "vendor": raw[vendor_col].fillna("").astype(str) if vendor_col else "",
            "archived": raw[archived_col].fillna("N").astype(str).str.upper()
            if archived_col
            else "N",
            "sellable": raw[sellable_col].fillna("Y").astype(str).str.upper()
            if sellable_col
            else "Y",
        }
    )
    out = out[out["name"] != ""].reset_index(drop=True)
    if out.empty:
        raise ValueError("ERR_CATALOG_EMPTY")
    return out


def parse_skip_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """解析「不必进货 / 售罄安全」参考表（本应用导出或同类格式）。"""
    raw = _read_upload(file_bytes, filename)
    if raw.empty:
        raise ValueError("ERR_SKIP_EMPTY")

    cols = [str(c) for c in raw.columns]
    name_col = _find_column(cols, "Product", "商品名称", "Item Name")
    sku_col = _find_column(cols, "SKU")
    stock_col = _find_column(cols, "Current stock", "当前库存", "Current Stock")
    days_col = _find_column(cols, "Days until stockout", "库存可售天数")
    rate_col = _find_column(cols, "Weighted daily avg", "日均销量(加权)")

    if not name_col:
        raise ValueError("ERR_SKIP_COLUMNS")

    out = pd.DataFrame(
        {
            "name": raw[name_col].map(_norm_name),
            "sku": raw[sku_col].map(norm_sku) if sku_col else "",
            "stock": pd.to_numeric(raw[stock_col], errors="coerce") if stock_col else pd.NA,
            "days_left": pd.to_numeric(raw[days_col], errors="coerce") if days_col else pd.NA,
            "daily_rate": pd.to_numeric(raw[rate_col], errors="coerce") if rate_col else pd.NA,
        }
    )
    out = out[out["name"] != ""].reset_index(drop=True)
    if out.empty:
        raise ValueError("ERR_SKIP_EMPTY")
    return out


def _is_skipped(sku: str, name: str, skip_skus: set[str], skip_names: set[str]) -> bool:
    if sku and sku in skip_skus:
        return True
    norm = name.lower()
    return bool(norm and norm in skip_names)


def _lookup_catalog_row(
    catalog: pd.DataFrame,
    sku: str,
    name: str,
) -> pd.Series | None:
    if sku:
        rows = catalog[catalog["sku"] == sku]
        if not rows.empty:
            return rows.iloc[0]
    rows = catalog[catalog["name"].str.lower() == name.lower()]
    if not rows.empty:
        return rows.iloc[0]
    return None


def _active_catalog(catalog: pd.DataFrame) -> pd.DataFrame:
    archived = catalog["archived"].isin(("N", "NO", "FALSE", "0", ""))
    sellable = catalog["sellable"].isin(("Y", "YES", "TRUE", "1", ""))
    return catalog[archived & sellable].copy()


def _priority_display(internal: str, lang: str) -> str:
    mapping = {
        "Urgent": "紧急",
        "High": "高",
        "Medium": "中",
        "Low": "低",
    }
    key = mapping.get(internal, internal)
    if key in ("紧急", "高", "中", "低", "充足"):
        return priority_label(key, lang)
    return internal


@dataclass(frozen=True)
class CatalogReorderResult:
    must_order: pd.DataFrame
    out_of_stock: pd.DataFrame
    all_items: pd.DataFrame
    skipped: pd.DataFrame
    summary: pd.DataFrame


def build_catalog_reorder(
    catalog: pd.DataFrame,
    skip: pd.DataFrame,
    *,
    forecast_df: pd.DataFrame | None = None,
    lang: str = "en",
    oos_default_qty: int = 20,
    include_forecast_must_order: bool = True,
) -> CatalogReorderResult:
    skip_skus = {s for s in skip["sku"].tolist() if s}
    skip_names = {n.lower() for n in skip["name"].tolist() if n}
    active = _active_catalog(catalog)

    rows: dict[str, dict] = {}

    def put_row(
        key: str,
        *,
        product: str,
        sku: str,
        stock: int,
        reorder_qty: int,
        priority: str,
        vendor: str,
        source_key: str,
        days_left: object = "",
        daily_rate: object = "",
    ) -> None:
        if reorder_qty <= 0:
            return
        if key in rows:
            if reorder_qty > rows[key]["_reorder_internal"]:
                rows[key]["_reorder_internal"] = reorder_qty
                rows[key]["_priority_internal"] = priority
            return
        rows[key] = {
            "product": product,
            "sku": sku,
            "stock": stock,
            "_reorder_internal": reorder_qty,
            "_priority_internal": priority,
            "vendor": vendor,
            "source_key": source_key,
            "days_left": days_left,
            "daily_rate": daily_rate,
        }

    if include_forecast_must_order and forecast_df is not None and not forecast_df.empty:
        mask = (forecast_df["建议进货量"] > 0) & (
            forecast_df["优先级"].isin(("紧急", "高")) | (forecast_df["当前库存"] <= 0)
        )
        subset = forecast_df.loc[mask]
        for _, r in subset.iterrows():
            name = _norm_name(r["商品名称"])
            sku = norm_sku(r.get("SKU", ""))
            if _is_skipped(sku, name, skip_skus, skip_names):
                continue
            cat_row = _lookup_catalog_row(active, sku, name)
            stock = int(cat_row["stock"]) if cat_row is not None else int(r["当前库存"])
            vendor = str(cat_row["vendor"]) if cat_row is not None else ""
            orig_reorder = int(r["建议进货量"])
            orig_stock = int(r["当前库存"])
            reorder = max(0, orig_reorder - (stock - orig_stock))
            pri = str(r["优先级"])
            key = sku or name.lower()
            put_row(
                key,
                product=name,
                sku=sku,
                stock=stock,
                reorder_qty=reorder,
                priority=pri,
                vendor=vendor,
                source_key="source_forecast",
                days_left=r.get("库存可售天数", ""),
            )

    for _, c in active.iterrows():
        sku, name = c["sku"], c["name"]
        if _is_skipped(sku, name, skip_skus, skip_names):
            continue
        stock = int(c["stock"])
        if stock > 0:
            continue
        key = sku or name.lower()
        if key in rows:
            continue
        alert = int(c["alert"])
        reorder = max(oos_default_qty, alert * 4) - max(stock, 0)
        put_row(
            key,
            product=name,
            sku=sku,
            stock=stock,
            reorder_qty=reorder,
            priority="紧急",
            vendor=str(c["vendor"]),
            source_key="source_oos",
        )

    sorted_rows = sorted(
        rows.values(),
        key=lambda r: (
            PRIORITY_SORT.get(r["_priority_internal"], 9),
            -r["_reorder_internal"],
        ),
    )

    display_rows = []
    for row in sorted_rows:
        display_rows.append(
            {
                t("cr_col_product", lang): row["product"],
                t("cr_col_sku", lang): row["sku"],
                t("cr_col_stock", lang): row["stock"],
                t("cr_col_reorder", lang): int(row["_reorder_internal"]),
                t("cr_col_priority", lang): _priority_display(row["_priority_internal"], lang),
                t("cr_col_vendor", lang): row["vendor"],
                t("cr_col_source", lang): t(row["source_key"], lang),
                t("cr_col_days_left", lang): row["days_left"],
                t("cr_col_daily_rate", lang): row["daily_rate"],
            }
        )

    all_df = pd.DataFrame(display_rows)

    must_df = all_df[all_df[t("cr_col_source", lang)] == t("source_forecast", lang)].copy()
    oos_df = all_df[all_df[t("cr_col_source", lang)] == t("source_oos", lang)].copy()

    skip_cols = {
        "name": t("cr_col_product", lang),
        "sku": t("cr_col_sku", lang),
        "stock": t("cr_col_stock_skip", lang),
        "days_left": t("cr_col_days_left", lang),
        "daily_rate": t("cr_col_daily_rate", lang),
    }
    skipped_display = skip.rename(columns=skip_cols)[list(skip_cols.values())].copy()

    total_skus = len(all_df)
    total_units = int(all_df[t("cr_col_reorder", lang)].sum()) if not all_df.empty else 0
    summary = pd.DataFrame(
        {
            t("cr_summary_metric", lang): [
                t("cr_summary_catalog_rows", lang),
                t("cr_summary_skip_rows", lang),
                t("cr_summary_must_rows", lang),
                t("cr_summary_oos_rows", lang),
                t("cr_summary_total_skus", lang),
                t("cr_summary_total_units", lang),
            ],
            t("cr_summary_value", lang): [
                len(catalog),
                len(skip),
                len(must_df),
                len(oos_df),
                total_skus,
                total_units,
            ],
        }
    )

    return CatalogReorderResult(
        must_order=must_df.reset_index(drop=True),
        out_of_stock=oos_df.reset_index(drop=True),
        all_items=all_df.reset_index(drop=True),
        skipped=skipped_display.reset_index(drop=True),
        summary=summary,
    )


def catalog_reorder_excel_bytes(result: CatalogReorderResult, lang: str) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result.must_order.to_excel(
            writer, index=False, sheet_name=t("cr_sheet_must", lang)[:31],
        )
        result.out_of_stock.to_excel(
            writer, index=False, sheet_name=t("cr_sheet_oos", lang)[:31],
        )
        result.all_items.to_excel(
            writer, index=False, sheet_name=t("cr_sheet_all", lang)[:31],
        )
        result.skipped.to_excel(
            writer, index=False, sheet_name=t("cr_sheet_skip", lang)[:31],
        )
        result.summary.to_excel(
            writer, index=False, sheet_name=t("cr_sheet_summary", lang)[:31],
        )
    return buffer.getvalue()


def build_from_uploads(
    catalog_bytes: bytes,
    catalog_name: str,
    skip_bytes: bytes,
    skip_name: str,
    *,
    forecast_df: pd.DataFrame | None = None,
    lang: str = "en",
    oos_default_qty: int = 20,
    include_forecast_must_order: bool = True,
) -> CatalogReorderResult:
    catalog = parse_square_catalog(catalog_bytes, catalog_name)
    skip = parse_skip_file(skip_bytes, skip_name)
    return build_catalog_reorder(
        catalog,
        skip,
        forecast_df=forecast_df,
        lang=lang,
        oos_default_qty=oos_default_qty,
        include_forecast_must_order=include_forecast_must_order,
    )
