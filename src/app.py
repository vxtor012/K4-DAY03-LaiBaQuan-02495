"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    FINAL_RESPONSE_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

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

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Hỗ trợ chuỗi suy luận đa bước thực thụ (Multi-step Tool Calling qua nhiều vòng lặp liên tiếp).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    current_prompt = f"Yêu cầu từ người dùng: {user_query}\n"
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với Native Tool Calling Specs và ngữ cảnh tích lũy các bước trước
        llm_response = provider.generate_with_tools(current_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp (kết luận mục tiêu)
        if llm_response.get("type") == "text":
            raw_content = llm_response.get("content", "").strip()
            
            # Nếu LLM vô tình sinh đoạn văn bản mô tả kỹ thuật kiểu '(Thực hiện gọi công cụ...)'
            if ("thực hiện" in raw_content.lower() and "công cụ" in raw_content.lower()) or raw_content.startswith("*("):
                try:
                    synth_prompt = (
                        f"Yêu cầu ban đầu của người dùng: '{user_query}'\n"
                        f"Dữ liệu và kết quả các bước đã thực hiện:\n{current_prompt}\n"
                        f"Hãy trả lời trực tiếp cho người dùng kết quả tài chính, lời khuyên và xác nhận các khoản đã ghi nhận."
                    )
                    raw_content = provider.generate(synth_prompt, system_prompt=FINAL_RESPONSE_SYSTEM_PROMPT)
                except Exception:
                    pass
                    
            final_content = clean_final_answer(raw_content)
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            obs_str = json.dumps(obs_data, ensure_ascii=False)
            print(f"👁️ [Observation từ MCP Server]: {obs_str}")
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            # Nạp kết quả Observation vào ngữ cảnh để LLM tiếp tục suy luận ở Step tiếp theo
            current_prompt += (
                f"\n[Bước {step}]:\n"
                f"- Thought: {thought}\n"
                f"- Action: {tool_name}({json.dumps(arguments, ensure_ascii=False)})\n"
                f"- Observation: {obs_str}\n"
                f"Hướng dẫn suy luận: Hãy phân tích kết quả Observation trên. Nếu cần thực hiện tiếp hành động khác (ví dụ gọi thêm công cụ như add_expense, query_expense...), hãy tiếp tục phát sinh Tool Call. Nếu đã hoàn thành đầy đủ mục tiêu của người dùng, hãy phản hồi câu trả lời cuối cùng trực tiếp bằng văn bản (Final Answer) mà không gọi thêm công cụ. Tuyệt đối không viết 'Thought:' hay 'Action:' trong câu trả lời văn bản.\n"
            )
            # Tiếp tục vòng lặp để LLM xem xét Observation và quyết định bước tiếp theo!

    # Nếu sau MAX_ITERATIONS chưa có văn bản kết luận, tổng hợp lần cuối
    if not any(t.get("action_type") == "FINAL_ANSWER" for t in trace_logs):
        synthesis_prompt = (
            f"Yêu cầu từ người dùng: '{user_query}'\n"
            f"Quá trình thực thi qua các công cụ:\n{current_prompt}\n"
            f"Hãy đưa ra câu trả lời trực tiếp, rõ ràng cho người dùng về kết quả cuối cùng. "
            f"Tuyệt đối không viết nhãn 'Thought:' hay 'Action:'."
        )
        try:
            synth_res = provider.generate(synthesis_prompt, system_prompt=FINAL_RESPONSE_SYSTEM_PROMPT)
            final_ans = clean_final_answer(synth_res)
        except Exception:
            final_ans = "Đã hoàn tất xử lý các thao tác tài chính theo yêu cầu của bạn."
            
        print(f"🏁 [Final Answer]: {final_ans}")
        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Tổng hợp kết luận sau chuỗi ReAct đa bước.",
            "output": final_ans,
            "latency_ms": 10.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("💰 PERSONAL EXPENSE RE-ACT AGENT (MCP ENHANCED)")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy tắc quản lý chi tiêu 50/30/20 là gì?'")
        print("   - Tra cứu danh mục: 'Hãy tra cứu tình hình chi tiêu của danh mục Ăn uống'")
        print("   - Ghi nhận chi tiêu: 'Ghi lại khoản chi 45000 VNĐ cho Cà phê sáng vào danh mục Ăn uống'")
        print("   - Tổng tài chính ví: 'Tổng kết ngân sách và chi tiêu của tôi trong tháng này thế nào?'")
        print("   - Quản lý danh mục: 'Thêm danh mục Giải trí với hạn mức ngân sách 1500000 VNĐ'")
        print("   - Liệt kê danh mục: 'Cho tôi xem danh sách tất cả các danh mục chi tiêu hiện có'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Người dùng hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu chi tiêu) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
