# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Lại Bá Quân  
> **Mã Sinh Viên / Mã Học viên:** 02495  
> **Chủ đề Lựa chọn:** Trợ lý Quản lý Chi tiêu Cá nhân

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 3 / 5 | Bài toán yêu cầu chuỗi suy luận đa bước: (1) Nhận diện ý định $\rightarrow$ (2) Tra cứu số dư/chi tiêu thực tế $\rightarrow$ (3) Tính toán số tiền sau giao dịch so với hạn mức ngân sách $\rightarrow$ (4) Đưa ra khuyến nghị hoặc cảnh báo thâm hụt. |
| **2. Tool Interaction** | 5 / 5 | Bắt buộc tương tác với CSDL ví chi tiêu qua MCP Server. LLM không thể tự biết số dư, danh mục chi tiêu hay lịch sử chi tiêu nếu không gọi Tool `query_expense` và `add_expense`. |
| **3. Dynamic Decision** | 5 / 5 | Quyết định bước tiếp theo phụ thuộc động vào dữ liệu trả về từ Observation: Nếu ngân sách còn đủ thì phản hồi tích cực/cho phép ghi nhận; nếu sắp vượt ngưỡng thì cảnh báo thắt chặt chi tiêu; nếu danh mục không tồn tại thì báo lỗi lịch sự. |
| **4. Long Horizon Goal** | 4 / 5 | Hướng đến mục tiêu dài hạn là kiểm soát kỷ luật tài chính, tối ưu hóa ngân sách cá nhân theo chu kỳ tháng/năm và hỗ trợ người dùng đạt mục tiêu tiết kiệm. |
| **TỔNG ĐIỂM AGENTIC FIT** | **17 / 20** | *Đạt 17/20 điểm (> 12/20): Bài toán phù hợp để triển khai Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Ghi lại giúp tôi một khoản chi 45000 VNĐ cho 'Cà phê sáng' vào danh mục 'Ăn uống' ngày 13/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "add_expense",
    "arguments": {
      "date": "13/09/2026",
      "category": "Ăn uống",
      "note": "Cà phê sáng",
      "amount": 45000
    },
    "observation": {
      "status": "SUCCESS",
      "transaction_id": "TX-105329",
      "amount": 45000.0,
      "category": "Ăn uống",
      "note": "Cà phê sáng",
      "date": "13/09/2026",
      "current_spent": 1495000.0,
      "remaining_budget": 1505000.0,
      "message": "Đã ghi nhận thành công khoản chi 45,000 VND cho 'Cà phê sáng' vào danh mục 'Ăn uống'. Số dư ngân sách còn lại: 1,505,000 VND."
    },
    "latency_ms": 833.46
  },
  {
    "step": 2,
    "query": "Ghi lại giúp tôi một khoản chi 45000 VNĐ cho 'Cà phê sáng' vào danh mục 'Ăn uống' ngày 13/09/2026.",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Đã ghi nhận thành công khoản chi 45,000 VND cho 'Cà phê sáng' vào danh mục 'Ăn uống'. Số dư ngân sách còn lại: 1,505,000 VND.",
    "latency_ms": 10.0
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 / 5 test cases (TC01 trả lời trực tiếp từ kiến thức chung không gọi tool; TC02, TC03, TC04, TC05 đều kích hoạt Native Tool Calling chính xác).
- **Số lượng công cụ (Tools) công bố qua MCP Server:** 5 Tools chuẩn JSON Schema (`query_expense`, `add_expense`, `get_total_financial_summary`, `manage_category`, `list_categories`).
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
