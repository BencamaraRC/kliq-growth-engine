"""Store Preview — visual mockup of what a generated KLIQ webstore looks like.

Renders a full-page preview using the prospect's AI-generated content:
bio, blog posts, pricing tiers, and brand colors.
"""

import json

import streamlit as st

st.set_page_config(page_title="Store Preview | KLIQ Growth Engine", layout="wide")

st.title("Store Preview")
st.markdown("Preview what a generated KLIQ webstore looks like for a discovered coach.")

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
    selected = st.selectbox("Select a coach to preview their store", list(options.keys()))
    prospect_id = options[selected]

    # --- Load all data ---
    with engine.connect() as conn:
        prospect = dict(
            conn.execute(
                text("SELECT * FROM prospects WHERE id = :id"), {"id": prospect_id}
            ).fetchone()._mapping
        )

        generated = conn.execute(
            text("SELECT * FROM generated_content WHERE prospect_id = :id"),
            {"id": prospect_id},
        ).fetchall()

    # Parse generated content
    bio_data = {}
    seo_data = {}
    color_data = {}
    products = []
    blogs = []

    for row in generated:
        r = dict(row._mapping)
        body = r.get("body", "{}")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}

        if r["content_type"] == "bio":
            bio_data = parsed
        elif r["content_type"] == "seo":
            seo_data = parsed
        elif r["content_type"] == "colors":
            color_data = parsed
        elif r["content_type"] == "product":
            parsed["title"] = r.get("title", "")
            products.append(parsed)
        elif r["content_type"] == "blog":
            parsed["title"] = r.get("title", "")
            blogs.append(parsed)

    # --- Colors ---
    primary = color_data.get("primary", "#1E81FF")
    secondary = color_data.get("secondary", "#F5F5F5")
    accent = color_data.get("accent", primary)
    bg = color_data.get("background", "#FFFFFF")
    text_color = color_data.get("text", "#1A1A1A")

    # --- Render Store Preview ---
    st.markdown("---")

    # Header / Hero
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {primary}, {accent});
            padding: 60px 40px;
            border-radius: 16px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        ">
            <h1 style="color: white; font-size: 2.8em; margin-bottom: 10px;">
                {prospect['name']}
            </h1>
            <p style="font-size: 1.4em; opacity: 0.95; margin-bottom: 20px;">
                {bio_data.get('tagline', '')}
            </p>
            <p style="font-size: 1.1em; opacity: 0.85; max-width: 700px; margin: 0 auto;">
                {bio_data.get('short_bio', prospect.get('bio', ''))}
            </p>
            <div style="margin-top: 25px;">
                <span style="
                    background: white;
                    color: {primary};
                    padding: 12px 32px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 1.1em;
                    cursor: pointer;
                ">Get Started</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # About Section
    if bio_data.get("long_bio"):
        st.markdown(
            f"""
            <div style="
                background: {bg};
                padding: 40px;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                margin-bottom: 30px;
            ">
                <h2 style="color: {primary}; margin-bottom: 15px;">About</h2>
                <p style="color: {text_color}; line-height: 1.8; font-size: 1.05em; white-space: pre-line;">
                    {bio_data['long_bio']}
                </p>
                {"<div style='margin-top:20px;'>" + " ".join(f'<span style="background:{primary}15;color:{primary};padding:6px 14px;border-radius:20px;margin:4px;display:inline-block;font-size:0.9em;">{s}</span>' for s in bio_data.get('specialties', [])) + "</div>" if bio_data.get('specialties') else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Pricing Section
    if products:
        st.markdown(
            f'<h2 style="color: {primary}; text-align: center; margin: 30px 0 20px;">Pricing</h2>',
            unsafe_allow_html=True,
        )

        cols = st.columns(len(products))
        for i, product in enumerate(products):
            price_cents = product.get("price_cents", 0)
            currency_sym = "£" if product.get("currency", "GBP") == "GBP" else "$"
            price_display = f"{currency_sym}{price_cents / 100:.0f}"
            interval = product.get("interval")
            price_suffix = f"/{interval}" if interval else " one-time"
            is_recommended = product.get("recommended", False)

            border_style = f"3px solid {primary}" if is_recommended else "1px solid #E0E0E0"
            badge = f'<div style="background:{primary};color:white;padding:4px 12px;border-radius:12px;font-size:0.8em;display:inline-block;margin-bottom:10px;">RECOMMENDED</div>' if is_recommended else ""

            features_html = "".join(
                f'<div style="padding:6px 0;border-bottom:1px solid #F0F0F0;font-size:0.95em;">✓ {f}</div>'
                for f in product.get("features", [])
            )

            with cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        border: {border_style};
                        border-radius: 12px;
                        padding: 30px 20px;
                        text-align: center;
                        background: white;
                        height: 100%;
                    ">
                        {badge}
                        <h3 style="color: {text_color}; margin-bottom: 5px;">{product.get('title', '')}</h3>
                        <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">
                            {product.get('description', '')}
                        </p>
                        <div style="font-size: 2.2em; font-weight: bold; color: {primary}; margin: 15px 0;">
                            {price_display}<span style="font-size: 0.4em; color: #999;">{price_suffix}</span>
                        </div>
                        <div style="text-align: left; margin: 20px 0;">
                            {features_html}
                        </div>
                        <div style="
                            background: {primary};
                            color: white;
                            padding: 12px 24px;
                            border-radius: 8px;
                            font-weight: bold;
                            cursor: pointer;
                            margin-top: 15px;
                        ">Choose Plan</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Blog Section
    if blogs:
        st.markdown(
            f'<h2 style="color: {primary}; text-align: center; margin: 40px 0 20px;">Latest Articles</h2>',
            unsafe_allow_html=True,
        )

        for blog in blogs:
            with st.expander(f"📝 {blog.get('title', 'Untitled')}", expanded=False):
                if blog.get("excerpt"):
                    st.markdown(f"*{blog['excerpt']}*")
                if blog.get("body_html"):
                    st.markdown(blog["body_html"], unsafe_allow_html=True)
                if blog.get("tags"):
                    tag_html = " ".join(
                        f'<span style="background:#F0F0F0;padding:4px 10px;border-radius:12px;margin:2px;font-size:0.85em;">{t}</span>'
                        for t in blog["tags"]
                    )
                    st.markdown(tag_html, unsafe_allow_html=True)

    # Footer
    st.markdown(
        f"""
        <div style="
            background: {text_color};
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-top: 40px;
        ">
            <p style="font-size: 1.1em; margin-bottom: 10px;">Ready to transform your fitness?</p>
            <span style="
                background: {primary};
                color: white;
                padding: 12px 32px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 1.05em;
                cursor: pointer;
            ">Claim Your Store</span>
            <p style="font-size: 0.85em; opacity: 0.6; margin-top: 15px;">
                Powered by KLIQ — joinkliq.io
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Debug Info (collapsed) ---
    with st.expander("Debug: Raw Generated Data"):
        st.json({"bio": bio_data, "seo": seo_data, "colors": color_data, "products": products, "blogs": blogs})

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
