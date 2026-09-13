"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND (PERSONAL EXPENSE MANAGEMENT)
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
import time
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu tình hình chi tiêu và ngân sách theo danh mục
    {
        "name": "query_expense",
        "description": "Tra cứu tình hình chi tiêu, hạn mức ngân sách và số dư còn lại của một danh mục chi tiêu trong tháng.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tên danh mục chi tiêu cần tra cứu (ví dụ: 'Ăn uống', 'Mua sắm', 'Di chuyển', 'Học tập')"
                },
                "month": {
                    "type": "string",
                    "description": "Tháng cần tra cứu theo định dạng MM/YYYY (ví dụ: '09/2026')"
                }
            },
            "required": ["category"]
        }
    },
    
    # Tool 2: Ghi nhận giao dịch chi tiêu mới vào danh mục
    {
        "name": "add_expense",
        "description": "Ghi nhận thêm một khoản giao dịch chi tiêu mới vào danh mục chi tiêu tương ứng.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Số tiền chi tiêu bằng VNĐ (ví dụ: 45000, 800000)"
                },
                "category": {
                    "type": "string",
                    "description": "Tên danh mục chi tiêu (ví dụ: 'Ăn uống', 'Mua sắm', 'Di chuyển', 'Học tập')"
                },
                "note": {
                    "type": "string",
                    "description": "Nội dung hoặc ghi chú của khoản chi (ví dụ: 'Cà phê sáng', 'Áo khoác gió')"
                },
                "date": {
                    "type": "string",
                    "description": "Ngày phát sinh chi tiêu định dạng DD/MM/YYYY (ví dụ: '13/09/2026')"
                }
            },
            "required": ["amount", "category", "note"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_EXPENSE_DATABASE = {
    "ĂN UỐNG": {
        "category_name": "Ăn uống",
        "allocated_budget": 3000000,
        "spent": 1450000,
        "currency": "VND",
        "month": "09/2026"
    },
    "MUA SẮM": {
        "category_name": "Mua sắm",
        "allocated_budget": 1500000,
        "spent": 600000,
        "currency": "VND",
        "month": "09/2026"
    },
    "DI CHUYỂN": {
        "category_name": "Di chuyển",
        "allocated_budget": 500000,
        "spent": 210000,
        "currency": "VND",
        "month": "09/2026"
    },
    "HỌC TẬP": {
        "category_name": "Học tập",
        "allocated_budget": 1000000,
        "spent": 350000,
        "currency": "VND",
        "month": "09/2026"
    }
}


def execute_query_expense(category: str, month: str = "09/2026") -> str:
    """Thực thi tra cứu chi tiêu và ngân sách theo danh mục"""
    key = category.strip().upper()
    cat_data = MOCK_EXPENSE_DATABASE.get(key)
    
    if cat_data:
        allocated = cat_data["allocated_budget"]
        spent = cat_data["spent"]
        remaining = allocated - spent
        status = "Còn trong hạn mức" if remaining >= 0 else "Đã vượt hạn mức"
        
        return json.dumps({
            "status": "SUCCESS",
            "category": cat_data["category_name"],
            "month": month,
            "data": {
                "allocated_budget": allocated,
                "spent": spent,
                "remaining_budget": remaining,
                "currency": cat_data["currency"],
                "status": status
            }
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy danh mục chi tiêu '{category}' trong hệ thống ví."
        }, ensure_ascii=False)


def execute_add_expense(amount: float, category: str, note: str, date: str = "13/09/2026") -> str:
    """Thực thi ghi nhận khoản chi tiêu mới vào danh mục"""
    key = category.strip().upper()
    cat_data = MOCK_EXPENSE_DATABASE.get(key)
    
    if cat_data:
        cat_data["spent"] += float(amount)
        new_spent = cat_data["spent"]
        remaining = cat_data["allocated_budget"] - new_spent
        cat_name = cat_data["category_name"]
    else:
        # Nếu danh mục mới, khởi tạo mặc định
        MOCK_EXPENSE_DATABASE[key] = {
            "category_name": category.strip(),
            "allocated_budget": 1000000,
            "spent": float(amount),
            "currency": "VND",
            "month": "09/2026"
        }
        new_spent = float(amount)
        remaining = 1000000 - new_spent
        cat_name = category.strip()
        
    tx_id = f"TX-{int(time.time() * 1000) % 1000000:06d}"
    return json.dumps({
        "status": "SUCCESS",
        "transaction_id": tx_id,
        "amount": float(amount),
        "category": cat_name,
        "note": note,
        "date": date,
        "current_spent": new_spent,
        "remaining_budget": remaining,
        "message": f"Đã ghi nhận thành công khoản chi {int(amount):,} VND cho '{note}' vào danh mục '{cat_name}'. Số dư ngân sách còn lại: {int(remaining):,} VND."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "query_expense": execute_query_expense,
    "add_expense": execute_add_expense
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
