"""
SkillsetManager - 管理所有交易技能
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

class SkillsetManager:
    """管理和使用交易技能库"""
    
    def __init__(self, skills_dir: str = "skills", verbose=False):
        self.skills_dir = Path(skills_dir)
        self.skills = {}
        self.load_all_skills(verbose=verbose)
    
    def load_all_skills(self, verbose=False):
        """加载所有技能文件"""
        if not self.skills_dir.exists():
            if verbose:
                print(f"⚠️ Skills directory not found: {self.skills_dir}")
            return
        for skill_file in self.skills_dir.rglob("*.json"):
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    skill_data = json.load(f)
                    self.skills[skill_data['name']] = skill_data
            except Exception as e:
                if verbose:
                    print(f"❌ Failed to load {skill_file}: {e}")
    
    def get_skill(self, name: str) -> Optional[Dict]:
        """获取特定技能"""
        return self.skills.get(name)
    
    def list_skills(self, category: Optional[str] = None, 
                   difficulty: Optional[str] = None) -> List[str]:
        """列出技能"""
        filtered_skills = []
        
        for name, skill in self.skills.items():
            if category and skill.get('category') != category:
                continue
            if difficulty and skill.get('difficulty') != difficulty:
                continue
            filtered_skills.append(name)
        
        return filtered_skills
    
    def get_skills_by_market_condition(self, condition: str) -> List[Dict]:
        """根据市场环境获取适合的策略"""
        suitable_skills = []
        
        for name, skill in self.skills.items():
            best_for = skill.get('best_for', [])
            if condition in best_for or condition in skill.get('category', ''):
                suitable_skills.append(skill)
        
        return suitable_skills
    
    def rank_skills_by_performance(self) -> List[tuple]:
        """根据表现排名策略"""
        skill_performance = []
        
        for name, skill in self.skills.items():
            perf = skill.get('performance', {})
            if perf.get('total_trades', 0) > 0:
                skill_performance.append((
                    name,
                    perf.get('win_rate', 0),
                    perf.get('profit_factor', 0),
                    perf.get('total_pnl', 0)
                ))
        
        # 按胜率排序
        return sorted(skill_performance, key=lambda x: x[1], reverse=True)
    
    def update_skill_performance(self, skill_name: str, trade_result: Dict):
        """更新技能表现"""
        skill = self.get_skill(skill_name)
        if not skill:
            return
        
        perf = skill['performance']
        perf['total_trades'] += 1
        
        if trade_result['profit'] > 0:
            perf['wins'] += 1
        else:
            perf['losses'] += 1
        
        perf['win_rate'] = (perf['wins'] / perf['total_trades'] * 100)
        perf['total_pnl'] += trade_result['profit']
        
        # 保存更新
        self.save_skill(skill_name, skill)
    
    def save_skill(self, skill_name: str, skill_data: Dict):
        """保存技能更新"""
        # 找到原始文件路径
        for skill_file in self.skills_dir.rglob("*.json"):
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data['name'] == skill_name:
                        with open(skill_file, 'w', encoding='utf-8') as f:
                            json.dump(skill_data, f, indent=2, ensure_ascii=False)
                        print(f"💾 Updated skill: {skill_name}")
                        return
            except:
                pass
    
    def get_recommended_skills_for_beginner(self) -> List[str]:
        """推荐初学者技能"""
        return self.list_skills(difficulty='beginner')
    
    def get_skills_summary(self) -> str:
        """获取技能库摘要"""
        total = len(self.skills)
        by_category = {}
        by_difficulty = {}
        
        for skill in self.skills.values():
            # 按类别统计
            cat = skill.get('type', 'unknown')
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # 按难度统计
            diff = skill.get('difficulty', 'unknown')
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
        
        summary = f"""
📚 技能库摘要
━━━━━━━━━━━━━━━━━━━━━━
总技能数: {total}

按类别:
"""
        for cat, count in by_category.items():
            summary += f"  • {cat}: {count}\n"
        
        summary += "\n按难度:\n"
        for diff, count in by_difficulty.items():
            summary += f"  • {diff}: {count}\n"
        
        return summary
    
    def match_skill_to_market(self, market_data: Dict) -> List[str]:
        """根据市场数据匹配最佳策略"""
        recommendations = []
        
        # 分析市场环境
        trend = market_data.get('trend', '')
        volatility = market_data.get('volatility', 'normal')
        rsi = market_data.get('rsi', 50)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        # 趋势市场
        if 'bull' in trend.lower() or '看涨' in trend:
            recommendations.append('Trend Following')
            recommendations.append('EMA Crossover')
            if volume_ratio > 1.5:
                recommendations.append('Volume Breakout')
        
        # 震荡市场
        elif 'sideways' in market_data.get('market_condition', '') or '震荡' in trend:
            recommendations.append('Mean Reversion')
            recommendations.append('Support Resistance Bounce')
        
        # 超买超卖
        if rsi < 30:
            recommendations.append('RSI Divergence')
            recommendations.append('Mean Reversion')
        elif rsi > 70:
            recommendations.append('Mean Reversion')
        
        # 高波动
        if volatility == 'high' or market_data.get('vix', 0) > 25:
            recommendations.append('Volatility Trading')
        
        return recommendations


# 使用示例
if __name__ == "__main__":
    # 初始化管理器
    manager = SkillsetManager()
    
    # 查看摘要
    print(manager.get_skills_summary())
    
    # 获取初学者技能
    print("\n🎓 初学者推荐:")
    for skill_name in manager.get_recommended_skills_for_beginner():
        print(f"  • {skill_name}")
    
    # 查看特定技能
    ema_skill = manager.get_skill("EMA Crossover")
    if ema_skill:
        print(f"\n📖 {ema_skill['name']}")
        print(f"   描述: {ema_skill['description']}")
        print(f"   难度: {ema_skill['difficulty']}")
        print(f"   胜率: {ema_skill['performance']['win_rate']:.1f}%")
    
    # 根据市场匹配策略
    market_data = {
        'trend': '强势看涨',
        'rsi': 55,
        'volume_ratio': 2.1,
        'volatility': 'normal'
    }
    
    print(f"\n🎯 当前市场推荐策略:")
    for skill_name in manager.match_skill_to_market(market_data):
        print(f"  • {skill_name}")
    
    # 查看表现最佳的策略
    print(f"\n🏆 表现最佳策略:")
    top_skills = manager.rank_skills_by_performance()[:5]
    for name, win_rate, pf, pnl in top_skills:
        print(f"  • {name}: 胜率 {win_rate:.1f}%, 盈亏比 {pf:.2f}, P&L ${pnl:.2f}")
