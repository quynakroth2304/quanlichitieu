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
st.set_page_config(page_title="Misa AI Money V81", page_icon="🤖", layout="centered")

# 🔥 SỬA API KEY & EMAIL CỦA BẠN VÀO ĐÂY 🔥
GEMINI_API_KEY = "AIzaSyBE8SwSVUvxywD-LhUAhd_rsm2mNjs0L3I" 
EMAIL_HOST_USER = "quynakroth2304@gmail.com"
EMAIL_HOST_PASSWORD = "spem mabh baxv eqyl" 

# --- 2. DATABASE ---
DB_FILE = "finance_v81.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, name TEXT, type TEXT, balance INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, account_name TEXT, date TEXT, type TEXT, amount INTEGER, category TEXT, note TEXT, ai_comment TEXT
    )''')
    conn.commit(); conn.close()

init_db()

# --- 3. HÀM GỬI EMAIL ---
def send_backup(target_email, reason):
    if "email_cua" in EMAIL_HOST_USER: return 
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER; msg['To'] = target_email
        msg['Subject'] = f"BACKUP V81: {reason}"
        msg.attach(MIMEText("Dữ liệu chi tiêu mới nhất.", 'plain'))
        with open(DB_FILE, "rb") as f:
            p = MIMEBase('application', 'octet-stream'); p.set_payload(f.read())
            encoders.encode_base64(p); p.add_header('Content-Disposition', f"attachment; filename={DB_FILE}")
            msg.attach(p)
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls()
        s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD); s.sendmail(EMAIL_HOST_USER, target_email, msg.as_string()); s.quit()
    except: pass

# --- 4. HÀM AI (NÂNG CẤP THEO MODULE ZALO BOT) ---
def get_ai_advice(amount, category, note, persona, total_asset, recent_history):
    if "SỬA_" in GEMINI_API_KEY or not GEMINI_API_KEY: return "Chưa nhập API Key! 🤖"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Ưu tiên dùng model 1.5 Flash (nhanh & thông minh), nếu lỗi tự về Pro
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            model = genai.GenerativeModel('gemini-pro')

        # --- XÂY DỰNG NGỮ CẢNH (CONTEXT) TỪ LỊCH SỬ ---
        history_text = ""
        if not recent_history.empty:
            history_text = "Lịch sử chi tiêu gần đây của người này:\n"
            for _, row in recent_history.iterrows():
                history_text += f"- {row['date']}: {row['type']} {row['amount']}đ cho {row['category']} ({row['note']})\n"
        
        # --- PERSONA (TÍNH CÁCH - LẤY TỪ FILE AI.PY) ---
        system_instruction = ""
        if persona == "Nhây bựa (Lynk)":
            system_instruction = (
                "Bạn đóng vai Lynk, là con gái. Tính cách của Lynk là rất bựa bựa, nhây nhây, hài hước và lâu lâu hơi mất dạy tí. "
                "Mỗi tin nhắn của Lynk sẽ thả 1 icon tùy theo tâm trạng. Lynk xưng hô với người dùng là 'anh' hoặc 'cưng'. "
                "Đặc biệt: Hãy nhận xét về khoản chi tiêu vừa rồi dựa trên tổng tài sản và lịch sử chi tiêu. "
                "Nếu thấy tiêu hoang thì chửi khéo, nếu tiết kiệm thì khen đểu."
            )
        elif persona == "Giang hồ (Đòi nợ)":
            system_instruction = (
                "Bạn là một chủ nợ giang hồ cục súc, hay chửi thề (vừa phải). "
                "Bạn cực kỳ ghét việc người dùng tiêu tiền phung phí khi tài sản còn ít. "
                "Hãy chửi thẳng mặt, dùng ngôn ngữ đường phố, mỉa mai sâu cay."
            )
        else: # Nghiêm túc
            system_instruction = "Bạn là trợ lý tài chính chuyên nghiệp, nghiêm túc, ngắn gọn."

        # --- TẠO PROMPT CUỐI CÙNG ---
        final_prompt = f"""
        {system_instruction}
        
        {history_text}
        
        THÔNG TIN HIỆN TẠI:
        - Vừa thực hiện: Chi {amount}đ cho mục '{category}' (Ghi chú: {note}).
        - Tổng tài sản hiện tại còn: {total_asset}đ.
        
        Hãy phản hồi ngắn gọn (dưới 50 từ) đúng với tính cách trên.
        """
        
        return model.generate_content(final_prompt).text
    except Exception as e: return f"AI đang bận (Lỗi: {str(e)})"

# --- 5. CSS GLASS UI (GIỮ NGUYÊN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); font-family: 'Poppins', sans-serif; }
    [data-testid="stHeader"] { display: none; }
    
    @keyframes slideUp { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
    @keyframes float { 0% {transform: translateY(0px);} 50% {transform: translateY(-10px);} 100% {transform: translateY(0px);} }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px);
        border-radius: 20px; border: 1px solid rgba(255,255,255,0.8);
        padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.05); margin-bottom: 15px;
        animation: slideUp 0.5s ease-out;
    }
    
    .mascot-area { text-align: center; padding: 20px 0; animation: slideUp 0.8s ease-out; }
    .robot-img { width: 140px; filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2)); animation: float 4s ease-in-out infinite; }
    
    .chat-bubble {
        background: white; border-radius: 20px; padding: 15px 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: inline-block; max-width: 90%;
        font-size: 14px; color: #444; font-weight: 600; margin-bottom: 15px; border-bottom-left-radius: 2px;
    }

    .bank-card {
        background: linear-gradient(45deg, #0984e3, #74b9ff); color: white;
        border-radius: 15px; padding: 15px; min-width: 100%; 
        box-shadow: 0 4px 15px rgba(9, 132, 227, 0.3); text-align: center; margin-bottom: 10px;
    }
    .bank-card.cash { background: linear-gradient(45deg, #00b894, #55efc4); box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3); }
    
    .total-asset { 
        font-size: 36px; font-weight: 800; 
        background: linear-gradient(to right, #2d3436, #000); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        border-radius: 12px !important; border: 1px solid #ddd !important; background: white !important;
    }
    .stButton button {
        background: #6c5ce7 !important; color: white !important; border-radius: 12px !important; font-weight: bold !important;
    }
    
    .history-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }
    .cat-icon { width: 40px; height: 40px; background: #dfe6e9; border-radius: 50%; display:flex; align-items:center; justify-content:center; font-size:20px; margin-right: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 6. LOGIC CHÍNH ---
if 'user' not in st.session_state: st.session_state.user = None

# === LOGIN ===
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:#6c5ce7'>MISA AI V81</h1>", unsafe_allow_html=True)
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
                st.markdown("**💰 Thiết lập tài sản ban đầu:**")
                cash_init = st.number_input("Tiền mặt đang có", step=50000, value=0)
                bank_name = st.text_input("Tên Ngân hàng", "MBBank")
                bank_init = st.number_input("Số dư ngân hàng", step=50000, value=0)
                
                if st.form_submit_button("ĐĂNG KÝ NGAY"):
                    if ru and rp:
                        try:
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("INSERT INTO users VALUES (?,?,?,?)", (ru, rp, rn, re))
                            conn.execute("INSERT INTO accounts (username, name, type, balance) VALUES (?,?,?,?)", (ru, "Tiền mặt", "cash", cash_init))
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

# === DASHBOARD ===
else:
    me = st.session_state.user
    conn = sqlite3.connect(DB_FILE)
    
    # 1. Lấy ví & Fix lỗi
    accounts = pd.read_sql("SELECT * FROM accounts WHERE username=?", conn, params=(me,))
    if accounts.empty:
        conn.execute("INSERT INTO accounts (username, name, type, balance) VALUES (?,?,?,?)", (me, "Tiền mặt", "cash", 0))
        conn.commit()
        accounts = pd.read_sql("SELECT * FROM accounts WHERE username=?", conn, params=(me,))
    
    accounts['balance'] = pd.to_numeric(accounts['balance'], errors='coerce').fillna(0)
    total_asset = accounts['balance'].sum()
    
    # Lấy lịch sử để nạp vào não AI
    history = pd.read_sql("SELECT * FROM transactions WHERE username=? ORDER BY id DESC LIMIT 10", conn, params=(me,))
    recent_history_for_ai = history.head(5) # Lấy 5 gd gần nhất cho AI học
    conn.close()

    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 {st.session_state.name}")
        # THÊM TÍNH CÁCH NHÂY BỰA (LYNK) NHƯ BOT ZALO
        persona = st.radio("Tính cách Bot:", ["Nhây bựa (Lynk)", "Giang hồ (Đòi nợ)", "Nghiêm túc"])
        
        st.divider()
        st.subheader("➕ Thêm Ngân Hàng")
        with st.form("add_bank"):
            new_b_name = st.text_input("Tên (VD: TPBank)")
            new_b_bal = st.number_input("Số dư", min_value=0)
            if st.form_submit_button("Thêm ví"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO accounts (username, name, type, balance) VALUES (?,?,?,?)", (me, new_b_name, "bank", new_b_bal))
                conn.commit(); conn.close(); st.rerun()
        if st.button("Đăng xuất"): st.session_state.user = None; st.rerun()

    # HEADER & AI MASCOT
    if 'ai_msg' not in st.session_state: st.session_state.ai_msg = f"Chào cưng! Ví còn {total_asset:,.0f}đ đó nha 😘"
    
    st.markdown(f"""
    <div class="mascot-area">
        <div class="chat-bubble">{st.session_state.ai_msg}</div><br>
        <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" class="robot-img">
    </div>
    """, unsafe_allow_html=True)

    # TOTAL ASSET CARD
    st.markdown(f"""
    <div class="glass-card" style="text-align:center">
        <div style="font-size:12px; color:#888; font-weight:bold;">TỔNG TÀI SẢN RÒNG</div>
        <div class="total-asset">{total_asset:,.0f}đ</div>
    </div>
    """, unsafe_allow_html=True)

    # WALLET LIST
    st.markdown("**💳 Ví của bạn:**")
    if not accounts.empty:
        num_cols = min(len(accounts), 3)
        cols = st.columns(num_cols)
        for i, row in accounts.iterrows():
            col_idx = i % num_cols
            with cols[col_idx]:
                tk_type = "cash" if row['type'] == 'cash' else "bank"
                icon = "💵" if row['type'] == 'cash' else "🏦"
                bal_display = int(row['balance'])
                st.markdown(f"""
                <div class="bank-card {tk_type}">
                    <div style="font-size:20px">{icon}</div>
                    <div style="font-weight:bold; font-size:13px">{row['name']}</div>
                    <div style="font-size:15px; font-weight:800; margin-top:5px">{bal_display:,}</div>
                </div>
                """, unsafe_allow_html=True)

    # TRANSACTION FORM
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 GHI GIAO DỊCH MỚI", expanded=True):
        with st.form("tx_form"):
            col1, col2 = st.columns(2)
            t_type = col1.selectbox("Loại", ["Chi tiền", "Thu tiền"])
            acc_names = accounts['name'].tolist()
            t_acc = col2.selectbox("Nguồn tiền", acc_names if acc_names else ["Chưa có ví"])
            t_amt = st.number_input("Số tiền", step=1000, min_value=0)
            t_cat = st.text_input("Nội dung", "Ăn uống")
            t_note = st.text_input("Ghi chú", "")
            
            if st.form_submit_button("LƯU GIAO DỊCH"):
                if t_amt > 0 and acc_names:
                    conn = sqlite3.connect(DB_FILE)
                    curr_bal = int(accounts[accounts['name']==t_acc]['balance'].values[0])
                    new_bal = curr_bal - t_amt if t_type == "Chi tiền" else curr_bal + t_amt
                    
                    # Cập nhật ví
                    conn.execute("UPDATE accounts SET balance=? WHERE username=? AND name=?", (new_bal, me, t_acc))
                    
                    # Tính tổng tài sản dự kiến sau khi lưu để AI biết
                    new_total_asset = total_asset - t_amt if t_type == "Chi tiền" else total_asset + t_amt
                    
                    # GỌI AI PHÂN TÍCH TRƯỚC KHI LƯU DB
                    with st.spinner("Lynk đang suy nghĩ..."):
                        advice = get_ai_advice(t_amt, t_cat, t_note, persona, new_total_asset, recent_history_for_ai)
                    
                    # Lưu lịch sử kèm lời khuyên AI
                    conn.execute("INSERT INTO transactions (username, account_name, date, type, amount, category, note, ai_comment) VALUES (?,?,?,?,?,?,?,?,?)",
                                (me, t_acc, datetime.now().strftime('%Y-%m-%d %H:%M'), t_type, t_amt, t_cat, t_note, advice))
                    conn.commit(); conn.close()
                    
                    st.session_state.ai_msg = advice
                    send_backup(st.session_state.email, "New Transaction")
                    st.rerun()
                else: st.error("Nhập tiền hoặc tạo ví trước!")

    # HISTORY LIST
    st.markdown("**🕒 Lịch sử:**")
    if not history.empty:
        for idx, row in history.iterrows():
            clr = "#ff7675" if row['type'] == "Chi tiền" else "#00b894"
            sign = "-" if row['type'] == "Chi tiền" else "+"
            st.markdown(f"""
            <div class="glass-card" style="padding:10px 15px; margin-bottom:10px;">
                <div class="history-item" style="border:none; padding:0">
                    <div style="display:flex; align-items:center">
                        <div class="cat-icon">{'💸' if row['type']=="Chi tiền" else '💰'}</div>
                        <div>
                            <div style="font-weight:bold; color:#333">{row['category']} <span style="font-size:11px; color:#888">({row['account_name']})</span></div>
                            <div style="font-size:11px; color:#aaa">{row['date']}</div>
                        </div>
                    </div>
                    <div style="font-weight:800; color:{clr}">{sign}{row['amount']:,}đ</div>
                </div>
                <div style="font-size:12px; color:#6c5ce7; font-style:italic; margin-top:5px; padding-left:55px;">
                    🤖 {row['ai_comment']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else: st.info("Chưa có giao dịch.")