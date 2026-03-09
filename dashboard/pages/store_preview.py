"""Store Preview — visual mockup of what a generated KLIQ webstore looks like.

Renders a full-page preview matching the actual KLIQ public webstore design
as seen on live stores like Lift Your Vibe. Uses st.components.v1.html() for
reliable HTML rendering.
"""

import importlib.util
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Import the renderer directly by file path to avoid conflict with dashboard/app.py
_renderer_path = Path(__file__).resolve().parent.parent.parent / "app" / "preview" / "renderer.py"
_spec = importlib.util.spec_from_file_location("preview_renderer", _renderer_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
render_store_preview = _mod.render_store_preview

st.set_page_config(page_title="Store Preview | KLIQ Growth Engine", layout="wide")

from theme import inject_kliq_theme, sidebar_nav  # noqa: E402

inject_kliq_theme()
sidebar_nav()

st.markdown("#### Store Preview")

try:
    from data import engine
    from sqlalchemy import text

    # --- Select a prospect ---
    with engine.connect() as conn:
        prospects = conn.execute(
            text("""
                SELECT p.id, p.name, p.primary_platform, p.status
                FROM prospects p
                WHERE EXISTS (SELECT 1 FROM generated_content gc WHERE gc.prospect_id = p.id)
                ORDER BY p.name
            """)
        ).fetchall()

    if not prospects:
        st.info("No prospects with generated content yet. Run the AI pipeline first.")
        st.stop()

    options = {f"{p[1]} ({p[2]}) — {p[3]}": p[0] for p in prospects}
    option_keys = list(options.keys())
    default_idx = 0
    query_id = st.query_params.get("id")
    if query_id:
        query_id_int = int(query_id)
        for i, key in enumerate(option_keys):
            if options[key] == query_id_int:
                default_idx = i
                break
    else:
        for i, key in enumerate(option_keys):
            if "KLIQ" in key:
                default_idx = i
                break
    selected = st.selectbox("Select a coach to preview their store", option_keys, index=default_idx)
    prospect_id = options[selected]

    # --- Load all data ---
    with engine.connect() as conn:
        prospect = dict(
            conn.execute(text("SELECT * FROM prospects WHERE id = :id"), {"id": prospect_id})
            .fetchone()
            ._mapping
        )

        generated = conn.execute(
            text("SELECT * FROM generated_content WHERE prospect_id = :id"),
            {"id": prospect_id},
        ).fetchall()

    # Convert rows to list of dicts for the renderer
    generated_content = []
    for row in generated:
        r = dict(row._mapping)
        generated_content.append(
            {
                "content_type": r.get("content_type", ""),
                "title": r.get("title", ""),
                "body": r.get("body", "{}"),
            }
        )

    # Render the store preview HTML using the shared renderer
    full_html = render_store_preview(prospect=prospect, generated_content=generated_content)

    # Render as a full-screen iframe component
    components.html(full_html, height=3200, scrolling=True)

    # --- Debug Info ---
    # Parse generated content for debug display
    bio_data = {}
    seo_data = {}
    color_data = {}
    products = []
    blogs = []
    for r in generated_content:
        body = r.get("body", "{}")
        try:
            parsed = json.loads(body) if body else {}
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        ct = r.get("content_type", "")
        if ct == "bio":
            bio_data = parsed
        elif ct == "seo":
            seo_data = parsed
        elif ct == "colors":
            color_data = parsed
        elif ct == "product":
            parsed["title"] = r.get("title", "")
            products.append(parsed)
        elif ct == "blog":
            parsed["title"] = r.get("title", "")
            blogs.append(parsed)

    with st.expander("Debug: Raw Generated Data"):
        st.json(
            {
                "bio": bio_data,
                "seo": seo_data,
                "colors": color_data,
                "products": products,
                "blogs": blogs,
            }
        )

except Exception as e:
    st.error(f"Error: {e}")
    import traceback

    st.code(traceback.format_exc())
