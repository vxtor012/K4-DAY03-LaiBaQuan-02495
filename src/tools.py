"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND (PERSONAL EXPENSE MANAGEMENT)
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Hỗ trợ đầy đủ các tính năng: Tra cứu, Ghi chép chi tiêu, Báo cáo tài chính tổng quan, Quản lý danh mục & Ngân sách.
"""

import json
import time
from typing import Dict, Any, List

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2 & ENHANCEMENTS)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu tình hình chi tiêu và ngân sách theo từng danh mục
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
    },

    # Tool 3: Báo cáo tài chính tổng thể (Tổng số tiền, tổng chi, tổng dư)
    {
        "name": "get_total_financial_summary",
        "description": "Tra cứu bức tranh tổng quan tài chính toàn bộ ví: tổng hạn mức ngân sách, tổng số tiền đã chi, tổng số dư còn lại và tỷ lệ sử dụng ngân sách trên toàn bộ danh mục trong tháng.",
        "parameters": {
            "type": "object",
            "properties": {
                "month": {
                    "type": "string",
                    "description": "Tháng cần tổng kết theo định dạng MM/YYYY (mặc định: '09/2026')"
                }
            },
            "required": []
        }
    },

    # Tool 4: Quản lý danh mục & Thiết lập hạn mức ngân sách mới
    {
        "name": "manage_category",
        "description": "Tạo mới một danh mục chi tiêu hoặc cập nhật/điều chỉnh hạn mức ngân sách được cấp cho một danh mục trong ví.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tên danh mục chi tiêu cần tạo hoặc cập nhật (ví dụ: 'Giải trí', 'Y tế', 'Ăn uống')"
                },
                "allocated_budget": {
                    "type": "number",
                    "description": "Hạn mức ngân sách mới cấp cho danh mục bằng VNĐ (ví dụ: 2000000)"
                },
                "month": {
                    "type": "string",
                    "description": "Tháng áp dụng theo định dạng MM/YYYY (mặc định: '09/2026')"
                }
            },
            "required": ["category", "allocated_budget"]
        }
    },

    # Tool 5: Liệt kê danh sách tất cả các danh mục chi tiêu hiện có trong ví
    {
        "name": "list_categories",
        "description": "Liệt kê danh sách tất cả các danh mục chi tiêu hiện đang được theo dõi trong ví tài chính.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_details": {
                    "type": "boolean",
                    "description": "Hiển thị chi tiết ngân sách và số tiền đã chi của từng danh mục (mặc định: true)"
                }
            },
            "required": []
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


def execute_get_total_financial_summary(month: str = "09/2026") -> str:
    """Thực thi tổng kết toàn bộ tình hình tài chính các danh mục"""
    total_budget = sum(c["allocated_budget"] for c in MOCK_EXPENSE_DATABASE.values())
    total_spent = sum(c["spent"] for c in MOCK_EXPENSE_DATABASE.values())
    total_remaining = total_budget - total_spent
    ratio = round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0.0
    
    breakdown = []
    for cat in MOCK_EXPENSE_DATABASE.values():
        rem = cat["allocated_budget"] - cat["spent"]
        breakdown.append({
            "category": cat["category_name"],
            "budget": cat["allocated_budget"],
            "spent": cat["spent"],
            "remaining": rem,
            "status": "An toàn" if rem >= 0 else "Cảnh báo vượt"
        })
        
    return json.dumps({
        "status": "SUCCESS",
        "month": month,
        "data": {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "spending_ratio_pct": ratio,
            "currency": "VND",
            "categories_count": len(MOCK_EXPENSE_DATABASE),
            "categories_breakdown": breakdown
        },
        "message": (
            f"Báo cáo tài chính tháng {month}: "
            f"Tổng ngân sách: {int(total_budget):,} VND | "
            f"Đã chi: {int(total_spent):,} VND ({ratio}%) | "
            f"Tổng số dư còn lại: {int(total_remaining):,} VND."
        )
    }, ensure_ascii=False)


def execute_manage_category(category: str, allocated_budget: float, month: str = "09/2026") -> str:
    """Thực thi tạo mới hoặc cập nhật hạn mức ngân sách cho danh mục"""
    key = category.strip().upper()
    cat_data = MOCK_EXPENSE_DATABASE.get(key)
    budget_val = float(allocated_budget)
    
    if cat_data:
        old_budget = cat_data["allocated_budget"]
        cat_data["allocated_budget"] = budget_val
        remaining = budget_val - cat_data["spent"]
        cat_name = cat_data["category_name"]
        action_msg = f"Đã cập nhật hạn mức ngân sách cho danh mục '{cat_name}' từ {int(old_budget):,} VND thành {int(budget_val):,} VND."
    else:
        cat_name = category.strip()
        MOCK_EXPENSE_DATABASE[key] = {
            "category_name": cat_name,
            "allocated_budget": budget_val,
            "spent": 0.0,
            "currency": "VND",
            "month": month
        }
        remaining = budget_val
        action_msg = f"Đã tạo mới danh mục '{cat_name}' với hạn mức ngân sách ban đầu là {int(budget_val):,} VND."
        
    return json.dumps({
        "status": "SUCCESS",
        "category": cat_name,
        "allocated_budget": budget_val,
        "spent": MOCK_EXPENSE_DATABASE[key]["spent"],
        "remaining_budget": remaining,
        "currency": "VND",
        "message": f"{action_msg} Số dư khả dụng hiện tại: {int(remaining):,} VND."
    }, ensure_ascii=False)


def execute_list_categories(include_details: bool = True) -> str:
    """Thực thi liệt kê tất cả danh mục chi tiêu"""
    categories = [
        {
            "name": c["category_name"],
            "budget": c["allocated_budget"],
            "spent": c["spent"],
            "remaining": c["allocated_budget"] - c["spent"],
            "currency": c["currency"]
        }
        for c in MOCK_EXPENSE_DATABASE.values()
    ]
    return json.dumps({
        "status": "SUCCESS",
        "count": len(categories),
        "categories": categories,
        "message": f"Hiện có {len(categories)} danh mục chi tiêu trong ví: " + ", ".join([c["name"] for c in categories])
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "query_expense": execute_query_expense,
    "add_expense": execute_add_expense,
    "get_total_financial_summary": execute_get_total_financial_summary,
    "manage_category": execute_manage_category,
    "list_categories": execute_list_categories
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
