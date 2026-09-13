import streamlit as st
import json
import os
import sys

# Đảm bảo đường dẫn import luôn chính xác dù chạy từ bất kỳ thư mục nào
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import importlib
import app
importlib.reload(app)
from app import run_react_agent, clean_final_answer
from mcp_server import MCPExpenseServer
from providers import get_llm_provider
from tools import MOCK_EXPENSE_DATABASE

def clean_final_answer(text: str) -> str:
    """Loại bỏ các đoạn suy luận kỹ thuật Thought/Action nếu có, chỉ giữ lại câu trả lời trực tiếp cho người dùng"""
    if not text:
        return ""
    markers = [
        "**Phản hồi cho người dùng:**",
        "**Phản hồi gửi người dùng:**",
        "**Phản hồi:**",
        "Phản hồi cho người dùng:",
        "Phản hồi:"
    ]
    for marker in markers:
        if marker in text:
            parts = text.split(marker, 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
                
    lines = text.split("\n")
    cleaned_lines = []
    skip_mode = False
    for line in lines:
        lower_line = line.strip().lower()
        if lower_line.startswith("**thought:**") or lower_line.startswith("thought:") or lower_line.startswith("**action:**") or lower_line.startswith("action:"):
            skip_mode = True
            continue
        if skip_mode:
            if lower_line.startswith("**phản hồi") or lower_line.startswith("phản hồi"):
                skip_mode = False
                continue
            if line.strip() == "---" or lower_line.startswith("chào bạn") or lower_line.startswith("dạ,") or lower_line.startswith("dựa trên") or lower_line.startswith("tôi đã") or lower_line.startswith("bạn có"):
                skip_mode = False
                cleaned_lines.append(line)
                continue
            continue
        cleaned_lines.append(line)
        
    result = "\n".join(cleaned_lines).strip()
    return result if result else text


# Icon URLs chuẩn từ Icons8 (Fluency High-Resolution Vector Assets)
ICONS = {
    "app_logo": "https://img.icons8.com/fluency/96/wallet.png",
    "dashboard": "https://img.icons8.com/fluency/48/combo-chart.png",
    "folder": "https://img.icons8.com/fluency/48/folder-invoices.png",
    "user": "https://img.icons8.com/fluency/96/user-male-circle.png",
    "assistant": "https://img.icons8.com/fluency/96/bot.png",
    "trace": "https://img.icons8.com/fluency/48/flow-chart.png",
    "settings": "https://img.icons8.com/fluency/48/settings.png",
    # Danh mục cụ thể
    "ăn uống": "https://img.icons8.com/fluency/48/restaurant.png",
    "mua sắm": "https://img.icons8.com/fluency/48/shopping-bag.png",
    "di chuyển": "https://img.icons8.com/fluency/48/car.png",
    "học tập": "https://img.icons8.com/fluency/48/graduation-cap.png",
    "giải trí": "https://img.icons8.com/fluency/48/popcorn.png",
    "default_cat": "https://img.icons8.com/fluency/48/price-tag.png"
}

st.set_page_config(
    page_title="Trợ lý Chi tiêu ReAct Agent",
    page_icon=ICONS["app_logo"],
    layout="wide"
)

# Tùy biến CSS để UI trông hiện đại, gọn gàng và không dùng emoji
st.markdown("""
<style>
    .cat-badge {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .cat-name {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .cat-info {
        font-size: 0.85rem;
        color: #8c8c8c;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Provider & MCP Server
if "provider" not in st.session_state:
    st.session_state.provider = get_llm_provider()
    st.session_state.mcp_server = MCPExpenseServer()
    st.session_state.messages = []

# --- SIDEBAR: DASHBOARD TÀI CHÍNH ---
with st.sidebar:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <img src="{ICONS['dashboard']}" width="32"/>
        <h2 style="margin: 0; font-size: 1.3rem;">Tổng quan Ví Chi tiêu</h2>
    </div>
    """, unsafe_allow_html=True)

    total_budget = sum(c["allocated_budget"] for c in MOCK_EXPENSE_DATABASE.values())
    total_spent = sum(c["spent"] for c in MOCK_EXPENSE_DATABASE.values())
    total_rem = total_budget - total_spent
    spent_pct = round((total_spent / total_budget) * 100, 1) if total_budget > 0 else 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Tổng ngân sách", f"{int(total_budget):,} đ")
    col2.metric("Đã chi", f"{int(total_spent):,} đ")
    st.metric("Số dư còn lại", f"{int(total_rem):,} đ", delta=f"{spent_pct}% đã dùng")
    
    st.progress(min(spent_pct / 100.0, 1.0))

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-top: 25px; margin-bottom: 12px;">
        <img src="{ICONS['folder']}" width="26"/>
        <h3 style="margin: 0; font-size: 1.1rem;">Danh mục Ngân sách</h3>
    </div>
    """, unsafe_allow_html=True)

    for cat in MOCK_EXPENSE_DATABASE.values():
        cat_key = cat["category_name"].lower()
        icon_url = ICONS.get(cat_key, ICONS["default_cat"])
        rem = cat["allocated_budget"] - cat["spent"]
        st.markdown(f"""
        <div class="cat-badge">
            <img src="{icon_url}" width="24"/>
            <div>
                <div class="cat-name">{cat['category_name']}</div>
                <div class="cat-info">Còn {int(rem):,} đ / {int(cat['allocated_budget']):,} đ</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN CHAT AREA ---
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 14px; margin-bottom: 5px;">
    <img src="{ICONS['app_logo']}" width="42"/>
    <div>
        <h1 style="margin: 0; font-size: 2rem;">Trợ lý Quản lý Chi tiêu Cá nhân</h1>
        <p style="margin: 0; color: #888; font-size: 0.95rem;">Hệ thống ReAct Agent kết nối Model Context Protocol (MCP) & Google Gemini</p>
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# Hiển thị lịch sử hội thoại
for msg in st.session_state.messages:
    avatar = ICONS["user"] if msg["role"] == "user" else ICONS["assistant"]
    with st.chat_message(msg["role"], avatar=avatar):
        clean_text = clean_final_answer(msg["content"]) if msg["role"] == "assistant" else msg["content"]
        st.markdown(clean_text)
        if "trace" in msg and msg["trace"]:
            with st.expander("Bản ghi suy luận ReAct Waterfall Trace"):
                st.json(msg["trace"])

# Nhận tin nhắn từ người dùng
if prompt := st.chat_input("Nhập câu hỏi tra cứu, ghi nhận khoản chi hoặc kiểm tra ngân sách..."):
    # Lưu tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=ICONS["user"]):
        st.markdown(prompt)

    # Xử lý Agent Response
    with st.chat_message("assistant", avatar=ICONS["assistant"]):
        with st.spinner("Agent đang phân tích câu hỏi và truy vấn MCP Server..."):
            traces = run_react_agent(prompt, st.session_state.provider, st.session_state.mcp_server)
            
            # Trích xuất câu trả lời kết luận
            raw_ans = next(
                (t["output"] for t in reversed(traces) if t.get("action_type") == "FINAL_ANSWER"),
                "Đã hoàn tất xử lý yêu cầu."
            )
            final_ans = clean_final_answer(raw_ans)
            st.markdown(final_ans)
            
            # Hiển thị dấu vết thực thi
            with st.expander("Bản ghi suy luận ReAct Waterfall Trace"):
                st.json(traces)

    st.session_state.messages.append({"role": "assistant", "content": final_ans, "trace": traces})
    st.rerun()
