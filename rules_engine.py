"""
Rules Engine - Loads and manages all AI rule files
Rules are loaded ONCE at startup and reused for all requests - massive token savings!
"""

from pathlib import Path
from typing import Dict, List
import json


class RulesEngine:
    """
    Loads all rule files once at startup.
    Rules stay in memory for entire session - massive token savings!
    
    Instead of sending full context with every request (800 tokens),
    we load rules once (~2,500 tokens) and send only relevant rules per request (~300-500 tokens).
    """
    
    def __init__(self, rules_dir='ai_rules', verbose=False):
        self.rules_dir = Path(rules_dir)
        self.rules = {}
        self.load_all_rules(verbose=verbose)
    
    def load_all_rules(self, verbose=False):
        """Load all markdown rule files into memory"""
        rule_files = [
            'bot_rules.md',
            'strategy_rules.md',
            'market_rules.md',
            'risk_rules.md',
            'response_templates.md',
            'indicator_rules.md',
            'language_rules.md',
            'personal_preference.md'
        ]
        for rule_file in rule_files:
            path = self.rules_dir / rule_file
            if path.exists():
                content = path.read_text(encoding='utf-8')
                rule_name = rule_file.replace('.md', '')
                self.rules[rule_name] = content
        if verbose:
            token_info = self.get_token_estimate()
            print(f"📊 AI rules: {token_info['total_rules']} files, ~{token_info['estimated_tokens']:,} tokens")
    
    def get_relevant_rules(self, intent: str) -> str:
        """
        Get only relevant rules for this intent (saves tokens)
        
        Instead of sending ALL rules every time, we send only what's needed:
        - Stock analysis → bot_rules + strategy + indicator + templates
        - News → bot_rules + templates + language
        - Positions → bot_rules + risk + templates
        
        This reduces context from ~2,500 tokens to ~300-800 tokens per request
        """
        rule_map = {
            'stock_analysis': [
                'bot_rules',
                'personal_preference',
                'strategy_rules',
                'market_rules',
                'indicator_rules',
                'response_templates'
            ],
            'news': [
                'bot_rules',
                'response_templates',
                'language_rules'
            ],
            'strategy': [
                'bot_rules',
                'personal_preference',
                'strategy_rules',
                'market_rules',
                'response_templates'
            ],
            'positions': [
                'bot_rules',
                'risk_rules',
                'response_templates',
                'language_rules'
            ],
            'performance': [
                'bot_rules',
                'risk_rules',
                'response_templates',
                'language_rules'
            ],
            'help': [
                'bot_rules',
                'response_templates',
                'language_rules'
            ],
            'general': [
                'bot_rules',
                'personal_preference',
                'language_rules'
            ]
        }
        
        # Get rules for this intent
        relevant_rule_names = rule_map.get(intent, ['bot_rules'])
        
        # Combine relevant rules
        combined_rules = "\n\n".join([
            f"# {name.upper().replace('_', ' ')}\n{self.rules[name]}"
            for name in relevant_rule_names
            if name in self.rules
        ])
        
        return combined_rules
    
    def get_rule(self, rule_name: str) -> str:
        """Get a specific rule by name"""
        return self.rules.get(rule_name, "")
    
    def get_all_rules(self) -> str:
        """Get all rules combined (use sparingly - sends all tokens)"""
        return "\n\n".join([
            f"# {name.upper().replace('_', ' ')}\n{content}"
            for name, content in self.rules.items()
        ])
    
    def get_token_estimate(self) -> Dict:
        """Estimate total tokens used by rules"""
        total_chars = sum(len(content) for content in self.rules.values())
        estimated_tokens = total_chars // 4  # Rough estimate: 1 token ≈ 4 chars
        
        return {
            'total_rules': len(self.rules),
            'total_characters': total_chars,
            'estimated_tokens': estimated_tokens,
            'loaded_rules': list(self.rules.keys()),
            'rules_detail': {
                name: {'chars': len(content), 'tokens': len(content) // 4}
                for name, content in self.rules.items()
            }
        }
    
    def get_token_savings(self, messages_per_day: int = 100) -> Dict:
        """
        Calculate estimated token savings vs loading rules every time
        
        Args:
            messages_per_day: Expected number of messages per day
        
        Returns:
            Dictionary with savings calculations
        """
        # Old system: Load all context every time
        old_tokens_per_request = 800  # Estimated
        old_total_daily = old_tokens_per_request * messages_per_day
        
        # New system: Load rules once, send only relevant per request
        rules_loaded_once = self.get_token_estimate()['estimated_tokens']
        new_tokens_per_request = 300  # Estimated average with relevant rules only
        new_total_daily = rules_loaded_once + (new_tokens_per_request * messages_per_day)
        
        # Calculate savings
        daily_savings = old_total_daily - new_total_daily
        monthly_savings = daily_savings * 30
        percentage_saved = (daily_savings / old_total_daily) * 100
        
        # Cost calculations (GPT-4o-mini pricing)
        # Input: $0.15 / 1M tokens, Output: $0.60 / 1M tokens
        # Assuming 50/50 split input/output
        cost_per_1k_tokens = 0.000375  # Average
        
        old_monthly_cost = (old_total_daily * 30 / 1000) * cost_per_1k_tokens
        new_monthly_cost = (new_total_daily * 30 / 1000) * cost_per_1k_tokens
        cost_savings = old_monthly_cost - new_monthly_cost
        
        return {
            'messages_per_day': messages_per_day,
            'old_system': {
                'tokens_per_request': old_tokens_per_request,
                'daily_tokens': old_total_daily,
                'monthly_tokens': old_total_daily * 30,
                'monthly_cost': f"${old_monthly_cost:.2f}"
            },
            'new_system': {
                'rules_loaded_once': rules_loaded_once,
                'tokens_per_request': new_tokens_per_request,
                'daily_tokens': new_total_daily,
                'monthly_tokens': new_total_daily * 30,
                'monthly_cost': f"${new_monthly_cost:.2f}"
            },
            'savings': {
                'daily_tokens': daily_savings,
                'monthly_tokens': monthly_savings,
                'percentage': f"{percentage_saved:.1f}%",
                'monthly_cost': f"${cost_savings:.2f}"
            }
        }
    
    def print_savings_report(self, messages_per_day: int = 100):
        """Print a formatted savings report"""
        savings = self.get_token_savings(messages_per_day)
        
        print("\n" + "=" * 60)
        print("💰 TOKEN SAVINGS REPORT")
        print("=" * 60)
        print(f"Based on {messages_per_day} messages/day:")
        print()
        print("📊 OLD SYSTEM (No rules optimization):")
        print(f"  • Per request: {savings['old_system']['tokens_per_request']} tokens")
        print(f"  • Daily: {savings['old_system']['daily_tokens']:,} tokens")
        print(f"  • Monthly cost: {savings['old_system']['monthly_cost']}")
        print()
        print("✨ NEW SYSTEM (With rules engine):")
        print(f"  • Rules loaded once: {savings['new_system']['rules_loaded_once']} tokens")
        print(f"  • Per request: {savings['new_system']['tokens_per_request']} tokens")
        print(f"  • Daily: {savings['new_system']['daily_tokens']:,} tokens")
        print(f"  • Monthly cost: {savings['new_system']['monthly_cost']}")
        print()
        print("🎉 SAVINGS:")
        print(f"  • Daily: {savings['savings']['daily_tokens']:,} tokens")
        print(f"  • Monthly: {savings['savings']['monthly_tokens']:,} tokens")
        print(f"  • Percentage: {savings['savings']['percentage']}")
        print(f"  • Monthly cost saved: {savings['savings']['monthly_cost']}")
        print("=" * 60 + "\n")
    
    def reload_rules(self):
        """Reload all rules from disk (useful for development)"""
        self.rules = {}
        self.load_all_rules()
        print("✅ Rules reloaded!")


# Test function
if __name__ == "__main__":
    print("🧪 TESTING RULES ENGINE\n")
    
    # Initialize
    engine = RulesEngine('ai_rules')
    
    # Test getting relevant rules for different intents
    intents_to_test = ['stock_analysis', 'news', 'positions', 'general']
    
    print("\n" + "=" * 60)
    print("📝 RELEVANT RULES BY INTENT")
    print("=" * 60)
    
    for intent in intents_to_test:
        rules = engine.get_relevant_rules(intent)
        tokens = len(rules) // 4
        print(f"\n{intent.upper()}:")
        print(f"  • Tokens: ~{tokens}")
        print(f"  • First 100 chars: {rules[:100]}...")
    
    # Print savings report
    engine.print_savings_report(messages_per_day=100)
    
    print("\n✅ Rules engine test complete!")
