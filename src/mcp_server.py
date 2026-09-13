"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPExpenseServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol cho Quản lý Chi tiêu Cá nhân
    """
    def __init__(self, server_name: str = "personal-expense-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        [TASK 2.1] HỌC VIÊN HOÀN THIỆN HÀM THỰC THI TOOL TRÊN MCP SERVER
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0
        """
        # 1. Gọi hàm dispatch_tool_call để lấy chuỗi JSON kết quả từ Tool Router
        raw_result = dispatch_tool_call(tool_name, arguments)
        
        # 2. Chuyển đổi chuỗi JSON kết quả thành Python Dictionary
        try:
            content = json.loads(raw_result)
        except Exception:
            content = {"raw": raw_result}
            
        # 3. Đóng gói phản hồi và trả về Dict theo đúng chuẩn giao thức MCP JSON-RPC 2.0
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }

# Alias tương thích ngược
MCPAcademicServer = MCPExpenseServer


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (personal-expense-mcp-server)")
    print("==========================================================")
    
    server = MCPExpenseServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")
    for t in tools:
        print(f"   - Tool: {t.get('name')} | {t.get('description')}")
    
    # Kiểm tra trạng thái TODO 1.2 (Tool Schema)
    has_valid_schemas = all(bool(t.get("parameters", {}).get("properties")) for t in tools)
    if not has_valid_schemas:
        print("⏳ [TODO 1.2]: Vẫn còn Tool chưa được định nghĩa properties đầy đủ trong 'src/tools.py'.")
    else:
        print("✅ [TODO 1.2]: Tất cả các Tool đã có schema JSON Schema đầy đủ.")

    # Kiểm tra trạng thái TODO 2.1 (call_tool)
    print("\n--- 🧪 TEST 1: Gọi Tool 'query_expense' qua MCP ---")
    test_query = server.call_tool("query_expense", {"category": "Ăn uống"})
    print(f"   Phản hồi JSON-RPC: {json.dumps(test_query, ensure_ascii=False, indent=2)}")

    print("\n--- 🧪 TEST 2: Gọi Tool 'add_expense' qua MCP ---")
    test_add = server.call_tool("add_expense", {"amount": 45000, "category": "Ăn uống", "note": "Cà phê sáng"})
    print(f"   Phản hồi JSON-RPC: {json.dumps(test_add, ensure_ascii=False, indent=2)}")

    print("\n--- 🧪 TEST 3: Gọi Tool 'get_total_financial_summary' qua MCP ---")
    test_summary = server.call_tool("get_total_financial_summary", {"month": "09/2026"})
    print(f"   Phản hồi JSON-RPC: {json.dumps(test_summary, ensure_ascii=False, indent=2)}")

    print("\n--- 🧪 TEST 4: Gọi Tool 'manage_category' qua MCP ---")
    test_manage = server.call_tool("manage_category", {"category": "Giải trí", "allocated_budget": 1200000})
    print(f"   Phản hồi JSON-RPC: {json.dumps(test_manage, ensure_ascii=False, indent=2)}")

    if test_query.get("result") and test_add.get("result") and test_summary.get("result") and test_manage.get("result"):
        print("\n🎉 [PASS CHECKPOINT 2]: MCP Server đã công bố và xử lý đầy đủ 5 Tools chuẩn JSON-RPC 2.0 hoàn toàn chính xác!")
    else:
        print("\n❌ [FAIL]: call_tool() chưa trả về đầy đủ kết quả.")
