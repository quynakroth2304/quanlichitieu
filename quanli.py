import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="Misa AI Money Pro", page_icon="💸", layout="centered")

# 🔥 NHẬP API KEY CỦA BẠN VÀO ĐÂY 🔥
GEMINI_API_KEY = "AIzaSyAaviiakNYZURaRLBEskwzhV4zqOmeO4n8" 

# --- DATABASE ---
DB_FILE = "finance_v73.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, amount INTEGER, category TEXT, note TEXT
    )''')
    conn.commit(); conn.close()
init_db()

# --- CSS MAGIC (LEVEL UP: GLASSMORPHISM & ANIMATIONS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    /* 1. NỀN & FONT */
    .stApp { 
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Poppins', sans-serif; 
    }
    [data-testid="stHeader"] { display: none; }
    
    /* 2. HIỆU ỨNG ĐỘNG (ANIMATIONS) */
    @keyframes float { 0% {transform: translateY(0px);} 50% {transform: translateY(-15px);} 100% {transform: translateY(0px);} }
    @keyframes slideUp { from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);} }
    @keyframes pulse { 0% {transform: scale(1);} 50% {transform: scale(1.05);} 100% {transform: scale(1);} }
    
    /* 3. MASCOT ROBOT */
    .mascot-area {
        text-align: center; padding: 20px 0;
        animation: slideUp 0.8s ease-out;
    }
    .robot-img { 
        width: 140px; 
        filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2));
        animation: float 4s ease-in-out infinite; 
    }
    
    /* 4. BONG BÓNG CHAT (iMESSAGE STYLE) */
    .chat-bubble {
        background: white; border-radius: 20px; padding: 15px 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        display: inline-block; max-width: 90%;
        font-size: 14px; color: #444; font-weight: 600;
        position: relative; margin-bottom: 15px;
        border-bottom-left-radius: 2px;
    }
    
    /* 5. THẺ CARD (GLASSMORPHISM) */
    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        margin-bottom: 20px;
        animation: slideUp 1s ease-out;
    }
    
    /* 6. SỐ LIỆU & TEXT */
    .label-text { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .money-text { font-size: 26px; font-weight: 800; color: #2d3436; margin: 5px 0; }
    .net-money { 
        font-size: 38px; font-weight: 800; 
        background: linear-gradient(45deg, #00b09b, #96c93d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulse 3s infinite;
    }
    .expense-money { color: #ff6b6b; }
    
    /* 7. FORM & BUTTON */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        border-radius: 16px !important; border: none !important;
        background: #f1f2f6 !important; padding: 10px 15px !important;
    }
    .stButton button {
        background: linear-gradient(45deg, #6c5ce7, #a29bfe) !important;
        color: white !important; border: none !important;
        border-radius: 18px !important; padding: 15px !important;
        font-weight: 800 !important; letter-spacing: 1px;
        box-shadow: 0 10px 20px rgba(108, 92, 231, 0.3);
        transition: 0.3s;
    }
    .stButton button:hover { transform: translateY(-3px); box-shadow: 0 15px 25px rgba(108, 92, 231, 0.4); }

    /* 8. LỊCH SỬ LIST */
    .history-item {
        display: flex; justify-content: space-between; align-items: center;
        padding: 15px 0; border-bottom: 1px solid rgba(0,0,0,0.05);
    }
    .cat-icon { width: 40px; height: 40px; background: #dfe6e9; border-radius: 50%; display:flex; align-items:center; justify-content:center; font-size:20px; margin-right: 15px; }
</style>
""", unsafe_allow_html=True)

# --- LOGIC AI ---
def get_ai_advice(amount, category, note, persona, balance):
    if not GEMINI_API_KEY: return "Nhập API Key vào code đi đại ca ơi! 🤖"
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompts = {
        "Cục súc": f"Bạn là AI quản lý tài chính cục súc, hay chửi thề (nhẹ). User tiêu {amount}đ cho {category} ({note}). Số dư còn {balance}đ. Chửi nó vì nghèo mà hoang. Ngắn gọn (dưới 40 từ).",
        "Nhẹ nhàng": f"Bạn là em gái mưa tên Misa, cute, icon đáng yêu. User tiêu {amount}đ cho {category} ({note}). Khuyên nhủ nhẹ nhàng. Ngắn gọn.",
        "Nghiêm túc": f"Phân tích tài chính ngắn gọn: {amount}đ cho {category}. Hợp lý không?"
    }
    try:
        response = model.generate_content(prompts.get(persona, prompts["Nhẹ nhàng"]))
        return response.text
    except: return "Mạng lag quá, cho Misa nghỉ tí..."

# --- XỬ LÝ SỐ LIỆU ---
conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

total_income = df[df['type']=='Thu']['amount'].sum() if not df.empty else 0
total_expense = df[df['type']=='Chi']['amount'].sum() if not df.empty else 0
net_change = total_income - total_expense

# --- GIAO DIỆN CHÍNH ---

# 1. SETTINGS (Ẩn trong Sidebar)
with st.sidebar:
    st.title("⚙️ Cài đặt")
    persona = st.radio("Chế độ Bot:", ["Nhẹ nhàng", "Cục súc", "Nghiêm túc"])
    st.info("Phiên bản V73 - Glass UI")

# 2. HEADER ROBOT (ĐÃ THÊM HIỆU ỨNG)
if 'ai_msg' not in st.session_state: st.session_state.ai_msg = "Chào Boss! Hôm nay ví dày hay mỏng đây? 💖"

st.markdown(f"""
<div class="mascot-area">
    <div class="chat-bubble">{st.session_state.ai_msg}</div>
    <br>
    <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" class="robot-img">
</div>
""", unsafe_allow_html=True)

# 3. THẺ TỔNG KẾT (HERO SECTION)
st.markdown(f"""
<div class="glass-card" style="text-align:center">
    <div class="label-text">SỐ DƯ HIỆN TẠI</div>
    <div class="net-money">{net_change:,.0f}đ</div>
    <br>
    <div style="display:flex; justify-content:space-around;">
        <div>
            <div class="label-text">THU NHẬP</div>
            <div style="color:#00b894; font-weight:800; font-size:18px">+{total_income:,.0f}</div>
        </div>
        <div style="width:1px; background:#ddd"></div>
        <div>
            <div class="label-text">CHI TIÊU</div>
            <div style="color:#ff7675; font-weight:800; font-size:18px">-{total_expense:,.0f}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. KHU VỰC NHẬP LIỆU (GRID ĐẸP)
c1, c2 = st.columns([1, 1.5])

with c1:
    st.markdown("""
    <div class="glass-card" style="height:180px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
        <div style="font-size:40px">📊</div>
        <div style="font-weight:bold; margin-top:10px; color:#555">Báo cáo<br>Chi tiết</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    # Nút bấm mở Form (Popover)
    with st.popover("➕ GHI GIAO DỊCH MỚI", use_container_width=True):
        st.markdown("### 📝 Nhập thông tin")
        with st.form("add_tx_v73"):
            type_tx = st.selectbox("Loại giao dịch", ["Chi", "Thu"])
            amt_tx = st.number_input("Số tiền", step=5000, min_value=0)
            cat_tx = st.text_input("Nội dung (VD: Cà phê)", "Ăn uống")
            
            if st.form_submit_button("LƯU VÀO SỔ"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO transactions (date, type, amount, category, note) VALUES (?,?,?,?,?)",
                            (datetime.now().strftime('%Y-%m-%d %H:%M'), type_tx, amt_tx, cat_tx, ""))
                conn.commit(); conn.close()
                
                # Gọi AI
                st.session_state.ai_msg = get_ai_advice(amt_tx, cat_tx, "", persona, net_change - amt_tx if type_tx=='Chi' else net_change + amt_tx)
                st.rerun()

# 5. DANH SÁCH LỊCH SỬ (GIAO DIỆN MOBILE LIST)
st.markdown("<h3 style='color:#555; margin-top:20px'>🕒 Gần đây</h3>", unsafe_allow_html=True)

if not df.empty:
    # Lấy 5 gd mới nhất
    recent = df.sort_index(ascending=False).head(5)
    
    st.markdown('<div class="glass-card" style="padding:10px 20px;">', unsafe_allow_html=True)
    for index, row in recent.iterrows():
        icon = "💸" if row['type'] == 'Chi' else "💰"
        color = "#ff7675" if row['type'] == 'Chi' else "#00b894"
        sign = "-" if row['type'] == 'Chi' else "+"
        
        st.markdown(f"""
        <div class="history-item">
            <div style="display:flex; align-items:center">
                <div class="cat-icon">{icon}</div>
                <div>
                    <div style="font-weight:bold; color:#2d3436">{row['category']}</div>
                    <div style="font-size:11px; color:#aaa">{row['date']}</div>
                </div>
            </div>
            <div style="font-weight:800; color:{color}">{sign}{row['amount']:,}đ</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Chưa có giao dịch nào. Hãy bấm nút Thêm màu tím ở trên!")

# 6. FOOTER DECORATION
st.markdown("<br><br><div style='text-align:center; color:#ccc; font-size:12px'>Misa AI Money V73</div>", unsafe_allow_html=True)