import streamlit as st
import sqlite3
import pandas as pd
import time
import io

st.set_page_config(page_title='Batch Manager', layout='centered')

st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        position: fixed; bottom: 80px; right: 30px; 
        border-radius: 50%; width: 60px; height: 60px;
        font-size: 30px; 
        background-color: #4CAF50;  /* Perfect Green */
        color: white;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        z-index: 9999;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover { 
        background-color: #45a049;
        transform: scale(1.1);
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    conn = sqlite3.connect('my_batches.db')
    query = """
        SELECT batches.id, batches.batch_name, batches.amount, 
               categories.name as Category, batches.date, batches.class_grade
        FROM batches
        JOIN categories ON batches.category_id = categories.id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    df = df.rename(columns={
        "batch_name": "Batch Name", "amount": "Price",
        "date": "Date", "class_grade": "Class"
    })
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

def add_new_batch(batch_name, category_id, amount, batch_date, batch_class_grade):
    try:
        conn = sqlite3.connect("my_batches.db")
        cursor = conn.cursor()
        query = "INSERT INTO batches (batch_name, category_id, amount, date, class_grade) VALUES (?,?,?,?,?)"
        cursor.execute(query, (batch_name, category_id, amount, batch_date, batch_class_grade))
        conn.commit(); conn.close()
        return True
    except:
        return False

def del_batches(batch_id):
    try:
        conn = sqlite3.connect('my_batches.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
        conn.commit(); conn.close()
        return True
    except:
        return False

def update_batch_details(batch_id, new_name, new_price, new_date, new_grade):
    try:
        conn = sqlite3.connect('my_batches.db')
        cursor = conn.cursor()
        query = """
            UPDATE batches 
            SET batch_name = ?, amount = ?, date = ?, class_grade = ?
            WHERE id = ?
        """
        cursor.execute(query, (new_name, new_price, new_date, new_grade, batch_id))
        conn.commit(); conn.close()
        return True
    except:
        return False

def search_batches(df, search_query):
    if not search_query:
        return df
    search_query = str(search_query).lower()
    match_name = df['Batch Name'].str.lower().str.contains(search_query, na=False)
    match_id = df['id'].astype(str).str.contains(search_query, na=False)
    return df[match_name | match_id]

def user_authentication():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['role'] = None

    if st.session_state['logged_in']:
        current_role = st.session_state.get('role', 'Unknown')
        st.sidebar.info(f"👤 Logged in as: {current_role.capitalize()}")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.rerun()
    else:
        col1, col2, col3 = st.columns([1, 2, 1]) 
        
        with col2:
            st.markdown("### 🔐 Admin Login")
            with st.form("login_form", border=True):
                u_name = st.text_input("Username")
                p_word = st.text_input("Password", type="password")
                
                users = {
                    "admin": {"pass": "bhopal123", "role": "admin"},
                    "guest": {"pass": "guest123", "role": "viewer"},
                    "manager": {"pass": "m123", "role": "manager"},
                    "intern": {"pass": "intern123", "role": "viewer"}
                }
                
                if st.form_submit_button("Access Dashboard", use_container_width=True, type="primary"):
                    if u_name in users and p_word == users[u_name]["pass"]:
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = users[u_name]["role"]
                        st.success("✅ Welcome Back!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password")
        st.stop()
        
def convert_df_to_excel(df):
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    processed_data = output.getvalue()
    return processed_data
    
@st.dialog("➕ Add New Batch")
def show_add_batch_form():
    with st.form("add_batch_popup"):
        new_name = st.text_input("Name")
        new_price = st.number_input("Price", step=500)
        cat_map = {"NEET": 1, "JEE": 2, "FOUNDATION": 3, "SSC": 4}
        sel_cat = st.selectbox("Category", list(cat_map.keys()))
        new_date = st.date_input("Date")
        new_grade = st.text_input("Class/Grade")
        
        if st.form_submit_button("Save Batch"):
            if add_new_batch(new_name, cat_map[sel_cat], new_price, str(new_date), new_grade):
                st.success("✅ Added Successfully!")
                time.sleep(1)
                st.rerun()

@st.dialog("✏️ Update Batch Details")
def show_edit_batch_form(target_id, current_data):
    with st.form("edit_batch_popup"):
        edit_name = st.text_input("Batch Name", value=current_data['Batch Name'])
        edit_price = st.number_input("Price (₹)", value=int(current_data['Price']), step=500)
        current_date_obj = pd.to_datetime(current_data['Date'])
        edit_date = st.date_input("Start Date", value=current_date_obj)
        edit_grade = st.text_input("Class", value=current_data['Class'])
        
        if st.form_submit_button("💾 Save Changes"):
            update_batch_details(target_id, edit_name, edit_price, str(edit_date), edit_grade)
            st.success("✅ Updated Successfully!")
            time.sleep(1)
            st.rerun()

st.title('🎓 Batch Management System')

user_authentication()

if st.button("➕", type="primary"):
    show_add_batch_form()

try:
    df = load_data()
except Exception as e:
    st.error(f"Database Error: {e}")
    df = pd.DataFrame()

if not df.empty:
    
    st.sidebar.header("⚙️ Manage Batches")
    
    with st.sidebar.expander("✏️ Edit Batch"):
        update_map = {row['Batch Name']: row['id'] for i, row in df.iterrows()}
        selected_update_name = st.selectbox("Select to Edit", list(update_map.keys()))
        if st.button("Open Edit Form ↗️"):
            target_id = update_map[selected_update_name]
            show_edit_batch_form(target_id, df[df['id'] == target_id].iloc[0]) 
            
    allowed_to_delete = ['admin', 'manager']
    if st.session_state.get('role') in allowed_to_delete:
        with st.sidebar.expander("🗑️ Delete Batch"):
            del_map = {row['Batch Name']: row['id'] for i, row in df.iterrows()}
            selected_del_name = st.selectbox("Select to Delete", list(del_map.keys()))
        
            with st.expander(f"🗑️ Delete '{selected_del_name}'?", expanded=False):
                st.error("⚠️ Are you sure you want to Delete it ?")
                
                if st.button("Yes, Delete 🚨"): 
                    del_batches(del_map[selected_del_name])
                    st.success("Deleted!")
                    time.sleep(1)
                    st.rerun()

    st.divider()
    
    search_text = st.text_input("🔍 Search Batches", placeholder="Type Batch Name or ID here...")
    searched_df = search_batches(df, search_text)
    
    col1, col2 = st.columns(2)
    with col1:
        avail_cat = searched_df['Category'].unique().tolist()
        uni_cat = ['All Categories'] + avail_cat
        sel_cat = st.selectbox("📂 Filter by Category", uni_cat)
        
    with col2:
        if sel_cat == 'All Categories':
            avail_classes = searched_df['Class'].unique().tolist()
        else:
            avail_classes = searched_df[searched_df['Category'] == sel_cat]['Class'].unique().tolist()
        uni_class = ['All Classes'] + avail_classes
        sel_class = st.selectbox("🎓 Filter by Class/Grade", uni_class)

    filt_df = searched_df.copy() 
    if sel_cat != 'All Categories':
        filt_df = filt_df[filt_df['Category'] == sel_cat]
    if sel_class != 'All Classes':
        filt_df = filt_df[filt_df['Class'] == sel_class]

    st.subheader("📋 Dashboard Overview")
    m1, m2 = st.columns(2)
    m1.metric("Total Batches Found", len(filt_df))
    m2.metric("Total Revenue", f"₹{filt_df['Price'].sum():,.0f}")

    st.subheader("📊 Data Validation")

    show_missing_only = st.checkbox("⚠️ Batches With 'Missing Details'")

    if show_missing_only:
        missing_filter = (
            df['Class'].isna() | (df['Class'] == 'None') | (df['Class'] == '') |
            df['Price'].isna() | (df['Price'] == 'None') | (df['Price'] == '')
        )
        
        filtered_df = df[missing_filter]
        
        if filtered_df.empty:
            st.success("Great! All batches have complete data.")
            st.dataframe(df)
        else:
            st.warning(f"Warning: {len(filtered_df)} batches have missing details!")
            st.dataframe(filtered_df)
    else:
        st.dataframe(filt_df.drop(columns=['id']), use_container_width=True, hide_index=True)

    st.subheader("📈 Performance Analytics")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        if sel_cat == "All Categories":
            st.caption("💰 Revenue By Category")
            st.bar_chart(filt_df.groupby('Category')['Price'].sum())
        else:
            st.caption(f"💰 Revenue by Batch ({sel_cat})")
            st.bar_chart(filt_df.set_index('Batch Name')['Price'])
            
    excel_data = convert_df_to_excel(filt_df)
    
    st.download_button(
        label="📥 Download Filtered Data as Excel",
        data=excel_data,
        file_name='batch_report.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
            
    with chart_col2:
        st.caption("🎓 Revenue By Class/Grade")
        class_revenue = filt_df.groupby('Class')['Price'].sum()
        
        if not class_revenue.empty:
            st.bar_chart(class_revenue)
        else:
            st.info("No class data available for this filter.")






