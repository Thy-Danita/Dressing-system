import json
import random
import re
import uuid
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st


DATA_FILE = Path(__file__).resolve().with_name("wardrobe.json")
IMAGE_DIR = Path(__file__).resolve().with_name("wardrobe_images")
CATEGORIES = ("Top", "Bottom", "Shoes", "Outerwear", "Accessory")
MAIN_CATEGORIES = ("Top", "Bottom", "Shoes", "Outerwear")
REQUIRED_ITEM_FIELDS = ("id", "name", "category", "color", "style")
CATEGORY_ICONS = {
    "Top": "👕",
    "Bottom": "👖",
    "Shoes": "👟",
    "Outerwear": "🧥",
    "Accessory": "👜",
}
CARD_THEMES = ("lavender", "pink", "sky", "butter", "sage")
BADGE_THEMES = {
    "Top": "pink",
    "Bottom": "lavender",
    "Shoes": "sky",
    "Outerwear": "sage",
    "Accessory": "butter",
}
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
NAVIGATION = ("My Wardrobe", "AI Outfit Generator")


def load_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not DATA_FILE.exists():
        return [], []

    with DATA_FILE.open("r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    if isinstance(data, list):
        items, outfits = data, []
    elif isinstance(data, dict):
        items, outfits = data.get("items", []), data.get("outfits", [])
    else:
        raise ValueError("Wardrobe data must be a JSON list or object.")

    if not isinstance(items, list) or not isinstance(outfits, list):
        raise ValueError("Wardrobe items and saved outfits must be JSON lists.")

    for index, item in enumerate(items):
        if not isinstance(item, dict) or any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in REQUIRED_ITEM_FIELDS
        ):
            raise ValueError(
                f"Wardrobe item {index + 1} must include non-empty "
                "id, name, category, color, and style values."
            )
        if item["category"] not in CATEGORIES:
            raise ValueError(
                f"Wardrobe item {index + 1} has an unknown category."
            )
        if "image" in item and not isinstance(item["image"], str):
            raise ValueError(f"Wardrobe item {index + 1} has an invalid image path.")

    for index, outfit in enumerate(outfits):
        if (
            not isinstance(outfit, dict)
            or not isinstance(outfit.get("id"), str)
            or not isinstance(outfit.get("style"), str)
            or not isinstance(outfit.get("item_ids"), list)
            or any(not isinstance(item_id, str) for item_id in outfit["item_ids"])
        ):
            raise ValueError(
                f"Saved outfit {index + 1} must include an id, style, "
                "and list of item IDs."
            )

    return items, outfits


def save_data(
    items: list[dict[str, Any]], outfits: list[dict[str, Any]]
) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as data_file:
        json.dump(
            {"items": items, "outfits": outfits},
            data_file,
            indent=2,
            ensure_ascii=False,
        )
        data_file.write("\n")


def save_uploaded_image(upload: Any, item_id: str) -> str | None:
    if upload is None:
        return None

    extension = IMAGE_EXTENSIONS.get(upload.type)
    if extension is None:
        raise ValueError("Choose a JPG, PNG, or WEBP image.")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{item_id}-{uuid.uuid4().hex[:8]}{extension}"
    (IMAGE_DIR / filename).write_bytes(upload.getvalue())
    return filename


def local_image(item: dict[str, Any]) -> Path | None:
    filename = item.get("image")
    if not isinstance(filename, str) or Path(filename).name != filename:
        return None
    image_path = IMAGE_DIR / filename
    return image_path if image_path.is_file() else None


def delete_image(item: dict[str, Any]) -> None:
    image_path = local_image(item)
    if image_path is not None:
        image_path.unlink(missing_ok=True)


def matching_outfit(
    items: list[dict[str, Any]],
    aesthetic: str,
    previous_item_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    query_terms = {
        term
        for term in re.findall(r"[a-z0-9]+", aesthetic.casefold())
        if term not in {"style", "aesthetic", "look", "wear"}
    }
    if not query_terms:
        return [], ["a style or aesthetic"]

    matching_items = [
        item
        for item in items
        if query_terms <= {
            term
            for term in re.findall(r"[a-z0-9]+", item["style"].casefold())
            if term not in {"style", "aesthetic", "look", "wear"}
        }
    ]
    if not matching_items:
        return [], ["clothing tagged with that style"]

    required = ("Top", "Bottom", "Shoes")
    missing = [
        category
        for category in required
        if not any(item["category"] == category for item in matching_items)
    ]
    if missing:
        return [], missing

    previous_item_ids = previous_item_ids or set()
    outfit = []
    for category in required:
        options = [
            item for item in matching_items if item["category"] == category
        ]
        alternatives = [
            item for item in options if item["id"] not in previous_item_ids
        ]
        outfit.append(random.choice(alternatives or options))
    outerwear = [
        item for item in matching_items if item["category"] == "Outerwear"
    ]
    if outerwear and random.choice((True, False)):
        alternatives = [
            item for item in outerwear if item["id"] not in previous_item_ids
        ]
        outfit.append(random.choice(alternatives or outerwear))
    return outfit, []


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --sage: #728675; --sage-dark: #536958; --ink: #292e2a;
            --lavender: #f2eaff; --pink: #ffeaf0; --sky: #e7f5ff;
            --butter: #fff6d9; --mint: #e9f3e8;
        }
        .stApp {
            background:
                radial-gradient(ellipse at 94% 5%, #f1e5ff 0, transparent 25rem),
                radial-gradient(ellipse at 5% 46%, #e2f4ec 0, transparent 27rem),
                radial-gradient(ellipse at 82% 88%, #e6f4ff 0, transparent 24rem),
                radial-gradient(circle, #8c77a214 1px, transparent 1.35px),
                url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 170 170' fill='none'%3E%3Cpath d='M32 13c3 10 6 13 16 16-10 3-13 6-16 16-3-10-6-13-16-16 10-3 13-6 16-16Z' stroke='%23927ab4' stroke-opacity='.14' stroke-width='1.6' stroke-linejoin='round'/%3E%3Cpath d='m124 62 3.5 10.5L138 76l-10.5 3.5L124 90l-3.5-10.5L110 76l10.5-3.5L124 62Z' stroke='%23ba8299' stroke-opacity='.12' stroke-width='1.5' stroke-linejoin='round'/%3E%3Cpath d='m61 122 2.5 7.5L71 132l-7.5 2.5L61 142l-2.5-7.5L51 132l7.5-2.5L61 122Z' stroke='%237d9c83' stroke-opacity='.12' stroke-width='1.4' stroke-linejoin='round'/%3E%3C/svg%3E"),
                #faf9f8;
            background-size: auto, auto, auto, 34px 34px, 220px 220px, auto;
            background-attachment: fixed;
            color: var(--ink);
        }
        html, body, [class*="css"] { font-family: 'Avenir Next', 'Segoe UI', sans-serif; }
        .block-container { max-width: 1320px; padding: 2.1rem 2.5rem 4rem; }
        h1, h2, h3 {
            color: var(--ink); letter-spacing: -0.035em; font-weight: 700;
        }
        h1, h2 {
            font-family: 'Iowan Old Style', 'Palatino Linotype', Georgia, serif !important;
            font-weight: 500 !important;
        }
        h1 { font-size: clamp(2rem, 4vw, 3.2rem) !important; }
        h2 { font-size: 2rem !important; }
        [data-testid="stSidebar"] {
            background: linear-gradient(175deg, #e4e8cf 0%, #d3dcc0 54%, #c4d2b2 100%);
            border-right: 1px solid #bdc9aa;
        }
        [data-testid="stSidebar"] * { color: #292e2a !important; }
        [data-testid="stSidebar"] .block-container { padding: 1.7rem 1rem; }
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            background: #f8f9f0b8;
            border: 1px solid #c1cbaa;
            box-shadow: 0 4px 12px #34422512;
            transition: background-color .18s ease, transform .18s ease;
        }
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
            background: #eef0d6;
            border-color: #aebc8d;
            transform: translateX(2px);
        }
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
            background: linear-gradient(120deg, #bac89b, #d8dfb8);
            border: 1px solid #a7b586;
            box-shadow: 0 5px 14px #46572c24;
        }
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(120deg, #aebd8b, #cbd5a1);
            border-color: #91a06e;
        }
        [data-testid="stMetric"] {
            background: #fff; border: 1px solid #eeece5; border-radius: 18px;
            padding: 1.1rem 1.25rem; box-shadow: 0 5px 20px #37392d08;
        }
        [data-testid="stMetricLabel"] { color: #777c74; font-size: .88rem; }
        [data-testid="stMetricValue"] { color: var(--ink); font-weight: 600; }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 12px; min-height: 2.8rem; font-weight: 600;
            border-color: #dcded5; transition: background-color .15s ease;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: var(--sage); border-color: var(--sage); color: white;
        }
        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--sage-dark); border-color: var(--sage-dark); color: white;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #fffdfd; border-color: #e8e2e9 !important;
            border-radius: 20px; box-shadow: 0 8px 24px #4b37500d;
        }
        [class*="st-key-wardrobe-card-"],
        [class*="st-key-outfit-card-"] {
            transition: transform .22s ease, filter .22s ease;
            overflow: hidden;
        }
        [class*="st-key-wardrobe-card-"]:hover,
        [class*="st-key-outfit-card-"]:hover {
            transform: translateY(-5px);
            filter: drop-shadow(0 14px 18px #4335541c);
        }
        @media (prefers-reduced-motion: reduce) {
            [class*="st-key-wardrobe-card-"],
            [class*="st-key-outfit-card-"] { transition: none; }
            [class*="st-key-wardrobe-card-"]:hover,
            [class*="st-key-outfit-card-"]:hover { transform: none; }
        }
        [class*="st-key-wardrobe-card-lavender"],
        [class*="st-key-outfit-card-lavender"] {
            background: radial-gradient(circle at 100% 0%, #dccbffb0 0, transparent 34%),
                linear-gradient(145deg, #f7f2ff, #eee5ff);
            border: 1px solid #dfd0f6; border-radius: 20px;
            padding: .8rem; box-shadow: 0 9px 24px #7356a315;
        }
        [class*="st-key-wardrobe-card-pink"],
        [class*="st-key-outfit-card-pink"] {
            background: radial-gradient(circle at 100% 0%, #ffc7d5aa 0, transparent 34%),
                linear-gradient(145deg, #fff4f6, #ffe8ee);
            border: 1px solid #f4d0dc; border-radius: 20px;
            padding: .8rem; box-shadow: 0 9px 24px #a34f7012;
        }
        [class*="st-key-wardrobe-card-sky"],
        [class*="st-key-outfit-card-sky"] {
            background: radial-gradient(circle at 100% 0%, #bde6ffb0 0, transparent 34%),
                linear-gradient(145deg, #f1faff, #e3f3ff);
            border: 1px solid #c9e4f5; border-radius: 20px;
            padding: .8rem; box-shadow: 0 9px 24px #39719a12;
        }
        [class*="st-key-wardrobe-card-butter"],
        [class*="st-key-outfit-card-butter"] {
            background: radial-gradient(circle at 100% 0%, #ffe59bb0 0, transparent 34%),
                linear-gradient(145deg, #fffbed, #fff4d5);
            border: 1px solid #f2e2ad; border-radius: 20px;
            padding: .8rem; box-shadow: 0 9px 24px #8b6a1912;
        }
        [class*="st-key-wardrobe-card-sage"],
        [class*="st-key-outfit-card-sage"] {
            background: radial-gradient(circle at 100% 0%, #c4dfc2b0 0, transparent 34%),
                linear-gradient(145deg, #f5faf3, #e7f1e5);
            border: 1px solid #d0e2cd; border-radius: 20px;
            padding: .8rem; box-shadow: 0 9px 24px #4d755312;
        }
        [class*="st-key-wardrobe-card-"] [data-testid="stVerticalBlockBorderWrapper"],
        [class*="st-key-outfit-card-"] [data-testid="stVerticalBlockBorderWrapper"],
        [class*="st-key-home-wardrobe-card"] [data-testid="stVerticalBlockBorderWrapper"],
        [class*="st-key-home-generator-card"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border-color: transparent !important;
            box-shadow: none !important;
        }
        [class*="st-key-home-wardrobe-card"] {
            background: radial-gradient(circle at 100% 0%, #c7b0ffb5 0, transparent 36%),
                linear-gradient(140deg, #f6f0ff, #e9e2ff);
            border: 1px solid #d9cbf3; border-radius: 22px;
            padding: 1.2rem; box-shadow: 0 12px 30px #7356a318;
        }
        [class*="st-key-home-generator-card"] {
            background: radial-gradient(circle at 100% 0%, #ff9fbdc9 0, transparent 40%),
                linear-gradient(140deg, #ffedf3, #ffd6e4);
            border: 1px solid #edb6ca; border-radius: 22px;
            padding: 1.2rem; box-shadow: 0 12px 30px #a34f7018;
        }
        [class*="st-key-generator-form-card"] {
            background:
                radial-gradient(circle at 100% 0%, #ffb8d1bd 0, transparent 38%),
                linear-gradient(135deg, #ffedf4, #f3eaff);
            border: 1px solid #efc6d6; border-radius: 22px;
            padding: 1rem; box-shadow: 0 12px 30px #a34f7014;
        }
        [class*="st-key-generator-form-card"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border-color: transparent !important;
            box-shadow: none !important;
        }
        [class*="st-key-home-wardrobe-card"],
        [class*="st-key-home-generator-card"] {
            transition: transform .22s ease, filter .22s ease;
        }
        [class*="st-key-home-wardrobe-card"]:hover,
        [class*="st-key-home-generator-card"]:hover {
            transform: translateY(-5px);
            filter: drop-shadow(0 14px 18px #4335541c);
        }
        .category-badge {
            display: inline-flex; align-items: center; gap: .35rem;
            padding: .28rem .68rem; border-radius: 999px; margin: .35rem 0 .2rem;
            font-size: .68rem; line-height: 1.3; font-weight: 700;
            letter-spacing: .08em; text-transform: uppercase; color: #343139;
        }
        .badge-pink { background: #ffd9e3; }
        .badge-lavender { background: #e6d7ff; }
        .badge-sky { background: #d2edff; }
        .badge-butter { background: #ffedb8; }
        .badge-sage { background: #d5e9d1; }
        .item-card-name { font-size: 1.05rem; font-weight: 700; margin: .2rem 0; }
        .outfit-card-image img {
            border-radius: 14px; border: 1px solid #ffffffb8;
            box-shadow: 0 6px 18px #43355414;
        }
        [data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div > div {
            border-radius: 11px;
        }
        .eyebrow {
            color: var(--sage-dark); font-size: .76rem; font-weight: 700;
            letter-spacing: .13em; text-transform: uppercase;
        }
        .soft-caption { color: #68626f; }
        @media (max-width: 700px) {
            .block-container { padding: 1.3rem 1rem 3rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_item_visual(item: dict[str, Any], height: int = 210) -> None:
    image_path = local_image(item)
    if image_path is not None:
        st.image(str(image_path), use_container_width=True)
    else:
        icon = CATEGORY_ICONS.get(item["category"], "✦")
        palettes = {
            "Top": ("#ffe6ed", "#ffb9cb"),
            "Bottom": ("#efe5ff", "#cbb3ff"),
            "Shoes": ("#e0f3ff", "#acdfff"),
            "Outerwear": ("#e6f1df", "#bad9b3"),
            "Accessory": ("#fff2cc", "#ffdf8a"),
        }
        start_color, end_color = palettes.get(
            item["category"], ("#f0e8f8", "#dfd1ee")
        )
        st.markdown(
            f"""
            <div style="height:{height}px;display:flex;align-items:center;
                justify-content:center;background:linear-gradient(145deg,{start_color},{end_color});
                border-radius:14px;color:#534764;font-size:4.4rem;
                box-shadow:inset 0 0 0 1px #ffffffa8;">
                {icon}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_category_badge(category: str) -> None:
    badge_theme = BADGE_THEMES.get(category, "butter")
    icon = CATEGORY_ICONS.get(category, "✦")
    st.markdown(
        f'<span class="category-badge badge-{badge_theme}">'
        f"{icon} {category}</span>",
        unsafe_allow_html=True,
    )


def render_item_card(
    item: dict[str, Any],
    items: list[dict[str, Any]],
    outfits: list[dict[str, Any]],
    theme: str,
) -> None:
    with st.container(
        border=True,
        key=f"wardrobe-card-{theme}-{item['id']}",
    ):
        render_item_visual(item, height=220)
        render_category_badge(item["category"])
        st.markdown(
            f'<div class="item-card-name">{escape(item["name"])}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"● {item['color']}  ·  {item['style']}"
        )
        edit_column, delete_column = st.columns(2)
        if edit_column.button("Edit", key=f"edit-{item['id']}"):
            edit_item_dialog(item, items, outfits)
        if delete_column.button("Delete", key=f"delete-{item['id']}"):
            delete_item_confirm(item, items, outfits)


@st.dialog("Add clothing")
def add_item_dialog(
    items: list[dict[str, Any]], outfits: list[dict[str, Any]]
) -> None:
    with st.form("add-item-form", clear_on_submit=True):
        name = st.text_input("Item name", placeholder="e.g. White cotton shirt")
        columns = st.columns(2)
        category = columns[0].selectbox("Category", MAIN_CATEGORIES)
        style = columns[1].text_input(
            "Style or aesthetic", placeholder="Casual, Korean style, ..."
        )
        color = st.text_input("Color", placeholder="e.g. Warm ivory")
        upload = st.file_uploader(
            "Photo",
            type=("jpg", "jpeg", "png", "webp"),
            help="Choose a JPG, PNG, or WEBP image (up to 5 MB).",
        )
        submitted = st.form_submit_button("Add to wardrobe", type="primary")

    if submitted:
        if not name.strip() or not color.strip() or not style.strip():
            st.error("Please enter an item name, color, and style.")
            return
        if upload is None:
            st.error("Please add a photo of this clothing item.")
            return
        if upload is not None and upload.size > 5 * 1024 * 1024:
            st.error("Please choose an image smaller than 5 MB.")
            return

        item_id = uuid.uuid4().hex
        image = None
        try:
            image = save_uploaded_image(upload, item_id)
            item: dict[str, Any] = {
                "id": item_id,
                "name": name.strip(),
                "category": category,
                "color": color.strip(),
                "style": style.strip(),
            }
            if image is not None:
                item["image"] = image
            save_data([*items, item], outfits)
        except (OSError, ValueError) as error:
            if image is not None:
                (IMAGE_DIR / image).unlink(missing_ok=True)
            st.error(f"Could not add this item: {error}")
            return
        st.session_state["flash_message"] = f"Added {item['name']} to your wardrobe."
        st.rerun()


@st.dialog("Edit clothing")
def edit_item_dialog(
    item: dict[str, Any],
    items: list[dict[str, Any]],
    outfits: list[dict[str, Any]],
) -> None:
    with st.form(f"edit-item-form-{item['id']}"):
        name = st.text_input("Item name", value=item["name"])
        columns = st.columns(2)
        categories = (
            CATEGORIES if item["category"] not in MAIN_CATEGORIES else MAIN_CATEGORIES
        )
        category = columns[0].selectbox(
            "Category", categories, index=categories.index(item["category"])
        )
        style = columns[1].text_input(
            "Style or aesthetic", value=item["style"]
        )
        color = st.text_input("Color", value=item["color"])
        upload = st.file_uploader(
            "Replace photo (optional)",
            type=("jpg", "jpeg", "png", "webp"),
            key=f"edit-image-{item['id']}",
        )
        submitted = st.form_submit_button("Save changes", type="primary")

    if submitted:
        if not name.strip() or not color.strip() or not style.strip():
            st.error("Please enter an item name, color, and style.")
            return
        if upload is not None and upload.size > 5 * 1024 * 1024:
            st.error("Please choose an image smaller than 5 MB.")
            return

        updated_item = {
            **item,
            "name": name.strip(),
            "category": category,
            "style": style.strip(),
            "color": color.strip(),
        }
        new_image: str | None = None
        try:
            if upload is not None:
                new_image = save_uploaded_image(upload, item["id"])
                if new_image is not None:
                    updated_item["image"] = new_image
            updated_items = [
                updated_item if existing["id"] == item["id"] else existing
                for existing in items
            ]
            save_data(updated_items, outfits)
        except (OSError, ValueError) as error:
            if new_image is not None:
                (IMAGE_DIR / new_image).unlink(missing_ok=True)
            st.error(f"Could not save these changes: {error}")
            return
        if upload is not None and item.get("image") != updated_item.get("image"):
            try:
                delete_image(item)
            except OSError as error:
                st.session_state["flash_warning"] = (
                    f"Changes saved, but the previous photo could not be deleted: {error}"
                )
        st.session_state["flash_message"] = f"Updated {updated_item['name']}."
        st.rerun()


@st.dialog("Remove clothing?")
def delete_item_confirm(
    item: dict[str, Any],
    items: list[dict[str, Any]],
    outfits: list[dict[str, Any]],
) -> None:
    st.write(f"Remove **{item['name']}** from your wardrobe?")
    cancel_column, confirm_column = st.columns(2)
    if cancel_column.button("Keep item", key=f"cancel-delete-{item['id']}"):
        st.rerun()
    if confirm_column.button(
        "Remove item", type="primary", key=f"confirm-delete-{item['id']}"
    ):
        remaining_items = [
            existing for existing in items if existing["id"] != item["id"]
        ]
        item_ids = {existing["id"] for existing in remaining_items}
        remaining_outfits = [
            {
                **outfit,
                "item_ids": [
                    item_id
                    for item_id in outfit["item_ids"]
                    if item_id in item_ids
                ],
            }
            for outfit in outfits
        ]
        try:
            save_data(remaining_items, remaining_outfits)
        except OSError as error:
            st.error(f"Could not remove this item from your wardrobe: {error}")
            return
        try:
            delete_image(item)
        except OSError as error:
            st.session_state["flash_warning"] = (
                f"Item removed, but its photo could not be deleted: {error}"
            )
        st.session_state["flash_message"] = f"Removed {item['name']}."
        st.rerun()


def set_page(page: str) -> None:
    st.session_state["navigation"] = page


def render_outfit_cards(outfit: list[dict[str, Any]]) -> None:
    columns = st.columns(len(outfit))
    for index, (column, item) in enumerate(zip(columns, outfit)):
        theme = CARD_THEMES[index % len(CARD_THEMES)]
        with column:
            with st.container(
                border=True,
                key=f"outfit-card-{theme}-{index}-{item['id']}",
            ):
                render_item_visual(item, height=250)
                render_category_badge(item["category"])
                st.markdown(
                    f'<div class="item-card-name">{escape(item["name"])}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"● {item['color']}  ·  {item['style']}")


def render_wardrobe(items: list[dict[str, Any]], outfits: list[dict[str, Any]]) -> None:
    title_column, button_column = st.columns([2, 1], vertical_alignment="center")
    title_column.title("My wardrobe")
    if button_column.button(
        "+  Add clothing", type="primary", use_container_width=True
    ):
        add_item_dialog(items, outfits)

    filter_columns = st.columns([1.1, 1, 1])
    category_filter = filter_columns[0].selectbox(
        "Category", ("All", *MAIN_CATEGORIES)
    )
    colors = sorted({item["color"] for item in items})
    color_filter = filter_columns[1].selectbox("Color", ("All", *colors))
    styles = sorted({item["style"] for item in items})
    style_filter = filter_columns[2].selectbox("Style", ("All", *styles))

    visible_items = [
        item for item in items
        if (category_filter == "All" or item["category"] == category_filter)
        and (color_filter == "All" or item["color"] == color_filter)
        and (style_filter == "All" or item["style"] == style_filter)
    ]
    st.caption(f"{len(visible_items)} pieces in view")

    if not visible_items:
        with st.container(border=True):
            st.markdown("### Nothing in this corner of your closet yet")
            st.write(
                "Try another filter, or add a clothing item to start building "
                "your digital wardrobe."
            )
            if st.button("Add a clothing item", type="primary"):
                add_item_dialog(items, outfits)
        return

    for start in range(0, len(visible_items), 3):
        columns = st.columns(3, gap="medium")
        for offset, (column, item) in enumerate(
            zip(columns, visible_items[start : start + 3])
        ):
            with column:
                theme = CARD_THEMES[(start + offset) % len(CARD_THEMES)]
                render_item_card(item, items, outfits, theme)


def render_generator(items: list[dict[str, Any]]) -> None:
    st.title("AI Outfit Generator")
    st.write(
        "Describe the style you’re in the mood for. Closetly checks your "
        "wardrobe’s style tags and recommends only pieces you already own."
    )
    with st.container(border=True, key="generator-form-card"):
        aesthetic_column, button_column = st.columns(
            [2, 1], vertical_alignment="bottom"
        )
        aesthetic = aesthetic_column.text_input(
            "Style or aesthetic",
            placeholder="e.g. casual, streetwear, minimalist, Korean style, formal",
            key="generator-aesthetic",
        )
        generate = button_column.button(
            "✦  Generate outfit",
            type="primary",
            use_container_width=True,
        )
        st.caption(
            "Recommendations use saved style tags and are assembled from your "
            "wardrobe only — no outside clothing is added."
        )

    if generate:
        if not aesthetic.strip():
            st.session_state.pop("current_outfit", None)
            st.session_state["outfit_missing"] = (
                aesthetic,
                ["a style or aesthetic"],
            )
        else:
            outfit, missing = matching_outfit(items, aesthetic.strip())
            if missing:
                st.session_state.pop("current_outfit", None)
                st.session_state["outfit_missing"] = (
                    aesthetic.strip(),
                    missing,
                )
            else:
                st.session_state["current_outfit"] = {
                    "aesthetic": aesthetic.strip(),
                    "item_ids": [item["id"] for item in outfit],
                }
                st.session_state.pop("outfit_missing", None)

    missing_state = st.session_state.get("outfit_missing")
    if missing_state:
        missing_aesthetic, missing_categories = missing_state
        if missing_categories == ["clothing tagged with that style"]:
            st.warning(
                f"No wardrobe pieces are tagged with “{missing_aesthetic}” yet. "
                "Add that aesthetic to an item's style, or try one already in "
                "your wardrobe."
            )
        elif missing_categories == ["a style or aesthetic"]:
            st.warning("Enter a style or aesthetic to build an outfit.")
        else:
            st.warning(
                f"For “{missing_aesthetic}”, your wardrobe still needs: "
                f"{', '.join(missing_categories).lower()}."
            )
            st.caption(
                "Add the missing pieces with a matching style tag in My Wardrobe."
            )

    current = st.session_state.get("current_outfit")
    if current:
        current_items = [
            item for item in items if item["id"] in current["item_ids"]
        ]
        outfit_categories = {item["category"] for item in current_items}
        if {"Top", "Bottom", "Shoes"} <= outfit_categories:
            st.write("")
            st.markdown(
                f'<div class="eyebrow">YOUR {current["aesthetic"].upper()} LOOK</div>',
                unsafe_allow_html=True,
            )
            render_outfit_cards(current_items)
            if st.button("↻  Generate another outfit", type="primary"):
                outfit, missing = matching_outfit(
                    items,
                    current["aesthetic"],
                    set(current["item_ids"]),
                )
                if missing:
                    st.session_state.pop("current_outfit", None)
                    st.session_state["outfit_missing"] = (
                        current["aesthetic"],
                        missing,
                    )
                else:
                    st.session_state["current_outfit"] = {
                        **current,
                        "item_ids": [item["id"] for item in outfit],
                    }
                    st.rerun()
        else:
            st.info(
                "This outfit is no longer complete in your wardrobe. "
                "Generate a new look to continue."
            )
            st.session_state.pop("current_outfit", None)


def main() -> None:
    st.set_page_config(
        page_title="Smart Dressing System",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="auto",
    )
    inject_styles()
    st.sidebar.button(
        "closetly.",
        key="home-link",
        on_click=set_page,
        args=("Home",),
        use_container_width=True,
    )
    st.sidebar.caption("SMART DRESSING SYSTEM")
    st.sidebar.markdown("YOUR SPACE")
    st.session_state.setdefault("navigation", "Home")
    if st.session_state["navigation"] not in {"Home", *NAVIGATION}:
        st.session_state["navigation"] = "Home"
    for page in NAVIGATION:
        st.sidebar.button(
            page,
            key=f"nav-{page}",
            type=(
                "primary"
                if st.session_state["navigation"] == page
                else "secondary"
            ),
            use_container_width=True,
            on_click=set_page,
            args=(page,),
        )
    st.sidebar.divider()
    st.sidebar.caption("Your clothes. Your style. All in one place.")

    try:
        items, outfits = load_data()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        st.error(f"Could not load your wardrobe: {error}")
        st.stop()

    flash_message = st.session_state.pop("flash_message", None)
    if flash_message:
        st.success(flash_message)
    flash_warning = st.session_state.pop("flash_warning", None)
    if flash_warning:
        st.warning(flash_warning)

    selected_page = st.session_state["navigation"]
    if selected_page == "Home":
        st.markdown(
            '<div class="eyebrow">A SMARTER WAY TO GET DRESSED</div>',
            unsafe_allow_html=True,
        )
        st.title("Your Wardrobe, Your Style.")
        st.write(
            "A digital home for the clothes you own, with outfit ideas built "
            "around the way you like to dress."
        )
        st.write("")
        feature_columns = st.columns(2, gap="large")
        with feature_columns[0]:
            with st.container(border=True, key="home-wardrobe-card"):
                st.markdown(
                    '<div class="eyebrow">01 · YOUR CLOSET</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("### My Wardrobe")
                st.write(
                    "Add, edit, and organize your clothing with photos, "
                    "categories, colors, and style tags."
                )
                st.caption(f"{len(items)} pieces in your closet")
                st.button(
                    "Explore my wardrobe  →",
                    type="primary",
                    use_container_width=True,
                    on_click=set_page,
                    args=("My Wardrobe",),
                )
        with feature_columns[1]:
            with st.container(border=True, key="home-generator-card"):
                st.markdown(
                    '<div class="eyebrow">02 · YOUR NEXT LOOK</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("### AI Outfit Generator")
                st.write(
                    "Tell us the aesthetic you want. Get outfit combinations "
                    "made only from clothes you already own."
                )
                st.caption(
                    "Casual · streetwear · minimalist · Korean style · formal"
                )
                st.button(
                    "Find an outfit  →",
                    use_container_width=True,
                    on_click=set_page,
                    args=("AI Outfit Generator",),
                )
        if items:
            st.write("")
            st.subheader("Your wardrobe at a glance")
            preview_columns = st.columns(min(4, len(items)))
            for column, item in zip(preview_columns, reversed(items[-4:])):
                with column:
                    with st.container(border=True):
                        render_item_visual(item, height=155)
                        st.markdown(f"**{item['name']}**")
                        st.caption(f"{item['category']} · {item['color']}")
    elif selected_page == "My Wardrobe":
        render_wardrobe(items, outfits)
    else:
        render_generator(items)


if __name__ == "__main__":
    main()
