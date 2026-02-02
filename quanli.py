import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Misa Finance V76", page_icon="🏦", layout="centered")

# 🔥 ĐIỀN API VÀ EMAIL CỦA BẠN VÀO ĐÂY 🔥
GEMINI_API_KEY = "AIzaSyAaviiakNYZURaRLBEskwzhV4zqOmeO4n8" 
EMAIL_HOST_USER = "quynakroth2304@gmail.com"
EMAIL_HOST_PASSWORD = "spem mabh baxv eqyl" 

# --- 2. DATABASE NÂNG CẤP (HỖ TRỢ ĐA VÍ) ---
DB_FILE = "finance_v74.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Bảng User
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT, email TEXT)''')
    
    # Bảng Tài Khoản (Ví tiền/Ngân hàng) -> MỚI
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, name TEXT, type TEXT, balance INTEGER
    )''')
    
    # Bảng Giao dịch (Thêm cột account_id để biết trừ tiền ở đâu)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, account_name TEXT, date TEXT, type TEXT, amount INTEGER, category TEXT, note TEXT, ai_comment TEXT
    )''')
    conn.commit(); conn.close()

init_db()

# --- 3. HÀM EMAIL ---
def send_backup(target_email, reason):
    if "email_cua" in EMAIL_HOST_USER: return 
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER; msg['To'] = target_email
        msg['Subject'] = f"BACKUP V76: {reason}"
        msg.attach(MIMEText("Data backup.", 'plain'))
        with open(DB_FILE, "rb") as f:
            p = MIMEBase('application', 'octet-stream'); p.set_payload(f.read())
            encoders.encode_base64(p); p.add_header('Content-Disposition', f"attachment; filename={DB_FILE}")
            msg.attach(p)
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls()
        s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD); s.sendmail(EMAIL_HOST_USER, target_email, msg.as_string()); s.quit()
    except: pass

# --- 4. HÀM AI ---
def get_ai_advice(amount, category, note, persona, total_asset):
    if "API_KEY" in GEMINI_API_KEY or not GEMINI_API_KEY: return "Chưa nhập API Key! 🤖"
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompts = {
            "Cục súc": f"User tiêu {amount}đ cho {category} ({note}). Tổng tài sản còn {total_asset}đ. Bạn là AI cục súc. Chửi nó vì nghèo mà hoang. <40 từ.",
            "Nhẹ nhàng": f"User tiêu {amount}đ cho {category} ({note}). Tổng tài sản {total_asset}đ. Bạn là Misa cute. Khuyên nhẹ nhàng. <40 từ.",
            "Nghiêm túc": f"Phân tích khoản chi: {amount}đ ({category}). Hợp lý không?"
        }
        return model.generate_content(prompts.get(persona, prompts["Nhẹ nhàng"])).text
    except: return "AI đang bận..."

# --- 5. CSS GLASS UI (GIỮ NGUYÊN VÌ QUÁ ĐẸP) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); font-family: 'Poppins', sans-serif; }
    [data-testid="stHeader"] { display: none; }
    
    /* ANIMATION */
    @keyframes slideUp { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
    @keyframes float { 0% {transform: translateY(0px);} 50% {transform: translateY(-10px);} 100% {transform: translateY(0px);} }

    /* CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px);
        border-radius: 20px; border: 1px solid rgba(255,255,255,0.8);
        padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.05); margin-bottom: 15px;
        animation: slideUp 0.5s ease-out;
    }
    
    /* BANK CARD STYLE */
    .bank-card {
        background: linear-gradient(45deg, #0984e3, #74b9ff); color: white;
        border-radius: 15px; padding: 15px; margin-right: 10px; min-width: 140px;
        box-shadow: 0 4px 15px rgba(9, 132, 227, 0.3); text-align: center;
        display: inline-block; vertical-align: top;
    }
    .bank-card.cash { background: linear-gradient(45deg, #00b894, #55efc4); box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3); }
    
    .total-asset { 
        font-size: 36px; font-weight: 800; 
        background: linear-gradient(to right, #2d3436, #000); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* INPUTS */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        border-radius: 12px !important; border: 1px solid #ddd !important; background: white !important;
    }
    .stButton button {
        background: #6c5ce7 !important; color: white !important; border-radius: 12px !important; font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. LOGIC CHÍNH ---
if 'user' not in st.session_state: st.session_state.user = None

# === MÀN HÌNH LOGIN ===
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:#6c5ce7'>MISA ASSET V76</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["ĐĂNG NHẬP", "TẠO TÀI KHOẢN", "KHÔI PHỤC"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Username"); p = st.text_input("Password", type="password")
                if st.form_submit_button("LOGIN"):
                    conn = sqlite3.connect(DB_FILE)
                    row = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
                    conn.close()
                    if row:
                        st.session_state.user = row[0]; st.session_state.name = row[2]; st.session_state.email = row[3]
                        st.rerun()
                    else: st.error("Sai rồi!")

        with tab2:
            with st.form("reg"):
                ru = st.text_input("Username mới"); rn = st.text_input("Tên hiển thị"); re = st.text_input("Email"); rp = st.text_input("Password", type="password")
                st.markdown("---")
                st.markdown("**💰 Thiết lập tài sản ban đầu:**")
                cash_init = st.number_input("Tiền mặt đang có (VNĐ)", step=50000, value=0)
                bank_name = st.text_input("Tên Ngân hàng chính (VD: MBBank, VCB)", "MBBank")
                bank_init = st.number_input("Số dư ngân hàng (VNĐ)", step=50000, value=0)
                
                if st.form_submit_button("ĐĂNG KÝ NGAY"):
                    if ru and rp:
                        try:
                            conn = sqlite3.connect(DB_FILE)
                            # 1. Tạo User
                            conn.execute("INSERT INTO users VALUES (?,?,?,?)", (ru, rp, rn, re))
                            # 2. Tạo ví Tiền mặt
                            conn.execute("INSERT INTO accounts (username, name, type, balance) VALUES (?,?,?,?)", (ru, "Tiền mặt", "cash", cash_init))
                            # 3. Tạo ví Ngân hàng (nếu có tiền)
                            if bank_init > 0 or bank_name:
                                conn.execute("INSERT INTO accounts (username, name, type, balance) VALUES (?,?,?,?)", (ru, bank_name, "bank", bank_init))
                            conn.commit(); conn.close()
                            st.success("Tạo xong! Mời đăng nhập."); st.balloons()
                        except: st.error("Tên đăng nhập trùng!")
        
        with tab3:
            up = st.file_uploader("Upload file .db", type="db")
            if up:
                with open(DB_FILE, "wb") as f: f.write(up.getbuffer())
                st.success("Xong! Đăng nhập đi."); time.sleep(1); st.rerun()

# === MÀN HÌNH DASHBOARD ===
else:
    me = st.session_state.user
    conn = sqlite3.connect(DB_FILE)
    
    # Lấy danh sách ví
    accounts = pd.read_sql("SELECT * FROM accounts WHERE username=?", conn, params=(me,))
    total_asset = accounts['balance'].sum() if not accounts.empty else 0
    
    # Lấy lịch sử
    history = pd.read_sql("SELECT * FROM transactions WHERE username=? ORDER BY id DESC LIMIT 10", conn, params=(me,))
    conn.close()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.name}")
        persona = st.radio("Bot tính cách:", ["Nhẹ nhàng", "Cục súc", "Nghiêm túc"])
        
        st.markdown("---")
        st.subheader("➕ Thêm Ngân Hàng Mới")
        with st.form("add_bank"):
            new_b_name = st.text_input("Tên (VD: TPBank)")
            new_b_bal = st.number_input("Số dư hiện tại", min_value=0)
            if st.form_submit_button("Thêm ví"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO accounts (username, name, type, balance) VALUES (?,?,?,?)", (me, new_b_name, "bank", new_b_bal))
                conn.commit(); conn.close(); st.rerun()
                
        if st.button("Đăng xuất"): st.session_state.user = None; st.rerun()
        if st.button("Backup Email"): send_backup(st.session_state.email, "Manual"); st.success("Sent!")

    # --- HEADER & MASCOT ---
    if 'ai_msg' not in st.session_state: st.session_state.ai_msg = f"Chào {st.session_state.name}! Tổng tài sản: {total_asset:,}đ 🤑"
    
    st.markdown(f"""
    <div style="text-align:center; animation: float 3s infinite ease-in-out;">
        <div style="background:white; padding:10px 20px; border-radius:15px; display:inline-block; box-shadow:0 5px 15px rgba(0,0,0,0.1); margin-bottom:10px;">
            {st.session_state.ai_msg}
        </div><br>
        <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" width="100">
    </div>
    """, unsafe_allow_html=True)

    # --- TOTAL ASSET CARD ---
    st.markdown(f"""
    <div class="glass-card" style="text-align:center">
        <div style="font-size:12px; color:#888; font-weight:bold; letter-spacing:1px">TỔNG TÀI SẢN RÒNG</div>
        <div class="total-asset">{total_asset:,.0f}đ</div>
    </div>
    """, unsafe_allow_html=True)

    # --- DANH SÁCH VÍ (SCROLL NGANG) ---
    st.markdown("**💳 Ví của bạn:**")
    cols = st.columns(len(accounts))
    for i, row in accounts.iterrows():
        tk_type = "cash" if row['type'] == 'cash' else "bank"
        icon = "💵" if row['type'] == 'cash' else "🏦"
        st.markdown(f"""
        <div class="bank-card {tk_type}">
            <div style="font-size:20px">{icon}</div>
            <div style="font-weight:bold; font-size:14px">{row['name']}</div>
            <div style="font-size:16px; font-weight:800; margin-top:5px">{row['balance']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- GHI GIAO DỊCH ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 GHI GIAO DỊCH MỚI", expanded=True):
        with st.form("tx_form"):
            col1, col2 = st.columns(2)
            t_type = col1.selectbox("Loại", ["Chi tiền", "Thu tiền"])
            
            # Chọn ví để trừ/cộng tiền
            acc_names = accounts['name'].tolist()
            t_acc = col2.selectbox("Nguồn tiền (Ví/Bank)", acc_names)
            
            t_amt = st.number_input("Số tiền", step=1000, min_value=0)
            t_cat = st.text_input("Nội dung", "Ăn uống")
            t_note = st.text_input("Ghi chú", "")
            
            if st.form_submit_button("LƯU GIAO DỊCH"):
                if t_amt > 0:
                    conn = sqlite3.connect(DB_FILE)
                    
                    # 1. Cập nhật số dư ví
                    curr_bal = accounts[accounts['name']==t_acc]['balance'].values[0]
                    new_bal = curr_bal - t_amt if t_type == "Chi tiền" else curr_bal + t_amt
                    conn.execute("UPDATE accounts SET balance=? WHERE username=? AND name=?", (new_bal, me, t_acc))
                    
                    # 2. Lưu lịch sử
                    conn.execute("INSERT INTO transactions (username, account_name, date, type, amount, category, note, ai_comment) VALUES (?,?,?,?,?,?,?,?)",
                                (me, t_acc, datetime.now().strftime('%Y-%m-%d %H:%M'), t_type, t_amt, t_cat, t_note, ""))
                    conn.commit(); conn.close()
                    
                    # 3. AI Phản hồi (Tính tổng tài sản mới)
                    new_total = total_asset - t_amt if t_type == "Chi tiền" else total_asset + t_amt
                    advice = get_ai_advice(t_amt, t_cat, t_note, persona, new_total)
                    st.session_state.ai_msg = advice
                    
                    send_backup(st.session_state.email, "New Transaction")
                    st.rerun()
                else: st.error("Nhập tiền đi bạn!")

    # --- LỊCH SỬ ---
    st.markdown("**🕒 Lịch sử gần đây:**")
    if not history.empty:
        for idx, row in history.iterrows():
            clr = "#ff7675" if row['type'] == "Chi tiền" else "#00b894"
            sign = "-" if row['type'] == "Chi tiền" else "+"
            st.markdown(f"""
            <div class="glass-card" style="padding:10px 15px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:bold; color:#333">{row['category']} <span style="font-size:11px; color:#888">({row['account_name']})</span></div>
                    <div style="font-size:11px; color:#aaa">{row['date']}</div>
                </div>
                <div style="font-weight:800; color:{clr}">{sign}{row['amount']:,}đ</div>
            </div>
            """, unsafe_allow_html=True)
    else: st.info("Chưa có giao dịch.")