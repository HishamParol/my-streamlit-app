import sqlite3
import pandas as pd
import streamlit as st

from database.schema import get_connection
from functions.theme import apply_custom_theme
from functions.functions_parts_management import (
    get_parts_overview,
    search_parts_sourcing_guide,
    generate_parts_sourcing_pdf
)

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def parts_management_page():
    apply_custom_theme()
    st.title("📦 Parts Inventory & Sourcing Guide")
    st.caption("Track parts stock, car fitments, multi-brand options, and vendor sourcing guides in ₹")
    st.divider()

    if st.button("← Back to Business Planning", key="btn_back_parts"):
        navigate_to("main")

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Parts Sourcing Guide",
        "📦 Parts Inventory",
        "🚗 Car Fitment Mapping",
        "🏢 Brand & Supplier Sources"
    ])

    # TAB 1: Sourcing Guide & Lookup Engine
    with tab1:
        st.subheader("🔍 Car-to-Part Sourcing Lookup Engine")
        st.caption("Find which brands and suppliers provide parts for specific vehicle models.")

        conn = get_connection()
        makes_df = pd.read_sql_query("SELECT DISTINCT car_make FROM part_fitments ORDER BY car_make ASC", conn)
        models_df = pd.read_sql_query("SELECT DISTINCT car_model FROM part_fitments ORDER BY car_model ASC", conn)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            make_list = ["All"] + makes_df["car_make"].tolist()
            sel_make = st.selectbox("Filter by Car Make", options=make_list)
        with col_s2:
            model_list = ["All"] + models_df["car_model"].tolist()
            sel_model = st.selectbox("Filter by Car Model", options=model_list)
        with col_s3:
            part_search = st.text_input("Search Part Name / Part No", placeholder="e.g. Brake Pad, FIL101")

        guide_df = search_parts_sourcing_guide(conn, sel_make, sel_model, part_search)
        conn.close()

        if guide_df.empty:
            st.info("No sourcing records found matching your selection.")
        else:
            # Formatting cost for display
            display_df = guide_df.copy()
            display_df["Unit Cost (₹)"] = display_df["Unit Cost (₹)"].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "N/A")
            display_df["Preferred Source"] = display_df["Preferred Source"].apply(lambda x: "⭐ Yes" if x == 1 else "No")
            
            st.dataframe(display_df, use_container_width=True)

            pdf_bytes = generate_parts_sourcing_pdf(
                guide_df,
                "Car Garage - Spare Parts Sourcing & Procurement Guide",
                f"Make: {sel_make} | Model: {sel_model} | Results: {len(guide_df)} records"
            )

            st.download_button(
                label="📥 Download Parts Sourcing Guide (PDF)",
                data=pdf_bytes,
                file_name="garage_parts_sourcing_guide.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

    # TAB 2: Manage Parts Master List
    with tab2:
        st.subheader("Add New Part to Catalog")
        with st.form("add_part_form", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_no = st.text_input("Part Number (SKU)", placeholder="e.g. BRK-PAD-01")
                p_name = st.text_input("Part Name", placeholder="e.g. Front Brake Pads Set")
            with col_p2:
                p_cat = st.selectbox("Category", options=[
                    "Brakes & Suspension", "Engine Components", "Filters & Oils",
                    "Electrical & Sensors", "AC & Cooling", "Body & Trim", "General Consumables"
                ])
                col_qty1, col_qty2 = st.columns(2)
                with col_qty1:
                    p_stock = st.number_input("Initial Stock Qty", min_value=0, value=0)
                with col_qty2:
                    p_min = st.number_input("Min Stock Level", min_value=0, value=2)

            if st.form_submit_button("Save Part to Catalog"):
                if not p_no.strip() or not p_name.strip():
                    st.error("Part Number and Part Name are required.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO parts (part_number, name, category, stock_qty, min_stock_level) VALUES (?, ?, ?, ?, ?)",
                            (p_no.strip(), p_name.strip(), p_cat, p_stock, p_min)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Part '{p_name}' added successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Part Number '{p_no}' already exists.")

        st.divider()
        st.subheader("Parts Master Inventory")
        conn = get_connection()
        parts_df = get_parts_overview(conn)
        conn.close()

        if not parts_df.empty:
            st.dataframe(parts_df.drop(columns=["id"]), use_container_width=True)

    # TAB 3: Map Car Fitment
    with tab3:
        st.subheader("Link Part to Car Fitment")
        st.caption("Specify which car makes and models a specific part fits.")

        conn = get_connection()
        parts_list_df = pd.read_sql_query("SELECT id, part_number, name FROM parts ORDER BY name ASC", conn)
        conn.close()

        if parts_list_df.empty:
            st.info("Please register parts in the 'Parts Inventory' tab first.")
        else:
            with st.form("add_fitment_form", clear_on_submit=True):
                sel_part_id = st.selectbox(
                    "Select Part",
                    options=parts_list_df["id"],
                    format_func=lambda x: f"{parts_list_df[parts_list_df['id']==x]['part_number'].values[0]} - {parts_list_df[parts_list_df['id']==x]['name'].values[0]}"
                )
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    car_make = st.text_input("Car Make", placeholder="e.g. Maruti Suzuki, Hyundai, Honda")
                with col_f2:
                    car_model = st.text_input("Car Model", placeholder="e.g. Swift, i20, City")
                with col_f3:
                    year_range = st.text_input("Year Range", placeholder="e.g. 2018-2023, All Years")

                if st.form_submit_button("Link Fitment"):
                    if not car_make.strip() or not car_model.strip():
                        st.error("Car Make and Model are required.")
                    else:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO part_fitments (part_id, car_make, car_model, year_range) VALUES (?, ?, ?, ?)",
                            (sel_part_id, car_make.strip(), car_model.strip(), year_range.strip() or "All Years")
                        )
                        conn.commit()
                        conn.close()
                        st.success("Car fitment mapped successfully!")
                        st.rerun()

    # TAB 4: Multi-Brand & Multi-Supplier Sources
    with tab4:
        st.subheader("Record Brand & Supplier Quotes for Parts")
        st.caption("A single part can have multiple brands (e.g. Bosch, TVS, Brembo) sourced from different suppliers.")

        conn = get_connection()
        parts_list_df = pd.read_sql_query("SELECT id, part_number, name FROM parts ORDER BY name ASC", conn)
        supp_df = pd.read_sql_query("SELECT id, name FROM suppliers ORDER BY name ASC", conn)
        conn.close()

        if parts_list_df.empty or supp_df.empty:
            st.info("Ensure you have created parts in 'Parts Inventory' and registered suppliers in the main system.")
        else:
            with st.form("add_source_form", clear_on_submit=True):
                col_src1, col_src2 = st.columns(2)
                with col_src1:
                    sel_p_id = st.selectbox(
                        "Select Part",
                        options=parts_list_df["id"],
                        format_func=lambda x: f"{parts_list_df[parts_list_df['id']==x]['part_number'].values[0]} - {parts_list_df[parts_list_df['id']==x]['name'].values[0]}"
                    )
                    brand_name = st.text_input("Part Brand Name", placeholder="e.g. Bosch, Brembo, TVS, OEM")
                with col_src2:
                    sel_s_id = st.selectbox(
                        "Select Supplier",
                        options=supp_df["id"],
                        format_func=lambda x: supp_df[supp_df['id']==x]['name'].values[0]
                    )
                    unit_cost = st.number_input("Unit Cost (₹ in Rupees)", min_value=0.0, step=100.0)

                col_src3, col_src4 = st.columns(2)
                with col_src3:
                    lead_days = st.number_input("Delivery Lead Time (Days)", min_value=0, value=1)
                with col_src4:
                    is_pref = st.checkbox("Mark as Preferred Supplier for this Part", value=False)

                if st.form_submit_button("Save Brand & Supplier Sourcing Option"):
                    if not brand_name.strip():
                        st.error("Brand name is required.")
                    else:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO part_supplier_sources (part_id, brand_name, supplier_id, unit_cost, lead_time_days, is_preferred) VALUES (?, ?, ?, ?, ?, ?)",
                            (sel_p_id, brand_name.strip(), sel_s_id, unit_cost, lead_days, 1 if is_pref else 0)
                        )
                        conn.commit()
                        conn.close()
                        st.success("Sourcing option recorded successfully!")
                        st.rerun()