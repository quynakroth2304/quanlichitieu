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

# --- 1. CẤU HÌNH (SỬA DÒNG NÀY ĐỂ CHẠY) ---
st.set_page_config(page_title="Misa Finance V74", page_icon="💸", layout="centered")

# 🔥 1. API KEY GEMINI (Lấy tại aistudio.google.com)
GEMINI_API_KEY = "AIzaSyAaviiakNYZURaRLBEskwzhV4zqOmeO4n8" 

# 🔥 2. CẤU HÌNH EMAIL GỬI BACKUP (Lấy mật khẩu ứng dụng Gmail)
EMAIL_HOST_USER = "quynakroth2304@gmail.com"
EMAIL_HOST_PASSWORD = "spem mabh baxv eqyl" 

# --- 2. DATABASE ---
DB_FILE = "finance_v74.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Bảng User (Thêm cột email để gửi backup)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, name TEXT, email TEXT
    )''')
    # Bảng Giao dịch (Thêm cột username để biết tiền của ai)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, type TEXT, amount INTEGER, category TEXT, note TEXT, ai_comment TEXT
    )''')
    conn.commit(); conn.close()

init_db()

# --- 3. HÀM GỬI EMAIL BACKUP ---
def send_backup(target_email, reason):
    if "email_cua" in EMAIL_HOST_USER: return # Chưa config email thì bỏ qua
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = target_email
        msg['Subject'] = f"BACKUP MISA: {reason} - {datetime.now().strftime('%d/%m %H:%M')}"
        
        body = "Dữ liệu chi tiêu mới nhất của bạn."
        msg.attach(MIMEText(body, 'plain'))
        
        with open(DB_FILE, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={DB_FILE}")
            msg.attach(part)
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, target_email, msg.as_string())
        server.quit()
        print("Backup sent!")
    except Exception as e: print(f"Err mail: {e}")

# --- 4. HÀM AI GEMINI ---
def get_ai_advice(amount, category, note, persona, balance):
    if "SỬA_" in GEMINI_API_KEY or not GEMINI_API_KEY: 
        return "Bạn chưa nhập API Key vào code kìa! 🤖"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompts = {
            "Cục súc": f"Bạn là AI quản lý tài chính cục súc, hay chửi thề (vừa phải). User vừa tiêu {amount}đ cho {category} ({note}). Số dư còn {balance}đ. Chửi nó vì nghèo mà hoang. Ngắn gọn (dưới 40 từ).",
            "Nhẹ nhàng": f"Bạn là em gái mưa tên Misa, cute. User tiêu {amount}đ cho {category} ({note}). Khuyên nhủ nhẹ nhàng, dùng icon. Ngắn gọn.",
            "Nghiêm túc": f"Phân tích tài chính ngắn gọn: {amount}đ cho {category}. Hợp lý không?"
        }
        res = model.generate_content(prompts.get(persona, prompts["Nhẹ nhàng"]))
        return res.text
    except Exception as e: return f"AI đang bận: {e}"

# --- 5. CSS MAGIC (GLASS UI V73) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); font-family: 'Poppins', sans-serif; }
    [data-testid="stHeader"] { display: none; }
    
    /* ANIMATIONS */
    @keyframes float { 0% {transform: translateY(0px);} 50% {transform: translateY(-15px);} 100% {transform: translateY(0px);} }
    @keyframes slideUp { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
    
    /* UI ELEMENTS */
    .mascot-area { text-align: center; padding: 20px 0; animation: slideUp 0.8s ease-out; }
    .robot-img { width: 140px; filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2)); animation: float 4s ease-in-out infinite; }
    
    .chat-bubble {
        background: white; border-radius: 20px; padding: 15px 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: inline-block; max-width: 90%;
        font-size: 14px; color: #444; font-weight: 600; margin-bottom: 15px; border-bottom-left-radius: 2px;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.5); padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1); margin-bottom: 20px; animation: slideUp 1s ease-out;
    }
    
    .net-money { 
        font-size: 38px; font-weight: 800; 
        background: linear-gradient(45deg, #00b09b, #96c93d); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        border-radius: 16px !important; border: none !important; background: #f1f2f6 !important;
    }
    .stButton button {
        background: linear-gradient(45deg, #6c5ce7, #a29bfe) !important; color: white !important;
        border-radius: 18px !important; padding: 15px !important; font-weight: 800 !important;
        box-shadow: 0 10px 20px rgba(108, 92, 231, 0.3);
    }
    
    .history-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }
    .cat-icon { width: 40px; height: 40px; background: #dfe6e9; border-radius: 50%; display:flex; align-items:center; justify-content:center; font-size:20px; margin-right: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 6. AUTH & SESSION ---
if 'user' not in st.session_state: st.session_state.user = None

# --- MÀN HÌNH LOGIN / REGISTER ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center; color:#6c5ce7'>MISA MONEY V74</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["ĐĂNG NHẬP", "TẠO VÍ MỚI"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Tên đăng nhập")
                p = st.text_input("Mật khẩu", type="password")
                if st.form_submit_button("MỞ VÍ"):
                    conn = sqlite3.connect(DB_FILE)
                    row = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
                    conn.close()
                    if row:
                        st.session_state.user = row[0]
                        st.session_state.name = row[2]
                        st.session_state.email = row[3]
                        st.rerun()
                    else: st.error("Sai thông tin rồi!")
        
        with tab2:
            with st.form("reg"):
                ru = st.text_input("Tên đăng nhập mới")
                rn = st.text_input("Tên hiển thị (VD: Trường)")
                re = st.text_input("Email (Để nhận backup)")
                rp = st.text_input("Mật khẩu", type="password")
                if st.form_submit_button("TẠO TÀI KHOẢN"):
                    if not ru or not rp: st.error("Điền đủ đi bạn!")
                    else:
                        try:
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("INSERT INTO users VALUES (?,?,?,?)", (ru, rp, rn, re))
                            conn.commit(); conn.close()
                            st.success("Tạo xong! Đăng nhập đi."); st.balloons()
                        except: st.error("Tên này có người dùng rồi!")

# --- MÀN HÌNH CHÍNH (SAU KHI LOGIN) ---
else:
    me = st.session_state.user
    
    # LOAD DATA CỦA USER ĐÓ
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM transactions WHERE username=? ORDER BY id DESC", conn, params=(me,))
    conn.close()
    
    total_inc = df[df['type']=='Thu']['amount'].sum() if not df.empty else 0
    total_exp = df[df['type']=='Chi']['amount'].sum() if not df.empty else 0
    net_bal = total_inc - total_exp

    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 {st.session_state.name}")
        persona = st.radio("Chế độ Bot:", ["Nhẹ nhàng", "Cục súc", "Nghiêm túc"])
        if st.button("Đăng xuất"): st.session_state.user = None; st.rerun()
        if st.button("Gửi Backup về Email ngay"): 
            send_backup(st.session_state.email, "Manual Request")
            st.success("Đã gửi!")

    # HEADER & MASCOT
    if 'ai_msg' not in st.session_state: st.session_state.ai_msg = f"Chào {st.session_state.name}! Ví hôm nay dày không? 👋"
    
    st.markdown(f"""
    <div class="mascot-area">
        <div class="chat-bubble">{st.session_state.ai_msg}</div><br>
        <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" class="robot-img">
    </div>
    """, unsafe_allow_html=True)

    # BALANCE CARD
    st.markdown(f"""
    <div class="glass-card" style="text-align:center">
        <div class="label-text">SỐ DƯ HIỆN TẠI</div>
        <div class="net-money">{net_bal:,.0f}đ</div>
        <br>
        <div style="display:flex; justify-content:space-around;">
            <div><div class="label-text">THU NHẬP</div><div style="color:#00b894; font-weight:800">+{total_inc:,.0f}</div></div>
            <div style="width:1px; background:#ddd"></div>
            <div><div class="label-text">CHI TIÊU</div><div style="color:#ff7675; font-weight:800">-{total_exp:,.0f}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ACTION AREA
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown('<div class="glass-card" style="height:180px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;"><div style="font-size:40px">📊</div><div style="font-weight:bold; color:#555">Báo cáo</div></div>', unsafe_allow_html=True)
    
    with c2:
        with st.popover("➕ GHI GIAO DỊCH", use_container_width=True):
            st.markdown("### 📝 Nhập thông tin")
            with st.form("add_tx"):
                t_type = st.selectbox("Loại", ["Chi", "Thu"])
                t_amt = st.number_input("Số tiền", step=1000, min_value=0)
                t_cat = st.text_input("Danh mục", "Ăn uống")
                t_note = st.text_input("Ghi chú", "")
                
                if st.form_submit_button("LƯU VÀO SỔ"):
                    # 1. Gọi AI trước
                    new_bal = net_bal - t_amt if t_type=='Chi' else net_bal + t_amt
                    advice = get_ai_advice(t_amt, t_cat, t_note, persona, new_bal)
                    
                    # 2. Lưu DB
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("INSERT INTO transactions (username, date, type, amount, category, note, ai_comment) VALUES (?,?,?,?,?,?,?)",
                                (me, datetime.now().strftime('%Y-%m-%d %H:%M'), t_type, t_amt, t_cat, t_note, advice))
                    conn.commit(); conn.close()
                    
                    # 3. Gửi Backup
                    send_backup(st.session_state.email, "New Transaction")
                    
                    # 4. Update UI
                    st.session_state.ai_msg = advice
                    st.rerun()

    # HISTORY LIST
    st.markdown("### 🕒 Lịch sử gần đây")
    if not df.empty:
        for idx, row in df.head(5).iterrows():
            icon = "💸" if row['type'] == 'Chi' else "💰"
            color = "#ff7675" if row['type'] == 'Chi' else "#00b894"
            sign = "-" if row['type'] == 'Chi' else "+"
            st.markdown(f"""
            <div class="glass-card" style="padding:10px 20px; margin-bottom:10px">
                <div class="history-item" style="border:none; padding:0">
                    <div style="display:flex; align-items:center">
                        <div class="cat-icon">{icon}</div>
                        <div>
                            <div style="font-weight:bold; color:#2d3436">{row['category']} <span style="font-weight:normal; font-size:12px; color:#888">({row['note']})</span></div>
                            <div style="font-size:11px; color:#aaa">{row['date']}</div>
                            <div style="font-size:11px; color:#6c5ce7; font-style:italic">🤖 {row['ai_comment'][:30]}...</div>
                        </div>
                    </div>
                    <div style="font-weight:800; color:{color}">{sign}{row['amount']:,}đ</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else: st.info("Chưa có giao dịch nào.")