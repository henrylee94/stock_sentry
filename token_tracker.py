"""
Token 使用追踪系统
实时监控 OpenAI API 使用量和成本
"""

import json
from pathlib import Path
from datetime import datetime, date
import tiktoken

class TokenTracker:
    """Token 使用追踪器"""
    
    def __init__(self, log_file="token_usage.json"):
        self.log_file = Path(log_file)
        self.encoder = tiktoken.encoding_for_model("gpt-4o-mini")
        self.usage_data = self.load_usage()
        
        # GPT-4o-mini 定价 (2025)
        self.pricing = {
            "input": 0.15 / 1_000_000,   # $0.15 per 1M tokens
            "output": 0.60 / 1_000_000,  # $0.60 per 1M tokens
        }
    
    def load_usage(self):
        """加载使用记录"""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        
        return {
            "total": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0
            },
            "today": {
                "date": str(date.today()),
                "input_tokens": 0,
                "output_tokens": 0,
                "requests": 0,
                "cost": 0
            },
            "history": []
        }
    
    def save_usage(self):
        """保存使用记录"""
        with open(self.log_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def count_tokens(self, text):
        """计算文本的 token 数量"""
        try:
            return len(self.encoder.encode(text))
        except:
            # 简单估算: 1 token ≈ 4 字符
            return len(text) // 4
    
    def log_request(self, prompt, response, model="gpt-4o-mini"):
        """记录一次 API 请求"""
        # 计算 tokens
        input_tokens = self.count_tokens(prompt)
        output_tokens = self.count_tokens(response)
        
        # 计算成本
        input_cost = input_tokens * self.pricing["input"]
        output_cost = output_tokens * self.pricing["output"]
        total_cost = input_cost + output_cost
        
        # 检查是否是新的一天
        today_str = str(date.today())
        if self.usage_data["today"]["date"] != today_str:
            # 保存昨天的数据到历史
            self.usage_data["history"].append(self.usage_data["today"])
            
            # 重置今日数据
            self.usage_data["today"] = {
                "date": today_str,
                "input_tokens": 0,
                "output_tokens": 0,
                "requests": 0,
                "cost": 0
            }
        
        # 更新今日统计
        self.usage_data["today"]["input_tokens"] += input_tokens
        self.usage_data["today"]["output_tokens"] += output_tokens
        self.usage_data["today"]["requests"] += 1
        self.usage_data["today"]["cost"] += total_cost
        
        # 更新总计
        self.usage_data["total"]["input_tokens"] += input_tokens
        self.usage_data["total"]["output_tokens"] += output_tokens
        self.usage_data["total"]["total_cost"] += total_cost
        
        # 保存
        self.save_usage()
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": total_cost,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_today_usage(self):
        """获取今日使用情况"""
        today_str = str(date.today())
        if self.usage_data["today"]["date"] != today_str:
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "requests": 0,
                "cost": 0
            }
        
        today = self.usage_data["today"]
        return {
            "input_tokens": today["input_tokens"],
            "output_tokens": today["output_tokens"],
            "total_tokens": today["input_tokens"] + today["output_tokens"],
            "requests": today["requests"],
            "cost": today["cost"]
        }
    
    def get_total_usage(self):
        """获取总使用情况"""
        total = self.usage_data["total"]
        return {
            "input_tokens": total["input_tokens"],
            "output_tokens": total["output_tokens"],
            "total_tokens": total["input_tokens"] + total["output_tokens"],
            "total_cost": total["total_cost"]
        }
    
    def get_weekly_usage(self):
        """获取本周使用情况"""
        # 获取最近7天的数据
        recent = self.usage_data["history"][-7:] + [self.usage_data["today"]]
        
        total_input = sum(day["input_tokens"] for day in recent)
        total_output = sum(day["output_tokens"] for day in recent)
        total_cost = sum(day["cost"] for day in recent)
        total_requests = sum(day["requests"] for day in recent)
        
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "requests": total_requests,
            "cost": total_cost
        }
    
    def get_statistics(self):
        """获取完整统计"""
        today = self.get_today_usage()
        weekly = self.get_weekly_usage()
        total = self.get_total_usage()
        
        return {
            "today": today,
            "weekly": weekly,
            "total": total,
            "avg_tokens_per_request": total["total_tokens"] / max(today["requests"], 1),
            "avg_cost_per_request": today["cost"] / max(today["requests"], 1)
        }
    
    def format_usage_display(self):
        """格式化显示使用情况"""
        stats = self.get_statistics()
        
        return f"""
📊 Token 使用统计

【今日】
• Tokens: {stats['today']['total_tokens']:,} ({stats['today']['input_tokens']:,} in + {stats['today']['output_tokens']:,} out)
• 请求数: {stats['today']['requests']}
• 成本: ${stats['today']['cost']:.4f}

【本周】
• Tokens: {stats['weekly']['total_tokens']:,}
• 请求数: {stats['weekly']['requests']}
• 成本: ${stats['weekly']['cost']:.4f}

【总计】
• Tokens: {stats['total']['total_tokens']:,}
• 成本: ${stats['total']['total_cost']:.4f}
"""

# 创建全局实例
token_tracker = TokenTracker()

# 使用示例
if __name__ == "__main__":
    # 模拟一次 API 调用
    prompt = "分析 NVDA 股票的入场点"
    response = "根据技术分析，NVDA 当前价格 $147.50，建议在 $146.80-147.20 入场..."
    
    result = token_tracker.log_request(prompt, response)
    
    print("本次请求:")
    print(f"Input tokens: {result['input_tokens']}")
    print(f"Output tokens: {result['output_tokens']}")
    print(f"Cost: ${result['cost']:.6f}")
    
    print("\n" + token_tracker.format_usage_display())