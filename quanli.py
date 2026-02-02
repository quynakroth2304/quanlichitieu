import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime
import time

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Misa AI Money", page_icon="🐷", layout="centered")

# 🔥 NHẬP GEMINI API KEY CỦA BẠN VÀO ĐÂY 🔥
GEMINI_API_KEY = ""  

# --- DATABASE ---
DB_FILE = "finance_v71.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        amount INTEGER,
        category TEXT,
        note TEXT
    )''')
    conn.commit(); conn.close()

init_db()

# --- CSS MAGIC (TẠO GIAO DIỆN GIỐNG ẢNH) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
    
    /* Reset nền */
    .stApp { background-color: #f5f7fa; font-family: 'Nunito', sans-serif; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    
    /* Ẩn các thành phần thừa */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    
    /* HEADER BUTTONS */
    .top-btn {
        background: #fff; border-radius: 20px; padding: 8px 15px; 
        font-weight: bold; color: #555; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: inline-block; margin-right: 10px; font-size: 14px;
    }
    .icon-gold { color: #ffbf00; }
    .icon-blue { color: #0084ff; }

    /* MASCOT AREA */
    .mascot-container { text-align: center; margin-top: 20px; margin-bottom: 10px; position: relative; }
    .robot-img { width: 120px; animation: float 3s ease-in-out infinite; }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    /* SPEECH BUBBLE (Lời thoại robot) */
    .speech-bubble {
        position: relative; background: #fff; border-radius: 15px;
        padding: 10px 15px; display: inline-block; max-width: 80%;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        font-size: 14px; color: #333; border: 1px solid #eee;
    }
    .speech-bubble:after {
        content: ''; position: absolute; bottom: -10px; left: 50%;
        border-width: 10px 10px 0; border-style: solid;
        border-color: #fff transparent; display: block; width: 0;
        margin-left: -10px;
    }

    /* MAIN ACTION CARDS */
    .action-card {
        background: white; border-radius: 20px; padding: 20px; text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 120px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        border: 1px solid #eee; cursor: pointer; transition: 0.3s;
    }
    .action-card:hover { transform: scale(1.02); }
    .big-num { font-size: 20px; font-weight: 800; color: #333; margin-top: 5px; }
    .sub-text { font-size: 13px; color: #888; font-weight: 600; }
    .add-icon { font-size: 30px; color: #888; }

    /* GRADIENT SUMMARY CARD (THAY ĐỔI RÒNG) */
    .gradient-card {
        background: linear-gradient(135deg, #e0f7fa 0%, #e8f5e9 100%);
        border-radius: 20px; padding: 20px; margin-top: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #b2dfdb;
    }
    .grad-title { font-size: 16px; font-weight: bold; color: #004d40; margin-bottom: 5px; }
    .grad-total { font-size: 28px; font-weight: 800; color: #004d40; margin-bottom: 15px; }
    
    .stat-row { display: flex; justify-content: space-between; }
    .stat-box { 
        background: rgba(255,255,255,0.6); padding: 10px 20px; border-radius: 12px; 
        width: 48%; text-align: center;
    }
    .income-txt { color: #42b72a; font-weight: 800; font-size: 16px; }
    .expense-txt { color: #ff4d4d; font-weight: 800; font-size: 16px; }
    .label-stat { font-size: 12px; color: #555; }

    /* FORM STYLING */
    div[data-testid="stForm"] { background: white; padding: 20px; border-radius: 20px; border: 1px solid #eee; }
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        border-radius: 10px !important; border: 1px solid #eee !important;
    }
    .stButton button {
        background-color: #333 !important; color: white !important; border-radius: 25px !important;
        width: 100%; padding: 10px !important; font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIC AI GEMINI ---
def get_ai_advice(amount, category, note, persona, balance):
    if not GEMINI_API_KEY: return "Bạn chưa nhập API Key nên mình hổng biết nói gì :("
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompts = {
        "Cục súc": f"Bạn là một con robot tài chính cực kỳ đanh đá, mỏ hỗn. Người dùng vừa tiêu {amount} cho {category} ({note}). Số dư hiện tại là {balance}. Hãy chửi nó vì tiêu hoang hoặc dọa nó sợ. Ngắn gọn thôi.",
        "Nhẹ nhàng": f"Bạn là con robot tài chính dễ thương, cute (tên Misa). Người dùng vừa tiêu {amount} cho {category} ({note}). Hãy khuyên nhủ nhẹ nhàng, dùng icon đáng yêu. Ngắn gọn.",
        "Nghiêm túc": f"Phân tích khoản chi: {amount} cho {category}. Đưa ra lời khuyên tài chính ngắn gọn."
    }
    
    try:
        response = model.generate_content(prompts.get(persona, prompts["Nhẹ nhàng"]))
        return response.text
    except: return "Mạng lag quá, không load được não AI..."

# --- LOGIC XỬ LÝ SỐ LIỆU ---
conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

total_income = df[df['type']=='Thu']['amount'].sum() if not df.empty else 0
total_expense = df[df['type']=='Chi']['amount'].sum() if not df.empty else 0
net_change = total_income - total_expense

# --- GIAO DIỆN CHÍNH ---

# 1. HEADER (Giả lập nút bấm như ảnh)
c1, c2 = st.columns([1,1])
with c1: st.markdown('<div class="top-btn"><span class="icon-gold">🏆</span> Những cột mốc</div>', unsafe_allow_html=True)
with c2: st.markdown('<div class="top-btn" style="float:right"><span class="icon-blue">📊</span> Phân tích thêm</div>', unsafe_allow_html=True)

# 2. MASCOT & AI SPEECH (Phần quan trọng nhất)
if 'ai_msg' not in st.session_state: st.session_state.ai_msg = "Chào bạn! Hôm nay ví tiền thế nào rồi? 👋"

st.markdown(f"""
<div class="mascot-container">
    <div class="speech-bubble">{st.session_state.ai_msg}</div>
    <br>
    <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" class="robot-img">
</div>
""", unsafe_allow_html=True)

# 3. SETTINGS NHANH (Sidebar cho gọn)
with st.sidebar:
    st.header("Cài đặt Misa AI")
    persona = st.radio("Tính cách Robot:", ["Nhẹ nhàng", "Cục súc", "Nghiêm túc"])
    st.info("Nhập API Key trong code để Bot hoạt động nhé!")

# 4. KHU VỰC THAO TÁC (GRID GIỐNG ẢNH)
col_left, col_right = st.columns(2)

with col_left:
    # Hộp hiển thị Chi Tiêu tháng này
    st.markdown(f"""
    <div class="action-card">
        <div class="sub-text">CHI TIÊU THÁNG NÀY</div>
        <div class="big-num">{total_expense:,.0f}đ</div>
        <div style="font-size:10px; color:#aaa">✏️ Chạm để xem</div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # Nút Thêm Giao Dịch (Dùng Popover để không chuyển trang)
    with st.popover("➕ Thêm GD", use_container_width=True):
        st.markdown("### Thêm giao dịch mới")
        with st.form("add_tx"):
            t_type = st.selectbox("Loại", ["Chi", "Thu"], index=0)
            t_amt = st.number_input("Số tiền", step=1000, min_value=0)
            t_cat = st.text_input("Danh mục", "Ăn uống")
            t_note = st.text_input("Ghi chú", "...")
            
            if st.form_submit_button("Lưu ngay"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO transactions (date, type, amount, category, note) VALUES (?,?,?,?,?)",
                            (datetime.now().strftime('%Y-%m-%d'), t_type, t_amt, t_cat, t_note))
                conn.commit(); conn.close()
                
                # Gọi AI trả lời
                st.session_state.ai_msg = get_ai_advice(t_amt, t_cat, t_note, persona, net_change - t_amt if t_type=='Chi' else net_change + t_amt)
                st.rerun()
    
    # Hiển thị text giả lập nút bấm (chỉ để đẹp)
    st.markdown("""
    <div style="text-align:center; margin-top:-35px; pointer-events:none; position:relative; z-index:0;">
        <div class="action-card" style="background:#eee; border:none;">
            <div class="add-icon">+</div>
            <div class="sub-text">Ví mới</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. DATE SELECTOR
st.markdown("<br>", unsafe_allow_html=True)
col_d1, col_d2 = st.columns([1, 2])
with col_d1: st.selectbox("", ["Tháng này", "Tháng trước"], label_visibility="collapsed")
with col_d2: st.markdown(f"<div style='padding-top:10px; color:#555'>Tháng {datetime.now().month} năm {datetime.now().year}</div>", unsafe_allow_html=True)

# 6. GRADIENT SUMMARY CARD (THAY ĐỔI RÒNG)
# Logic màu sắc: Âm thì đỏ, Dương thì xanh
net_color = "#004d40" if net_change >= 0 else "#d32f2f"

st.markdown(f"""
<div class="gradient-card">
    <div class="grad-title">Thay đổi ròng</div>
    <div class="grad-total" style="color:{net_color}">{net_change:,.0f}đ</div>
    
    <div class="stat-row">
        <div class="stat-box">
            <div class="label-stat">Chi phí ▼</div>
            <div class="expense-txt">{total_expense:,.0f}đ</div>
        </div>
        <div class="stat-box">
            <div class="label-stat">Thu nhập ▲</div>
            <div class="income-txt">{total_income:,.0f}đ</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 7. BOTTOM NAV (GIẢ LẬP)
st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:100%; background:white; padding:15px; border-top:1px solid #eee; display:flex; justify-content:space-around; align-items:center; z-index:999;">
    <div style="text-align:center; color:#0084ff; font-weight:bold;">🏠<br><span style="font-size:10px">Trang chủ</span></div>
    <div style="text-align:center; color:#ccc;">💸<br><span style="font-size:10px">Sổ GD</span></div>
    <div style="text-align:center; color:#ccc;">📊<br><span style="font-size:10px">Báo cáo</span></div>
    <div style="text-align:center; color:#ccc;">👤<br><span style="font-size:10px">Tài khoản</span></div>
</div>
<br><br><br>
""", unsafe_allow_html=True)