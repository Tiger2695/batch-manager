import streamlit as st
import pandas as pd
import time
import io
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURATION & CSS (Styling)
# ========================================== 
st.set_page_config(page_title='Batch Manager', layout='centered')

st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        position: fixed; bottom: 30px; right: 30px; 
        border-radius: 50%; width: 60px; height: 60px;
        font-size: 30px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        z-index: 9999;
    }
    div.stButton > button[kind="primary"]:hover { transform: scale(1.1); }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. DATABASE FUNCTIONS (Backend)
# ==========================================

conn = st.connection("gsheets", type=GSheetsConnection)
def load_data():
    """Google Sheet se fresh data lana"""
    # ttl=0 matlab cache mat karo, hamesha live data lao
    sheet_url = "https://docs.google.com/spreadsheets/d/18zymh_fCP9MUng5reeMhh7-HHR-tdu-cGiR-E9_TQ1c/edit?usp=sharing" # Agar secrets mein nahi hai toh
    df = conn.read(spreadsheet=sheet_url, ttl=0)
    df = df.dropna(how="all")
    
    # Columns ko rename kar do taaki tumhara purana Search wala code chale
    df = df.rename(columns={
        "batch_name": "Batch Name", 
        "amount": "Price",
        "category": "Category",
        "date": "Date",
        "class_grade": "Class"
    })

def add_new_batch(batch_name, category_id, amount, batch_date, batch_class_grade):
    """Nayi row Google Sheet mein jodne ke liye"""
    try:
        existing_df = load_data()
        # Naya data purane data ke niche lagana
        updated_df = pd.concat([existing_df, pd.DataFrame([new_row_list])], ignore_index=True)
        # Sheet par wapas bhejna
        conn.update(data=updated_df)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def del_batches(batch_id):
    try:
        # 1. Fresh data lao
        df = load_data()
        
        # 2. Sirf wo rows rakho jinki ID match NAHI karti (Matlab target id ud gayi)
        # Humne 'id' column ko string mein convert kiya hai safe side ke liye
        df = df[df['id'].astype(str) != str(batch_id)]
        
        # 3. Baaki bacha hua data Sheet par wapas bhej do
        conn.update(data=df)
        return True
    except Exception as e:
        st.error(f"Delete Error: {e}")
        return False

def update_batch_details(batch_id, new_name, new_price, new_date, new_grade):
    try:
        # 1. Fresh data lao
        df = load_data()
        
        # 2. Check karo ki wo ID table mein kahan hai (Index dhoondo)
        mask = df['id'].astype(str) == str(batch_id)
        
        # 3. Us specific jagah par naya data bhar do (.loc use karke)
        df.loc[mask, 'batch_name'] = new_name
        df.loc[mask, 'amount'] = new_price
        df.loc[mask, 'date'] = str(new_date)
        df.loc[mask, 'class_grade'] = new_grade
        
        # 4. Poora Updated Table wapas Sheet par upload kar do
        conn.update(data=df)
        return True
    except Exception as e:
        st.error(f"Update Error: {e}")
        return False

def search_batches(df, search_query):
    if not search_query:
        return df
    search_query = str(search_query).lower()
    match_name = df['Batch Name'].str.lower().str.contains(search_query, na=False)
    match_id = df['id'].astype(str).str.contains(search_query, na=False)
    return df[match_name | match_id]


# Login and Logout
def user_authentication():
    # 1. Memory check (Diary)
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    # 2. Agar Login hai, toh Sidebar mein Logout dikhao
    if st.session_state['logged_in']:
        st.sidebar.info(f"👤 Logged in as: Admin")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
    # 3. Agar Login nahi hai, toh Screen par Parda (Login Form) gira do
    else:
        # Page ke beech mein form lane ke liye columns ka use
        col1, col2, col3 = st.columns([1, 2, 1]) 
        
        with col2:
            st.markdown("### 🔐 Admin Login")
            with st.container(border=True):
                u_name = st.text_input("Username")
                p_word = st.text_input("Password", type="password")
                
                # --- YE RAHI TUMHARI CHABHI (Credentials) ---
                MY_USER = "admin"    # <--- Isko change kar sakte ho
                MY_PASS = "bhopal123" # <--- Isko change kar sakte ho
                
                if st.button("Access Dashboard", use_container_width=True, type="primary"):
                    if u_name == MY_USER and p_word == MY_PASS:
                        st.session_state['logged_in'] = True
                        st.success("✅ Welcome Back!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password")
        
        # SABSE JAROORI: Jab tak login nahi, tab tak neeche ka code mat chalao
        st.stop()
        
def convert_df_to_excel(df):
    # 1. Memory mein ek khali jagah banao (Buffer)
    output = io.BytesIO()
    
    # 2. Pandas ko bolo ki is memory mein Excel file likh de
    # index=False matlab humein row numbers (0, 1, 2) nahi chahiye Excel mein
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    # 3. File ko tayyar karke wapas bhej do
    processed_data = output.getvalue()
    return processed_data
        
# ==========================================
# 3. POPUP FORMS (Modals)
# ==========================================

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


# ==========================================
# 4. MAIN UI & DASHBOARD
# ==========================================

st.title('🎓 Batch Management System')

# 1. Sabse pehle Security Checkpost (Login Function) call karo
user_authentication()

# ---------------------------------------------------------
# 💡 AGAR CODE YAHAN TAK PAHUNCH GAYA HAI...
# Iska matlab hai ki user login ho chuka hai (st.stop() nahi chala)
# ---------------------------------------------------------
    
# ------------------------------------------------------    
# --- CREATE BATCH FLOATING BUTTON ---
# ------------------------------------------------------

if st.button("➕", type="primary"):
    show_add_batch_form()

# --- LOAD DATA ---
try:
    df = load_data()
except Exception as e:
    st.error(f"Database Error: {e}")
    df = pd.DataFrame()

if not df.empty:
    
    # --- SIDEBAR (Edit & Delete) ---
    st.sidebar.header("⚙️ Manage Batches")
    
    with st.sidebar.expander("✏️ Edit Batch"):
        update_map = {row['Batch Name']: row['id'] for i, row in df.iterrows()}
        selected_update_name = st.selectbox("Select to Edit", list(update_map.keys()))
        if st.button("Open Edit Form ↗️"):
            target_id = update_map[selected_update_name]
            show_edit_batch_form(target_id, df[df['id'] == target_id].iloc[0]) 
            
    with st.sidebar.expander("🗑️ Delete Batch"):
        # del_map = {}
        #    for i, row in df.iterrows():      # i=0, row=1st row
        #    del_map[row['Batch Name']] = row['id']  # "Python": 1
           
        del_map = {row['Batch Name']: row['id'] for i, row in df.iterrows()}
        selected_del_name = st.selectbox("Select to Delete", list(del_map.keys()))
        with st.expander(f"🗑️ Delete '{selected_del_name}'?", expanded=False):
            st.error("⚠️ Are you sure  you want to Delete it ?")
            if st.button("Yes, Delete 🚨"): 
                del_batches(del_map[selected_del_name])
                st.success("Deleted!")
                time.sleep(1)
                st.rerun()
# ------------------------------------------------------
    # --- 🔍 SEARCH & FILTERS PIPELINE ---
# ------------------------------------------------------
    st.divider()
    
    # Step 1: SEARCH BAR
    search_text = st.text_input("🔍 Search Batches", placeholder="Type Batch Name or ID here...")
    searched_df = search_batches(df, search_text)
    
    # Step 2: DUAL FILTERS
    col1, col2 = st.columns(2)
    with col1:
        uni_cat = ['All Categories'] + searched_df['Category'].unique().tolist()
        sel_cat = st.selectbox("📂 Filter by Category", uni_cat)
        
    with col2:
        if sel_cat == 'All Categories':
            avail_classes = searched_df['Class'].unique().tolist()
        else:
            avail_classes = searched_df[searched_df['Category'] == sel_cat]['Class'].unique().tolist()
        uni_class = ['All Classes'] + avail_classes
        sel_class = st.selectbox("🎓 Filter by Class/Grade", uni_class)

    # Step 3: APPLY FILTERS ON SEARCHED DATA
    filt_df = searched_df.copy() 
    if sel_cat != 'All Categories':
        filt_df = filt_df[filt_df['Category'] == sel_cat]
    if sel_class != 'All Classes':
        filt_df = filt_df[filt_df['Class'] == sel_class]


    # --- 📊 DISPLAY RESULTS ---
    # Metrics
    st.subheader("📋 Dashboard Overview")
    m1, m2 = st.columns(2)
    m1.metric("Total Batches Found", len(filt_df))
    m2.metric("Total Revenue", f"₹{filt_df['Price'].sum():,.0f}")

    # Table
    st.dataframe(filt_df.drop(columns=['id']), use_container_width=True, hide_index=True)

    # Charts
    st.subheader("📈 Performance Analytics")
    chart_col1, chart_col2 = st.columns(2)
    
    # CHART 1: Category ya Batch Name ke hisaab se (Purana wala)
    with chart_col1:
        if sel_cat == "All Categories":
            st.caption("💰 Revenue By Category")
            st.bar_chart(filt_df.groupby('Category')['Price'].sum())
        else:
            st.caption(f"💰 Revenue by Batch ({sel_cat})")
            st.bar_chart(filt_df.set_index('Batch Name')['Price'])
            
    # Dashboard ke Metrics ke neeche...
    st.subheader("📋 Dashboard Overview")
    
    # Excel Download Logic
    excel_data = convert_df_to_excel(filt_df) # Filter kiya hua data convert karo
    
    st.download_button(
        label="📥 Download Filtered Data as Excel",
        data=excel_data,
        file_name='batch_report.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
            
    # CHART 2: Class/Grade ke hisaab se (Tumhara Naya Idea!)
    with chart_col2:
        st.caption("🎓 Revenue By Class/Grade")
        # Ye line jaadu karegi: Class ke hisaab se total revenue nikalegi
        class_revenue = filt_df.groupby('Class')['Price'].sum()
        
        # Ek chota check: Agar data hai tabhi chart dikhao, warna khali box ajeeb lagega
        if not class_revenue.empty:
            st.bar_chart(class_revenue)
        else:

            st.info("No class data available for this filter.")

