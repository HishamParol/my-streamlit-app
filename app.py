import streamlit as st

from database.schema import init_db
from functions.theme import apply_custom_theme, THEME_ORANGE, THEME_BLACK, THEME_GREY, THEME_LIGHT_GREY
from pages.equipment_lists import equipments_page
from pages.parts_management import parts_management_page

st.set_page_config(
    page_title="Car Garage Business Planning",
    page_icon="🚗",
    layout="wide"
)

init_db()

if "current_page" not in st.session_state:
    st.session_state.current_page = "main"

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def main_page():
    apply_custom_theme()
    st.title("🚗 Car Garage Business Planning")
    st.caption("Comprehensive Equipment Procurement, Parts Inventory & Supplier Management")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="border: 2px solid {THEME_ORANGE}; border-radius: 12px; padding: 24px; background-color: {THEME_LIGHT_GREY};">
                <h3 style="margin-top: 0; color: {THEME_BLACK};">🛠️ Equipments List</h3>
                <p style="color: {THEME_GREY}; font-size: 14px;">Manage workshop machinery, tool requirements, multi-supplier quotes, and export PDF comparison reports.</p>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Open Equipments List ➔", key="btn_equipments", use_container_width=True):
            navigate_to("equipments")

    with col2:
        st.markdown(
            f"""
            <div style="border: 2px solid {THEME_ORANGE}; border-radius: 12px; padding: 24px; background-color: {THEME_LIGHT_GREY};">
                <h3 style="margin-top: 0; color: {THEME_BLACK};">📦 Parts Inventory & Sourcing Guide</h3>
                <p style="color: {THEME_GREY}; font-size: 14px;">Track spare parts stock, link parts to car fitments (Make/Model), compare brands (e.g. Bosch, Brembo), and locate preferred suppliers.</p>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Open Parts Management ➔", key="btn_parts", use_container_width=True):
            navigate_to("parts")

# Streamlit Routing
try:
    p_main = st.Page(main_page, title="Business Planning", icon="🚗", default=True)
    p_equip = st.Page(equipments_page, title="Equipments List", icon="🛠️")
    p_parts = st.Page(parts_management_page, title="Parts Sourcing & Inventory", icon="📦")
    pg = st.navigation([p_main, p_equip, p_parts])
    pg.run()
except AttributeError:
    if st.session_state.current_page == "main":
        main_page()
    elif st.session_state.current_page == "equipments":
        equipments_page()
    elif st.session_state.current_page == "parts":
        parts_management_page()