import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid

# ---------- সেটআপ ----------
st.set_page_config(page_title="তথ্য খাতা", page_icon="📒", layout="centered")
SHEET_NAME = "তথ্য খাতা"   # আপনার Google Sheet-এর নাম (secrets-এ না দিলে এটাই ব্যবহার হবে)
HEADERS = ["id", "name", "mobile", "address", "notes", "created_at"]

@st.cache_resource
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet_name = st.secrets.get("sheet_name", SHEET_NAME)
    sh = client.open(sheet_name).sheet1
    if sh.row_values(1) != HEADERS:
        sh.clear()
        sh.append_row(HEADERS)
    return sh

sheet = get_sheet()

def load_records():
    rows = sheet.get_all_records()
    rows.reverse()  # নতুনগুলো আগে
    return rows

def add_record(name, mobile, address, notes):
    sheet.append_row([
        str(uuid.uuid4()), name, mobile, address, notes,
        datetime.now().isoformat(),
    ])

def delete_record(rid):
    cell = sheet.find(rid)
    if cell:
        sheet.delete_rows(cell.row)

# ---------- ডার্ক থিম CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #1a1a1a; color: #e8e8e8; }
    div[data-testid="stExpander"] {
        background-color: #242424;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #2a2a2a;
        color: #e8e8e8;
        border: 1px solid #3a3a3a;
    }
    .record-card {
        background-color: #242424;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .record-name { font-size: 16px; font-weight: 600; color: #f0f0f0; }
    .record-meta { font-size: 13px; color: #999; margin-top: 4px; }
    .stButton button { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

st.title("📒তথ্য খাতা")

# ---------- নতুন এন্ট্রি ----------
with st.expander("➕ নতুন এন্ট্রি যোগ করুন"):
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("নাম")
        mobile = st.text_input("মোবাইল নম্বর")
        address = st.text_input("ঠিকানা")
        notes = st.text_area("মন্তব্য (ঐচ্ছিক)")
        submitted = st.form_submit_button("সংরক্ষণ করুন")

        if submitted:
            if not name.strip() and not mobile.strip():
                st.error("অন্তত নাম অথবা মোবাইল নম্বর দিন।")
            else:
                add_record(name.strip(), mobile.strip(), address.strip(), notes.strip())
                st.success("সংরক্ষিত হয়েছে।")
                st.rerun()

# ---------- সার্চ ও তালিকা ----------
query = st.text_input("🔍 নাম, মোবাইল বা ঠিকানা দিয়ে খুঁজুন")

try:
    records = load_records()
except Exception as e:
    st.error(f"Google Sheet থেকে ডেটা আনতে সমস্যা হয়েছে: {e}")
    records = []

if query.strip():
    q = query.strip().lower()
    records = [
        r for r in records
        if q in " ".join(str(r.get(k, "")) for k in ["name", "mobile", "address", "notes"]).lower()
    ]

st.markdown(f"**মোট এন্ট্রি: {len(records)}**")

if not records:
    st.info("কোনো এন্ট্রি পাওয়া যায়নি।")

for r in records:
    with st.container():
        st.markdown(f"""
        <div class="record-card">
            <div class="record-name">{r.get('name') or '(নাম নেই)'}</div>
            <div class="record-meta">📞 {r.get('mobile') or '-'} &nbsp;&nbsp; 📍 {r.get('address') or '-'}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("বিস্তারিত দেখুন / মুছুন"):
            if r.get("notes"):
                st.write(f"**মন্তব্য:** {r['notes']}")
            try:
                dt = datetime.fromisoformat(r["created_at"]).strftime("%d %b, %Y")
            except Exception:
                dt = r.get("created_at", "")
            st.caption(f"যোগ করা হয়েছে: {dt}")
            if st.button("🗑️ মুছে ফেলুন", key=f"del_{r['id']}"):
                delete_record(r["id"])
                st.rerun()
