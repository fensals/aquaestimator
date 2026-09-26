import os
import pandas as pd
import streamlit as st

APP_NAME = "Bootcamp 10.0 AquaEstimator"
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "alltalentz.png")

st.set_page_config(page_title=APP_NAME, page_icon="💧", layout="wide")

# Simple droplet wordmark used until alltalentz.png is dropped into assets/.
FALLBACK_LOGO_SVG = """
<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
  <path d="M22 2 C22 2 8 20 8 29 a14 14 0 0 0 28 0 C36 20 22 2 22 2 Z"
        fill="#1E88E5"/>
  <path d="M22 8 C22 8 12 21 12 28 a10 10 0 0 0 20 0 C32 21 22 8 22 8 Z"
        fill="#64B5F6" opacity="0.6"/>
</svg>
"""


def render_header():
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=48)
        else:
            st.markdown(FALLBACK_LOGO_SVG, unsafe_allow_html=True)
    with col_title:
        st.markdown(f"## {APP_NAME}")


# Reference data

# Which materials are offered depends on which surface the reading is for.
SURFACE_MATERIALS = {
    "Floor": ["Carpet & Pad", "Hardwood", "Laminate", "Vinyl/LVP", "Tile", "Concrete"],
    "Wall": ["Drywall", "Plaster", "Wood Paneling", "Concrete Block", "Brick"],
    "Ceiling": ["Drywall", "Plaster", "Acoustic Tile", "Wood"],
}

# Material porosity affects how long an area takes to dry and whether it
# needs specialty (Class 4) drying equipment.
MATERIAL_PROFILES = {
    "Carpet & Pad":   {"porosity": "high",   "base_dry_days": 3},
    "Hardwood":       {"porosity": "low",    "base_dry_days": 5},
    "Laminate":       {"porosity": "medium", "base_dry_days": 4},
    "Vinyl/LVP":      {"porosity": "low",    "base_dry_days": 3},
    "Tile":           {"porosity": "low",    "base_dry_days": 2},
    "Concrete":       {"porosity": "low",    "base_dry_days": 5},
    "Drywall":        {"porosity": "medium", "base_dry_days": 3},
    "Plaster":        {"porosity": "medium", "base_dry_days": 4},
    "Wood Paneling":  {"porosity": "low",    "base_dry_days": 4},
    "Concrete Block": {"porosity": "low",    "base_dry_days": 5},
    "Brick":          {"porosity": "low",    "base_dry_days": 5},
    "Acoustic Tile":  {"porosity": "high",   "base_dry_days": 2},
    "Wood":           {"porosity": "low",    "base_dry_days": 4},
}

# Classes of water
# Class 1 = least evaporation load, Class 4 = specialty/deeply saturated.
CLASS_PROFILES = {
    1: {"air_mover_per_sqft": 100, "dehu_per_sqft": 1000, "day_adj": 0},
    2: {"air_mover_per_sqft": 60,  "dehu_per_sqft": 700,  "day_adj": 1},
    3: {"air_mover_per_sqft": 40,  "dehu_per_sqft": 500,  "day_adj": 2},
    4: {"air_mover_per_sqft": 40,  "dehu_per_sqft": 400,  "day_adj": 4},
}

# Daily equipment rates and labor rate (illustrative placeholder pricing).
PRICING = {
    "Air Mover ($/day)": 35.00,
    "LGR Dehumidifier ($/day)": 75.00,
    "Antimicrobial Treatment ($/sqft)": 0.45,
    "Labor - Setup/Monitoring ($/hr)": 45.00,
    "Labor Hours per Room (setup + 1 daily check)": 1.5,
}

DEFAULT_DRYING_GOAL = 15  # % moisture content considered "dry" for most materials


def classify_severity(moisture_pct: float, drying_goal: float) -> str:
    if moisture_pct < drying_goal:
        return "Dry (monitor only)"
    elif moisture_pct < 25:
        return "Elevated"
    elif moisture_pct < 40:
        return "Wet"
    else:
        return "Saturated"


def environment_adjustment(rh_pct: float, temp_f: float):
    """Ambient relative humidity and temperature affect evaporation rate:
    high RH slows evaporation and taxes dehumidifier capacity; cold air
    holds less moisture and slows drying; warm, drier air speeds it up.
    Returns (extra_drying_days, extra_dehumidifiers)."""
    day_adj = 0
    extra_dehu = 0

    if rh_pct >= 70:
        day_adj += 1
        extra_dehu += 1
    elif rh_pct <= 40:
        day_adj -= 1

    if temp_f < 60:
        day_adj += 1
    elif temp_f > 85:
        day_adj -= 1

    return day_adj, extra_dehu


def calculate_room_plan(room_name, surface, material, sqft, moisture_pct,
                         rh_pct, temp_f, water_class, drying_goal):
    profile = CLASS_PROFILES[water_class]
    material_profile = MATERIAL_PROFILES[material]
    severity = classify_severity(moisture_pct, drying_goal)

    row = {
        "Room": room_name,
        "Surface": surface,
        "Material": material,
        "Sq Ft": sqft,
        "Moisture %": moisture_pct,
        "RH %": rh_pct,
        "Temp (°F)": temp_f,
        "Severity": severity,
        "Class": water_class,
    }

    if severity == "Dry (monitor only)":
        row.update({"Air Movers": 0, "Dehumidifiers": 0, "Est. Drying Days": 0})
        return row

    air_movers = max(1, round(sqft / profile["air_mover_per_sqft"]))
    dehumidifiers = max(1, round(sqft / profile["dehu_per_sqft"]))

    drying_days = material_profile["base_dry_days"] + profile["day_adj"]
    if severity == "Saturated" and material_profile["porosity"] == "low":
        drying_days += 2
    elif severity == "Saturated":
        drying_days += 1

    env_day_adj, env_extra_dehu = environment_adjustment(rh_pct, temp_f)
    drying_days = max(1, drying_days + env_day_adj)
    dehumidifiers += env_extra_dehu

    row.update({
        "Air Movers": air_movers,
        "Dehumidifiers": dehumidifiers,
        "Est. Drying Days": drying_days,
    })
    return row


def build_line_items(plan_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in plan_df.iterrows():
        if r["Est. Drying Days"] == 0:
            continue

        days = r["Est. Drying Days"]
        am_cost = r["Air Movers"] * days * PRICING["Air Mover ($/day)"]
        dehu_cost = r["Dehumidifiers"] * days * PRICING["LGR Dehumidifier ($/day)"]
        antimicrobial_cost = r["Sq Ft"] * PRICING["Antimicrobial Treatment ($/sqft)"]
        labor_cost = (
            PRICING["Labor Hours per Room (setup + 1 daily check)"]
            * days
            * PRICING["Labor - Setup/Monitoring ($/hr)"]
        )

        rows.append({"Room": r["Room"], "Line Item": "Air Mover Rental",
                      "Qty": r["Air Movers"], "Unit": f"{days} day(s)",
                      "Cost": round(am_cost, 2)})
        rows.append({"Room": r["Room"], "Line Item": "LGR Dehumidifier Rental",
                      "Qty": r["Dehumidifiers"], "Unit": f"{days} day(s)",
                      "Cost": round(dehu_cost, 2)})
        rows.append({"Room": r["Room"], "Line Item": "Antimicrobial Treatment",
                      "Qty": r["Sq Ft"], "Unit": "sqft",
                      "Cost": round(antimicrobial_cost, 2)})
        rows.append({"Room": r["Room"], "Line Item": "Labor (Setup & Monitoring)",
                      "Qty": PRICING["Labor Hours per Room (setup + 1 daily check)"] * days,
                      "Unit": "hrs", "Cost": round(labor_cost, 2)})

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Room list state (supports add / remove, and surface-dependent material)
# ---------------------------------------------------------------------------

if "room_ids" not in st.session_state:
    st.session_state.room_ids = [0]
    st.session_state.next_room_id = 1


def add_room():
    st.session_state.room_ids.append(st.session_state.next_room_id)
    st.session_state.next_room_id += 1


def remove_room(rid):
    if rid in st.session_state.room_ids:
        st.session_state.room_ids.remove(rid)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

render_header()
st.caption(
    "Converts room-by-room moisture and environmental readings into an "
    "equipment plan and a cost estimate. Simplified rules-based demo — not "
    "a certified IICRC S500 calculation."
)

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=64)
    st.markdown(f"### {APP_NAME}")
    st.header("Job Info")
    job_name = st.text_input("Claim No.", " ")
    client_name = st.text_input("Client Name", "")
    st.markdown("---")
    st.subheader("Pricing Assumptions")
    for k, v in PRICING.items():
        st.write(f"**{k}:** {v}")

st.subheader("Set Drying Goal")

goal_col, _= st.columns([1, 7])
drying_goal = goal_col.number_input(
    "Drying Goal (%)",
    min_value=0,
    max_value=100,
    value=DEFAULT_DRYING_GOAL,
)


st.subheader("Enter Room Readings")

for rid in list(st.session_state.room_ids):
    with st.container(border=True):
        cols = st.columns([1.6, 1.1, 1.5, 0.9, 0.9, 0.9, 0.9, 0.8, 0.5])

        room_name = cols[0].text_input(
            "Room", value=f"Room {rid + 1}", key=f"room_name_{rid}"
        )

        surface_key = f"surface_{rid}"
        if surface_key not in st.session_state:
            st.session_state[surface_key] = "Floor"
        surface = cols[1].selectbox(
            "Surface", list(SURFACE_MATERIALS.keys()), key=surface_key
        )

        material_options = SURFACE_MATERIALS[surface]
        material_key = f"material_{rid}"
        if (material_key not in st.session_state
                or st.session_state[material_key] not in material_options):
            st.session_state[material_key] = material_options[0]
        material = cols[2].selectbox("Material", material_options, key=material_key)

        sqft = cols[3].number_input(
            "Sq Ft", min_value=1, value=100, key=f"sqft_{rid}"
        )
        moisture = cols[4].number_input(
            "Moisture %", min_value=0, max_value=100, value=30, key=f"moisture_{rid}"
        )
        rh = cols[5].number_input(
            "RH %", min_value=0, max_value=100, value=55, key=f"rh_{rid}"
        )
        temp = cols[6].number_input(
            "Temp (°F)", min_value=32, max_value=120, value=70, key=f"temp_{rid}"
        )

        class_key = f"class_{rid}"
        if class_key not in st.session_state:
            st.session_state[class_key] = 2
        wclass = cols[7].selectbox(
            "Class", list(CLASS_PROFILES.keys()), key=class_key
        )

        cols[8].markdown("&nbsp;")
        cols[8].button("🗑", key=f"remove_{rid}", on_click=remove_room, args=(rid,))

st.button("➕ Add Room", on_click=add_room)

# Snapshot current widget state into a plain rooms list for calculation.
rooms_data = []
for rid in st.session_state.room_ids:
    rooms_data.append({
        "Room": st.session_state.get(f"room_name_{rid}", f"Room {rid + 1}"),
        "Surface": st.session_state.get(f"surface_{rid}", "Floor"),
        "Material": st.session_state.get(f"material_{rid}"),
        "Sq Ft": st.session_state.get(f"sqft_{rid}", 100),
        "Moisture %": st.session_state.get(f"moisture_{rid}", 30),
        "RH %": st.session_state.get(f"rh_{rid}", 55),
        "Temp (°F)": st.session_state.get(f"temp_{rid}", 70),
        "Class": st.session_state.get(f"class_{rid}", 2),
    })

st.markdown("---")

if st.button("Generate Equipment Plan & Estimate", type="primary"):
    st.markdown(
        f"This drying assessment and equipment estimate is prepared for "
        f"**Claim No. {job_name}**, Client: **{client_name or '—'}**."
    )

    plan_rows = [
        calculate_room_plan(
            r["Room"], r["Surface"], r["Material"], r["Sq Ft"], r["Moisture %"],
            r["RH %"], r["Temp (°F)"], int(r["Class"]), drying_goal,
        )
        for r in rooms_data
        if r["Room"]
    ]
    plan_df = pd.DataFrame(plan_rows)

    st.subheader("Equipment Plan")
    st.dataframe(plan_df, use_container_width=True)

    line_items_df = build_line_items(plan_df)

    if not line_items_df.empty:
        st.subheader("Cost Line Items")
        st.dataframe(line_items_df, use_container_width=True)

        total_cost = line_items_df["Cost"].sum()
        st.metric("Estimated Total Cost", f"${total_cost:,.2f}")
    else:
        st.info("All rooms are at or below the drying goal — no equipment needed.")

st.markdown("---")
st.caption(
    "The goal is to show how a repetitive, rules-based part of the estimating "
    "workflow (moisture/psychrometric reading -> equipment sizing -> cost "
    "line items) can be automated."
)