"""Square inventory reorder forecast — GUI (read-only)."""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from config import Settings
from src.i18n import (
    DEFAULT_LANG,
    LANG_EN,
    LANG_ZH,
    PRIORITY_COLORS,
    PRIORITY_ORDER_INTERNAL,
    forecast_col_display,
    localize_dataframe,
    priority_col,
    priority_display_order,
    priority_from_display,
    priority_label,
    product_col,
    reorder_qty_col,
    t,
)
from src.order_export import build_must_order_df, build_must_order_excel_bytes, save_must_order_excel
from src.pipeline import run_forecast
from src.reporter import save_report


def _get_lang() -> str:
    return st.session_state.get("language", DEFAULT_LANG)


def _priority_style(val: str) -> str:
    lang = _get_lang()
    for internal in PRIORITY_ORDER_INTERNAL:
        if priority_label(internal, lang) == val:
            color = PRIORITY_COLORS.get(internal, "#95a5a6")
            return f"background-color: {color}; color: white; font-weight: 600;"
    return ""


def _to_excel_bytes(df: pd.DataFrame, lang: str) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=t("excel_sheet", lang))
    return buffer.getvalue()


def _init_form_state() -> None:
    if "form_initialized" in st.session_state:
        return
    defaults = Settings.env_defaults()
    st.session_state.language = DEFAULT_LANG
    st.session_state.access_token = defaults["access_token"]
    st.session_state.environment = (
        defaults["environment"] if defaults["environment"] in ("production", "sandbox") else "production"
    )
    st.session_state.location_id = defaults["location_id"]
    st.session_state.history_days = defaults["history_days"]
    st.session_state.forecast_days = defaults["forecast_days"]
    st.session_state.safety_stock_z = defaults["safety_stock_z"]
    st.session_state.exclude_not_for_sale = True
    st.session_state.form_initialized = True


def _translate_config_error(exc: ValueError, lang: str) -> str:
    code = str(exc)
    if code == "ERR_MISSING_TOKEN":
        return t("err_missing_token", lang)
    if code == "ERR_INVALID_ENV":
        return t("err_invalid_env", lang)
    return code


def render_footer(lang: str) -> None:
    st.markdown("---")
    st.markdown(
        f'<p style="text-align:center;color:#888;font-size:0.85rem;margin-top:1rem;">'
        f'{t("copyright", lang)}</p>',
        unsafe_allow_html=True,
    )


def render_page_header() -> None:
    """页面顶部：左侧标题，右上角语言切换。"""
    lang = _get_lang()
    title_col, lang_col = st.columns([7, 1], vertical_alignment="top")

    with lang_col:
        st.segmented_control(
            t("lang_label", lang),
            options=[LANG_EN, LANG_ZH],
            format_func=lambda code: "EN" if code == LANG_EN else "中文",
            key="language",
            label_visibility="collapsed",
        )

    lang = _get_lang()
    with title_col:
        st.title(t("app_title", lang))
        st.markdown(t("app_subtitle", lang))


def render_sidebar() -> dict:
    _init_form_state()
    lang = _get_lang()

    st.sidebar.title(t("settings", lang))
    st.sidebar.subheader(t("api_credentials", lang))
    st.sidebar.caption(t("api_hint", lang))

    st.sidebar.text_input(
        t("access_token", lang),
        type="password",
        placeholder=t("token_placeholder", lang),
        help=t("token_help", lang),
        key="access_token",
    )
    st.sidebar.caption(t("token_privacy", lang))
    st.sidebar.selectbox(
        t("environment", lang),
        options=["production", "sandbox"],
        key="environment",
    )
    st.sidebar.text_input(
        t("location_id", lang),
        placeholder=t("location_placeholder", lang),
        key="location_id",
    )

    st.sidebar.divider()
    st.sidebar.subheader(t("forecast_params", lang))
    st.sidebar.caption(t("readonly_notice", lang))

    st.sidebar.slider(t("history_days", lang), 30, 180, key="history_days", step=15)
    st.sidebar.slider(t("forecast_days", lang), 7, 90, key="forecast_days", step=1)
    st.sidebar.slider(
        t("safety_stock_z", lang),
        0.0,
        3.0,
        step=0.05,
        help=t("safety_stock_help", lang),
        key="safety_stock_z",
    )
    st.sidebar.checkbox(
        t("exclude_not_for_sale", lang),
        help=t("exclude_not_for_sale_help", lang),
        key="exclude_not_for_sale",
    )

    run_clicked = st.sidebar.button(
        t("run_forecast", lang), type="primary", use_container_width=True,
    )

    settings = None
    if run_clicked:
        try:
            settings = Settings.from_values(
                st.session_state.access_token,
                environment=st.session_state.environment,
                location_id=st.session_state.location_id or None,
                history_days=st.session_state.history_days,
                forecast_days=st.session_state.forecast_days,
                safety_stock_z=st.session_state.safety_stock_z,
            )
        except ValueError as exc:
            st.sidebar.error(_translate_config_error(exc, lang))

    return {
        "lang": lang,
        "settings": settings,
        "history_days": st.session_state.history_days,
        "forecast_days": st.session_state.forecast_days,
        "safety_stock_z": st.session_state.safety_stock_z,
        "exclude_not_for_sale": st.session_state.exclude_not_for_sale,
        "run_clicked": run_clicked and settings is not None,
    }


def render_must_order_panel(df: pd.DataFrame, lang: str) -> None:
    """预测完成后展示必须下单清单，并提供 Excel 下载。"""
    order_df = build_must_order_df(df, lang)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with st.container(border=True):
        st.subheader(t("must_order_title", lang))
        st.markdown(t("must_order_desc", lang))

        if order_df.empty:
            st.info(t("must_order_empty", lang))
            return

        st.markdown(t("must_order_count", lang, count=len(order_df)))
        st.dataframe(order_df, use_container_width=True, height=min(56 + len(order_df) * 35, 420))

        excel_bytes = build_must_order_excel_bytes(df, lang)
        st.download_button(
            t("must_order_download", lang),
            data=excel_bytes,
            file_name=t("mo_filename", lang, ts=timestamp),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
            key="must_order_download_btn",
        )

        saved_path = st.session_state.get("must_order_saved_path")
        if saved_path:
            st.caption(t("must_order_saved", lang, path=saved_path))


def render_metrics(df: pd.DataFrame, forecast_days: int, meta: dict, lang: str) -> None:
    reorder_col = "建议进货量"
    priority_internal_col = "优先级"
    need = df[df[reorder_col] > 0] if not df.empty else df
    urgent = (
        need[need[priority_internal_col].isin(["紧急", "高"])]
        if not need.empty
        else need
    )
    total_reorder = int(need[reorder_col].sum()) if not need.empty else 0
    excluded = meta.get("excluded_not_for_sale", 0)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(t("metric_total_products", lang), len(df))
    c2.metric(t("metric_need_reorder", lang), len(need))
    c3.metric(t("metric_urgent_high", lang), len(urgent))
    c4.metric(t("metric_total_qty", lang), f"{total_reorder:,}")
    c5.metric(t("metric_horizon", lang), t("metric_days", lang, n=forecast_days))
    if excluded:
        c6.metric(t("metric_excluded", lang), excluded)

    st.caption(
        t(
            "meta_caption",
            lang,
            loc=meta["location_id"],
            history=meta["history_days"],
            sales=meta["sales_records"],
            inv=meta["inventory_count"],
        )
    )


def render_charts(
    df: pd.DataFrame,
    forecast_days: int,
    history_days: int,
    lang: str,
) -> None:
    display_df = localize_dataframe(df, lang, history_days, forecast_days)
    reorder_col = reorder_qty_col(lang)
    priority_col_name = priority_col(lang)
    product_col_name = product_col(lang)
    forecast_col_name = forecast_col_display(lang, forecast_days)

    need = display_df[display_df[reorder_col] > 0].copy()
    if need.empty:
        st.info(t("chart_no_reorder", lang))
        return

    col1, col2 = st.columns(2)
    display_order = priority_display_order(lang)
    color_map = {
        priority_label(p, lang): PRIORITY_COLORS[p] for p in PRIORITY_ORDER_INTERNAL
    }

    with col1:
        priority_counts = (
            display_df[priority_col_name]
            .value_counts()
            .reindex(display_order, fill_value=0)
            .reset_index()
        )
        priority_counts.columns = [t("chart_priority", lang), t("chart_count", lang)]
        fig = px.pie(
            priority_counts,
            values=t("chart_count", lang),
            names=t("chart_priority", lang),
            title=t("chart_priority_dist", lang),
            color=t("chart_priority", lang),
            color_discrete_map=color_map,
            category_orders={t("chart_priority", lang): display_order},
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top = need.nlargest(15, reorder_col)
        fig = px.bar(
            top,
            x=reorder_col,
            y=product_col_name,
            orientation="h",
            title=t("chart_top15", lang),
            color=priority_col_name,
            color_discrete_map=color_map,
            category_orders={priority_col_name: display_order},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=480)
        st.plotly_chart(fig, use_container_width=True)

    scatter = need.nlargest(200, reorder_col)
    stock_col = t("col_stock", lang)
    fig = px.scatter(
        scatter,
        x=stock_col,
        y=forecast_col_name,
        size=reorder_col,
        color=priority_col_name,
        hover_name=product_col_name,
        title=t("chart_scatter", lang),
        color_discrete_map=color_map,
        category_orders={priority_col_name: display_order},
    )
    st.plotly_chart(fig, use_container_width=True)


def render_table(df: pd.DataFrame, forecast_days: int, history_days: int, lang: str) -> pd.DataFrame:
    st.subheader(t("list_title", lang))

    display_order = priority_display_order(lang)
    default_filter = display_order[:3]

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input(
            t("search_label", lang),
            placeholder=t("search_placeholder", lang),
        )
    with col2:
        priority_filter = st.multiselect(
            t("priority_filter", lang),
            display_order,
            default=default_filter,
        )
    with col3:
        only_reorder = st.checkbox(t("only_reorder", lang), value=True)

    internal_df = df.copy()
    reorder_col = "建议进货量"
    priority_internal_col = "优先级"
    product_internal_col = "商品名称"

    filtered = internal_df
    if only_reorder:
        filtered = filtered[filtered[reorder_col] > 0]
    if priority_filter:
        internal_priorities = [
            p for p in (priority_from_display(d, lang) for d in priority_filter) if p
        ]
        filtered = filtered[filtered[priority_internal_col].isin(internal_priorities)]
    if search.strip():
        filtered = filtered[
            filtered[product_internal_col].str.contains(search.strip(), case=False, na=False)
        ]

    display_df = localize_dataframe(filtered, lang, history_days, forecast_days)
    priority_display_col = priority_col(lang)

    styled = display_df.style.map(_priority_style, subset=[priority_display_col])
    st.dataframe(styled, use_container_width=True, height=420)
    st.caption(t("showing_count", lang, shown=len(filtered), total=len(df)))

    return display_df


def main() -> None:
    st.set_page_config(
        page_title=t("page_title", DEFAULT_LANG),
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_form_state()

    render_page_header()
    opts = render_sidebar()
    lang = opts["lang"]

    if "result" not in st.session_state:
        st.session_state.result = None

    if opts["run_clicked"]:
        progress = st.progress(0, text=t("preparing", lang))
        status = st.empty()

        def on_progress(msg: str, fraction: float | None = None) -> None:
            status.info(msg)
            if fraction is not None:
                progress.progress(fraction, text=msg)

        try:
            with st.spinner(t("fetching", lang)):
                result = run_forecast(
                    settings=opts["settings"],
                    history_days=opts["history_days"],
                    forecast_days=opts["forecast_days"],
                    safety_stock_z=opts["safety_stock_z"],
                    on_progress=on_progress,
                    lang=lang,
                    exclude_not_for_sale=opts["exclude_not_for_sale"],
                )
            st.session_state.result = result
            st.session_state.must_order_saved_path = save_must_order_excel(
                result.df, lang, "output",
            )
            progress.progress(1.0, text=t("done", lang))
            status.success(t("forecast_complete", lang))
        except Exception as exc:
            progress.empty()
            status.error(t("forecast_failed", lang, error=exc))
            render_footer(lang)
            st.stop()

    result = st.session_state.result
    if result is None:
        st.info(t("empty_hint", lang))
        st.markdown(
            f"""
            {t("steps_title", lang)}
            {t("step_1", lang)}
            {t("step_2", lang)}
            {t("step_3", lang)}

            {t("features_title", lang)}
            {t("feature_1", lang)}
            {t("feature_2", lang)}
            {t("feature_3", lang)}
            """
        )
        render_footer(lang)
        return

    df = result.df
    meta = {
        "location_id": result.location_id,
        "history_days": result.history_days,
        "sales_records": result.sales_records,
        "inventory_count": result.inventory_count,
        "excluded_not_for_sale": result.excluded_not_for_sale,
    }

    render_metrics(df, result.forecast_days, meta, lang)
    st.divider()
    render_must_order_panel(df, lang)
    st.divider()

    tab1, tab2 = st.tabs([t("tab_charts", lang), t("tab_list", lang)])

    with tab1:
        render_charts(df, result.forecast_days, result.history_days, lang)

    with tab2:
        filtered = render_table(df, result.forecast_days, result.history_days, lang)

        st.divider()
        dl1, dl2, dl3 = st.columns(3)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_df = localize_dataframe(
            df, lang, result.history_days, result.forecast_days,
        )

        with dl1:
            st.download_button(
                t("download_excel", lang),
                data=_to_excel_bytes(export_df, lang),
                file_name=t("excel_filename", lang, ts=timestamp),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                t("download_csv", lang),
                data=filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name=t("csv_filename", lang, ts=timestamp),
                mime="text/csv",
                use_container_width=True,
            )
        with dl3:
            if st.button(t("save_output", lang), use_container_width=True):
                path = save_report(df, "output")
                st.success(t("saved_to", lang, path=path))

    render_footer(lang)


if __name__ == "__main__":
    main()
