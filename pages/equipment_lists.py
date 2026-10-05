import sqlite3
import pandas as pd
import streamlit as st

from database.schema import get_connection
from functions.theme import apply_custom_theme
from functions.functions_equipments import generate_pdf_report

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def equipments_page():
    apply_custom_theme()
    st.title("🛠️ Car Garage Equipments & Price Comparison")
    st.caption("Manage workshop tools, categories, multi-supplier quotations in ₹, and export PDF procurement plans")
    st.divider()

    if st.button("← Back to Business Planning", key="btn_back"):
        navigate_to("main")

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Price Comparison & PDF Reports", 
        "➕ Add / Manage Equipment", 
        "📁 Categories", 
        "🏢 Suppliers & Quotations"
    ])

    with tab1:
        conn = get_connection()
        equip_df = pd.read_sql_query("SELECT * FROM equipments ORDER BY si_no ASC", conn)
        supp_df = pd.read_sql_query("SELECT * FROM suppliers ORDER BY name ASC", conn)
        prices_df = pd.read_sql_query("""
            SELECT sp.equipment_id, sp.supplier_id, s.name as supplier_name, sp.price 
            FROM supplier_prices sp
            JOIN suppliers s ON sp.supplier_id = s.id
        """, conn)
        conn.close()

        if equip_df.empty:
            st.info("No equipment items registered yet. Go to 'Add / Manage Equipment' to get started.")
        else:
            comparison_rows = []
            for _, eq in equip_df.iterrows():
                qty = eq.get("qty", 1) if "qty" in eq else 1
                row = {
                    "SI No": eq["si_no"],
                    "Equipment Name": eq["name"],
                    "Qty": qty,
                    "Requirement": eq["requirement_type"],
                    "Category": eq["category"]
                }
                
                eq_prices = prices_df[prices_df["equipment_id"] == eq["id"]]
                
                min_price = float("inf")
                best_supplier = "None"
                
                for _, supp in supp_df.iterrows():
                    supp_quote = eq_prices[eq_prices["supplier_id"] == supp["id"]]
                    if not supp_quote.empty:
                        p_val = supp_quote["price"].values[0]
                        row[f"{supp['name']} (₹)"] = f"₹{p_val:,.2f}"
                        if p_val < min_price:
                            min_price = p_val
                            best_supplier = supp["name"]
                    else:
                        row[f"{supp['name']} (₹)"] = "N/A"

                if min_price != float("inf"):
                    total_cost = min_price * qty
                    row["Lowest Unit Price"] = f"₹{min_price:,.2f}"
                    row["Total Est. Cost"] = f"₹{total_cost:,.2f}"
                    row["Best Supplier"] = best_supplier
                else:
                    row["Lowest Unit Price"] = "No quotes"
                    row["Total Est. Cost"] = "N/A"
                    row["Best Supplier"] = "N/A"

                comparison_rows.append(row)

            res_df = pd.DataFrame(comparison_rows)

            st.subheader("Equipment Quotation Comparison Matrix")
            st.dataframe(res_df, use_container_width=True)

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total Garage Items", len(equip_df))
            with col_m2:
                st.metric("Registered Suppliers", len(supp_df))
            with col_m3:
                mandatory_count = len(equip_df[equip_df["requirement_type"] == "Mandatory"])
                st.metric("Mandatory Garage Items", mandatory_count)

            st.divider()

            st.subheader("📄 Download PDF Reports")

            with st.expander("🎯 Filtered PDF Export (Grouped by Category Headings)", expanded=False):
                st.write("Select specific categories and requirement type to download PDF reports formatted with category subheadings.")
                col_f1, col_f2 = st.columns(2)
                
                all_categories = sorted(res_df["Category"].unique().tolist())
                with col_f1:
                    selected_cats = st.multiselect(
                        "Select Categories", 
                        options=all_categories, 
                        default=all_categories,
                        help="Choose categories to include"
                    )
                with col_f2:
                    selected_req = st.radio(
                        "Requirement Filter",
                        options=["All", "Mandatory Only", "Optional Only"],
                        horizontal=True
                    )

                filtered_df = res_df.copy()
                if selected_cats:
                    filtered_df = filtered_df[filtered_df["Category"].isin(selected_cats)]
                else:
                    filtered_df = filtered_df.iloc[0:0]

                if selected_req == "Mandatory Only":
                    filtered_df = filtered_df[filtered_df["Requirement"] == "Mandatory"]
                elif selected_req == "Optional Only":
                    filtered_df = filtered_df[filtered_df["Requirement"] == "Optional"]

                filtered_df = filtered_df.reset_index(drop=True)

                st.caption(f"Found {len(filtered_df)} matching item(s) for export.")

                if not filtered_df.empty:
                    custom_pdf_data = generate_pdf_report(
                        filtered_df,
                        "Car Garage Business Planning - Category Grouped Report",
                        f"Requirement Filter: {selected_req} | Items: {len(filtered_df)}",
                        group_by_category=True
                    )
                    st.download_button(
                        label="📥 Download Category Grouped PDF",
                        data=custom_pdf_data,
                        file_name="garage_category_grouped_report.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.warning("No equipment matches the selected filters.")

            with st.expander("🏢 Supplier Specific & Best Price Breakdown PDF Export", expanded=True):
                st.write("Select one or more suppliers to generate a quotation report showing equipment quantities, best unit prices, total best price, and best supplier selection.")
                
                all_supplier_names = supp_df["name"].tolist() if not supp_df.empty else []
                if not all_supplier_names:
                    st.info("No suppliers registered yet. Please add suppliers in the 'Suppliers & Quotations' tab.")
                else:
                    selected_supps = st.multiselect(
                        "Select Supplier(s)",
                        options=all_supplier_names,
                        default=all_supplier_names,
                        help="Choose supplier(s) to include in the price comparison."
                    )

                    if selected_supps:
                        supp_rows = []
                        total_items_count = len(equip_df)
                        total_tools_qty = 0
                        total_best_equipment_cost = 0.0

                        for _, eq in equip_df.iterrows():
                            qty = eq.get("qty", 1) if "qty" in eq else 1
                            total_tools_qty += qty
                            
                            eq_prices = prices_df[prices_df["equipment_id"] == eq["id"]]

                            min_price = float("inf")
                            best_supplier = "None"

                            for s_name in selected_supps:
                                supp_info = supp_df[supp_df["name"] == s_name]
                                if not supp_info.empty:
                                    s_id = supp_info["id"].values[0]
                                    supp_quote = eq_prices[eq_prices["supplier_id"] == s_id]
                                    if not supp_quote.empty:
                                        p_val = float(supp_quote["price"].values[0])
                                        if p_val < min_price:
                                            min_price = p_val
                                            best_supplier = s_name

                            if min_price != float("inf"):
                                unit_price_str = f"₹{min_price:,.2f}"
                                total_price_val = min_price * qty
                                total_price_str = f"₹{total_price_val:,.2f}"
                                total_best_equipment_cost += total_price_val
                            else:
                                unit_price_str = "N/A"
                                total_price_str = "N/A"
                                best_supplier = "N/A"

                            s_row = {
                                "SI No": eq["si_no"],
                                "Equipment Name": eq["name"],
                                "Qty": qty,
                                "Unit Price (Best)": unit_price_str,
                                "Total Price (Best)": total_price_str,
                                "Best Supplier": best_supplier,
                            }

                            supp_rows.append(s_row)

                        supp_df_report = pd.DataFrame(supp_rows)

                        st.dataframe(supp_df_report, use_container_width=True)

                        st.markdown("#### 📊 Best Price Summary")
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.metric(
                                label="💰 Total Best Equipment Cost",
                                value=f"₹{total_best_equipment_cost:,.2f}",
                                help="Total cost combining the best unit price for each equipment item."
                            )
                        with col_b2:
                            st.metric(
                                label="📦 Total Equipment Quantity",
                                value=f"{total_tools_qty} items"
                            )

                        sum_metrics = {
                            "Total Equipment Items": total_items_count,
                            "Total Equipment Quantity": total_tools_qty,
                            "Total Best Equipment Cost": f"₹{total_best_equipment_cost:,.2f}"
                        }

                        pdf_supp_data = generate_pdf_report(
                            supp_df_report,
                            "Car Garage Business Planning - Best Supplier Quotation Report",
                            f"Selected Suppliers: {', '.join(selected_supps)} | Total Best Cost: ₹{total_best_equipment_cost:,.2f}",
                            summary_metrics=sum_metrics
                        )

                        st.download_button(
                            label="📥 Download Best Price Quotation PDF",
                            data=pdf_supp_data,
                            file_name="garage_best_supplier_quotation_report.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.warning("Please select at least one supplier to generate report.")

            st.write("")
            col_dl1, col_dl2 = st.columns(2)

            mandatory_df = res_df[res_df["Requirement"] == "Mandatory"].reset_index(drop=True)

            with col_dl1:
                st.markdown("##### Standard Mandatory Items PDF")
                if not mandatory_df.empty:
                    pdf_data_mandatory = generate_pdf_report(
                        mandatory_df,
                        "Car Garage Business Planning - Mandatory Equipments List",
                        f"Requirement Filter: Mandatory Only | Items: {len(mandatory_df)}"
                    )
                    st.download_button(
                        label="📥 Download Mandatory Items PDF",
                        data=pdf_data_mandatory,
                        file_name="garage_mandatory_equipments.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.info("No mandatory items found in current list.")

            with col_dl2:
                st.markdown("##### Full Procurement PDF")
                pdf_data_all = generate_pdf_report(
                    res_df,
                    "Car Garage Business Planning - Complete Equipments Matrix",
                    f"Requirement Filter: All Items | Items: {len(res_df)}"
                )
                st.download_button(
                    label="📥 Download Full Procurement PDF",
                    data=pdf_data_all,
                    file_name="garage_all_equipments.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    with tab2:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(si_no) FROM equipments")
        max_si = cursor.fetchone()[0]
        next_si_no = (max_si or 0) + 1

        cats_df = pd.read_sql_query("SELECT name FROM categories ORDER BY name ASC", conn)
        conn.close()

        category_options = cats_df["name"].tolist() if not cats_df.empty else ["General Garage Equipment"]

        st.subheader("Add New Equipment")
        with st.form("add_equipment_form", clear_on_submit=True):
            col_e1, col_e2, col_e3 = st.columns([1, 2, 1])
            with col_e1:
                st.number_input("SI No (Auto)", value=next_si_no, disabled=True)
            with col_e2:
                eq_name = st.text_input("Equipment Name", placeholder="e.g. 2-Post Hydraulic Car Lift")
            with col_e3:
                eq_qty = st.number_input("Quantity (Qty)", min_value=1, value=1, step=1)
                
            col_e4, col_e5 = st.columns(2)
            with col_e4:
                req_type = st.radio("Requirement Type", options=["Mandatory", "Optional"], horizontal=True)
            with col_e5:
                category = st.selectbox("Category", options=category_options)

            submitted = st.form_submit_button("Save Equipment")
            if submitted:
                if not eq_name.strip():
                    st.error("Please enter equipment name.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO equipments (si_no, name, requirement_type, category, qty) VALUES (?, ?, ?, ?, ?)",
                            (next_si_no, eq_name.strip(), req_type, category, eq_qty)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Equipment '{eq_name}' (Qty: {eq_qty}) added with SI No: {next_si_no}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving equipment: {e}")

        st.divider()
        st.subheader("Existing Garage Equipments")
        conn = get_connection()
        equip_data = pd.read_sql_query("SELECT si_no as 'SI No', name as 'Name', qty as 'Qty', requirement_type as 'Requirement', category as 'Category', id FROM equipments ORDER BY si_no ASC", conn)
        conn.close()

        if not equip_data.empty:
            st.dataframe(equip_data.drop(columns=["id"]), use_container_width=True)
            
            with st.expander("🗑 Delete Equipment"):
                del_eq_id = st.selectbox(
                    "Select Equipment to Delete", 
                    options=equip_data["id"], 
                    format_func=lambda x: f"SI {equip_data[equip_data['id']==x]['SI No'].values[0]} - {equip_data[equip_data['id']==x]['Name'].values[0]}"
                )
                if st.button("Delete Selected Equipment", type="primary"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM equipments WHERE id = ?", (del_eq_id,))
                    cur.execute("DELETE FROM supplier_prices WHERE equipment_id = ?", (del_eq_id,))
                    conn.commit()
                    conn.close()
                    st.success("Equipment deleted successfully!")
                    st.rerun()

    with tab3:
        st.subheader("Manage Garage Categories")
        st.caption("Add and manage custom equipment categories for your car garage planning.")
        
        col_c1, col_c2 = st.columns([1, 1])

        with col_c1:
            st.markdown("##### Add New Category")
            with st.form("add_category_form", clear_on_submit=True):
                new_cat_name = st.text_input("Category Name", placeholder="e.g. EV Battery Servicing Tools")
                cat_submitted = st.form_submit_button("Add Category")
                if cat_submitted:
                    if not new_cat_name.strip():
                        st.warning("Please enter a category name.")
                    else:
                        try:
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute("INSERT INTO categories (name) VALUES (?)", (new_cat_name.strip(),))
                            conn.commit()
                            conn.close()
                            st.success(f"Category '{new_cat_name}' added!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Category '{new_cat_name}' already exists.")

        with col_c2:
            st.markdown("##### Existing Categories")
            conn = get_connection()
            all_cats = pd.read_sql_query("SELECT id, name FROM categories ORDER BY name ASC", conn)
            conn.close()

            if not all_cats.empty:
                st.dataframe(all_cats[["name"]].rename(columns={"name": "Category Name"}), use_container_width=True)
                
                with st.expander("🗑️ Delete Category"):
                    del_cat_id = st.selectbox(
                        "Select Category to Delete", 
                        options=all_cats["id"], 
                        format_func=lambda x: all_cats[all_cats['id']==x]['name'].values[0],
                        key="sel_del_cat"
                    )
                    if st.button("Delete Selected Category", type="primary", key="btn_del_cat"):
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM categories WHERE id = ?", (del_cat_id,))
                        conn.commit()
                        conn.close()
                        st.success("Category deleted successfully!")
                        st.rerun()

    with tab4:
        col_sup1, col_sup2 = st.columns([1, 1])

        with col_sup1:
            st.subheader("1. Add / Delete Suppliers")
            with st.form("add_supplier_form", clear_on_submit=True):
                s_name = st.text_input("Supplier Name", placeholder="e.g. Bosch Garage Tools, ATS Elgi")
                sup_submitted = st.form_submit_button("Add Supplier")
                if sup_submitted:
                    if not s_name.strip():
                        st.warning("Please enter supplier name.")
                    else:
                        try:
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute("INSERT INTO suppliers (name) VALUES (?)", (s_name.strip(),))
                            conn.commit()
                            conn.close()
                            st.success(f"Supplier '{s_name}' added!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Supplier '{s_name}' already exists.")

            conn = get_connection()
            existing_sups = pd.read_sql_query("SELECT id, name FROM suppliers ORDER BY name ASC", conn)
            conn.close()

            if not existing_sups.empty:
                st.write("")
                st.dataframe(existing_sups[["name"]].rename(columns={"name": "Supplier Name"}), use_container_width=True)
                with st.expander("🗑️ Delete Supplier"):
                    del_sup_id = st.selectbox(
                        "Select Supplier to Delete",
                        options=existing_sups["id"],
                        format_func=lambda x: existing_sups[existing_sups['id']==x]['name'].values[0],
                        key="sel_del_sup"
                    )
                    if st.button("Delete Selected Supplier", type="primary", key="btn_del_sup"):
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM suppliers WHERE id = ?", (del_sup_id,))
                        cur.execute("DELETE FROM supplier_prices WHERE supplier_id = ?", (del_sup_id,))
                        conn.commit()
                        conn.close()
                        st.success("Supplier and associated price quotes deleted successfully!")
                        st.rerun()

        with col_sup2:
            st.subheader("2. Record / Update Price Quote (₹)")
            conn = get_connection()
            eqs = pd.read_sql_query("SELECT id, si_no, name FROM equipments ORDER BY si_no ASC", conn)
            sups = pd.read_sql_query("SELECT id, name FROM suppliers ORDER BY name ASC", conn)
            conn.close()

            if eqs.empty or sups.empty:
                st.info("Please make sure you have added at least one equipment and one supplier first.")
            else:
                with st.form("add_price_form"):
                    sel_eq_id = st.selectbox(
                        "Select Equipment", 
                        options=eqs["id"], 
                        format_func=lambda x: f"SI {eqs[eqs['id']==x]['si_no'].values[0]} - {eqs[eqs['id']==x]['name'].values[0]}"
                    )
                    sel_sup_id = st.selectbox(
                        "Select Supplier", 
                        options=sups["id"], 
                        format_func=lambda x: sups[sups['id']==x]['name'].values[0]
                    )
                    price_val = st.number_input("Quoted Price (₹ in Rupees)", min_value=0.0, step=500.0, format="%.2f")

                    price_submitted = st.form_submit_button("Save Price Quote")
                    if price_submitted:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO supplier_prices (equipment_id, supplier_id, price)
                            VALUES (?, ?, ?)
                            ON CONFLICT(equipment_id, supplier_id) DO UPDATE SET price=excluded.price
                        """, (sel_eq_id, sel_sup_id, price_val))
                        conn.commit()
                        conn.close()
                        st.success("Price quote recorded in Rupees (₹)!")
                        st.rerun()