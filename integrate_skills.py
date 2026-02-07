"""
自动集成 Skills 到 telegram_bot.py
运行此脚本会自动添加 Skills 功能到你的 bot
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """备份原文件"""
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(filepath, backup_path)
    print(f"✅ 已备份: {backup_path}")
    return backup_path

def integrate_skills(filepath="telegram_bot.py"):
    """自动集成 Skills 到 telegram_bot.py"""
    
    if not os.path.exists(filepath):
        print(f"❌ 找不到文件: {filepath}")
        return False
    
    # 备份原文件
    backup_path = backup_file(filepath)
    
    print(f"📖 读取 {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📝 原文件: {len(lines)} 行")
    
    # 准备要插入的代码
    insertions = []
    
    # 1. Import SkillsetManager (after line with 'import pytz')
    for i, line in enumerate(lines):
        if 'import pytz' in line:
            insertions.append({
                'line': i + 1,
                'code': '''
# 🆕 Import SkillsetManager
try:
    from skillset_manager import SkillsetManager
    SKILLS_ENABLED = True
except ImportError:
    print("⚠️ skillset_manager not found - Skills disabled")
    SKILLS_ENABLED = False

'''
            })
            break
    
    # 2. Initialize SkillsetManager (after OpenAI client initialization)
    for i, line in enumerate(lines):
        if 'print("⚠️ OPENAI_KEY not found")' in line:
            insertions.append({
                'line': i + 1,
                'code': '''
# 🆕 Initialize SkillsetManager
skills_manager = None
if SKILLS_ENABLED:
    try:
        skills_manager = SkillsetManager("skills")
        print(skills_manager.get_skills_summary())
    except Exception as e:
        print(f"⚠️ Skills 加载失败: {e}")
        skills_manager = None

'''
            })
            break
    
    # 3. Update version string
    for i, line in enumerate(lines):
        if 'GEEWONI AI 交易大脑 v7.0' in line:
            lines[i] = line.replace('v7.0', 'v7.1 - with Skills')
            print(f"✅ 更新版本号: 第 {i+1} 行")
            break
    
    # 4. Add trend_en to get_extended_stock_data result
    for i, line in enumerate(lines):
        if "'trend': trend," in line and 'result = {' in ''.join(lines[max(0,i-20):i]):
            # 在 'trend': trend 后面添加 trend_en
            indent = len(line) - len(line.lstrip())
            insertions.append({
                'line': i + 1,
                'code': f"{' ' * indent}'trend_en': 'bullish' if current_price > ema_9 else 'bearish',\n"
            })
            break
    
    # 5. Add skills recommendation in ai_brain (after building stock_data_context)
    for i, line in enumerate(lines):
        if "stock_data_context += f\"\"\"" in line and i > 400:
            # 找到 stock_data_context 构建完成的位置
            # 向下找到构建完成的地方
            j = i
            while j < len(lines) and '"""' not in lines[j+1]:
                j += 1
            
            if j < len(lines) - 10:
                insertions.append({
                    'line': j + 2,
                    'code': '''            
            # 🆕 添加技能推荐
            if skills_manager:
                recommended_skills = []
                for sym, data in stock_data.items():
                    market_condition = {
                        'trend': data.get('trend_en', 'neutral'),
                        'rsi': data.get('rsi', 50),
                        'volume_ratio': data.get('volume_ratio', 1.0),
                        'volatility': 'normal'
                    }
                    skills = skills_manager.match_skill_to_market(market_condition)
                    recommended_skills.extend(skills)
                
                # 去重
                recommended_skills = list(set(recommended_skills))[:3]
                if recommended_skills:
                    stock_data_context += "\\n\\n📚 推荐策略:\\n"
                    for skill_name in recommended_skills:
                        skill = skills_manager.get_skill(skill_name)
                        if skill:
                            stock_data_context += f"• {skill['name']} ({skill['difficulty']}): {skill['description']}\\n"
'''
                })
            break
    
    # 6. Add /skills and /skill commands (after learn_command)
    for i, line in enumerate(lines):
        if 'async def learn_command' in line:
            # 找到这个函数的结束位置
            j = i
            indent_count = 0
            while j < len(lines):
                if 'async def ' in lines[j] and j > i:
                    # 找到下一个函数
                    break
                j += 1
            
            insertions.append({
                'line': j,
                'code': '''
async def skills_command(update: Update, context):
    """显示所有可用策略"""
    if not skills_manager:
        await update.message.reply_text("⚠️ Skills 系统未加载")
        return
    
    summary = skills_manager.get_skills_summary()
    beginner_skills = skills_manager.get_recommended_skills_for_beginner()
    
    response = f"{summary}\\n\\n🎓 <b>初学者推荐:</b>\\n"
    for skill_name in beginner_skills:
        response += f"• {skill_name}\\n"
    
    response += "\\n💡 使用 /skill [名称] 查看详情"
    await update.message.reply_text(response, parse_mode='HTML')

async def skill_detail_command(update: Update, context):
    """显示特定策略详情"""
    if not skills_manager:
        await update.message.reply_text("⚠️ Skills 系统未加载")
        return
    
    if not context.args:
        await update.message.reply_text(
            "使用方法: /skill [策略名称]\\n\\n"
            "例如: /skill EMA Crossover\\n\\n"
            "查看所有策略: /skills"
        )
        return
    
    skill_name = ' '.join(context.args)
    skill = skills_manager.get_skill(skill_name)
    
    if not skill:
        await update.message.reply_text(f"❌ 找不到策略: {skill_name}\\n\\n查看所有策略: /skills")
        return
    
    entry_conditions = skill['rules'].get('entry_conditions', [])
    if isinstance(entry_conditions, list):
        entry_text = '\\n'.join([f"  • {c}" for c in entry_conditions[:3]])
    else:
        entry_text = "  见策略详情"
    
    response = f"""📖 <b>{skill['name']}</b>

<b>类型:</b> {skill['type']}
<b>难度:</b> {skill['difficulty']}
<b>描述:</b> {skill['description']}

<b>📈 入场条件:</b>
{entry_text}

<b>🛑 止损:</b> {skill['rules'].get('stop_loss', 'N/A')}
<b>💰 仓位:</b> {skill['rules'].get('position_size', 'N/A')}

<b>📊 表现:</b>
胜率: {skill['performance']['win_rate']:.1f}%
交易: {skill['performance']['total_trades']}
盈亏: ${skill['performance']['total_pnl']:.2f}

<b>💡 注意:</b> {skill.get('notes', 'N/A')}
"""
    await update.message.reply_text(response, parse_mode='HTML')

'''
            })
            break
    
    # 7. Update /start command to mention skills
    for i, line in enumerate(lines):
        if '"/learn - AI 学习报告' in line:
            lines[i] = line.replace(
                '"/learn - AI 学习报告',
                '"/skills - 查看策略库 🆕\\n"  # 新增\n        f"/skill [名称] - 策略详情 🆕\\n"  # 新增\n        f"/learn - AI 学习报告'
            )
            print(f"✅ 更新 /start 命令: 第 {i+1} 行")
            break
    
    # 8. Register new command handlers in main()
    for i, line in enumerate(lines):
        if 'application.add_handler(CommandHandler("learn", learn_command))' in line:
            insertions.append({
                'line': i + 1,
                'code': '    application.add_handler(CommandHandler("skills", skills_command))  # 🆕\n    application.add_handler(CommandHandler("skill", skill_detail_command))  # 🆕\n'
            })
            break
    
    # 按行号排序插入点（从后往前插入，避免行号变化）
    insertions.sort(key=lambda x: x['line'], reverse=True)
    
    # 执行插入
    for insertion in insertions:
        line_num = insertion['line']
        code = insertion['code']
        lines.insert(line_num, code)
        print(f"✅ 插入代码: 第 {line_num} 行后")
    
    # 写入新文件
    output_path = filepath
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\n✅ 集成完成!")
    print(f"📝 新文件: {len(lines)} 行 (增加了 {len(lines) - len(lines)} 行)")
    print(f"💾 已保存: {output_path}")
    print(f"📦 备份: {backup_path}")
    print(f"\n🚀 现在可以运行: py -3.12 telegram_bot.py")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 GEEWONI Skills 自动集成工具")
    print("=" * 60)
    print()
    
    # 检查文件
    if not os.path.exists("telegram_bot.py"):
        print("❌ 找不到 telegram_bot.py")
        print("   请确保在正确的文件夹运行此脚本")
        exit(1)
    
    if not os.path.exists("skillset_manager.py"):
        print("❌ 找不到 skillset_manager.py")
        print("   请确保 skillset_manager.py 在同一文件夹")
        exit(1)
    
    if not os.path.exists("skills"):
        print("❌ 找不到 skills 文件夹")
        print("   请确保 skills/ 文件夹存在")
        exit(1)
    
    print("✅ 所有文件检查通过")
    print()
    
    # 确认
    response = input("是否开始集成? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        exit(0)
    
    print()
    
    # 执行集成
    success = integrate_skills()
    
    if success:
        print()
        print("=" * 60)
        print("🎉 集成成功!")
        print("=" * 60)
        print()
        print("📋 下一步:")
        print("1. 运行: py -3.12 telegram_bot.py")
        print("2. 测试: /start, /skills, /skill EMA Crossover")
        print("3. 查看: NVDA 入场点?")
        print()
    else:
        print()
        print("❌ 集成失败")
        print("请检查错误信息")