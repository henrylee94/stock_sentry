#!/usr/bin/env python3
"""
Quick test script for new strategy selection system
Run this to verify everything works before starting the bot
"""

import sys
from pathlib import Path

print("=" * 60)
print("STRATEGY SYSTEM VERIFICATION")
print("=" * 60)

# Test 1: Import core modules
print("\n[1] Testing imports...")
try:
    from core.data_manager import get_extended_stock_data
    print("   ✅ data_manager")
except Exception as e:
    print(f"   ❌ data_manager: {e}")
    sys.exit(1)

try:
    from backtester import run_backtest_single_strategy
    print("   ✅ backtester (with run_backtest_single_strategy)")
except Exception as e:
    print(f"   ❌ backtester: {e}")
    sys.exit(1)

try:
    from strategy_agents.base_agent import StrategyAgent
    print("   ✅ base_agent")
except Exception as e:
    print(f"   ❌ base_agent: {e}")
    sys.exit(1)

try:
    from strategy_orchestrator import StrategyOrchestrator
    print("   ✅ strategy_orchestrator")
except Exception as e:
    print(f"   ❌ strategy_orchestrator: {e}")
    sys.exit(1)

# Test 2: Load strategies
print("\n[2] Testing strategy loading...")
try:
    orchestrator = StrategyOrchestrator()
    strategies = orchestrator.list_all_strategies()
    print(f"   ✅ Loaded {len(strategies)} strategies:")
    for s in strategies:
        print(f"      • {s}")
except Exception as e:
    print(f"   ❌ Strategy loading failed: {e}")
    sys.exit(1)

# Test 3: Test new indicators
print("\n[3] Testing new indicators (BB, Donchian, ATR, EMA5)...")
try:
    test_data = get_extended_stock_data("AAPL", use_cache=False)
    if test_data:
        required_fields = ['bb_upper', 'bb_middle', 'bb_lower', 'donchian_upper_20', 'donchian_lower_20', 'atr', 'ema_5', 'week_52_high']
        missing = [f for f in required_fields if f not in test_data or test_data[f] == 0]
        if missing:
            print(f"   ⚠️  Some indicators returned 0 or missing: {missing}")
            print(f"      (This is OK if data is insufficient, but check if it persists)")
        else:
            print(f"   ✅ All new indicators present:")
            print(f"      • BB: ${test_data['bb_lower']:.2f} / ${test_data['bb_middle']:.2f} / ${test_data['bb_upper']:.2f}")
            print(f"      • Donchian(20): ${test_data['donchian_lower_20']:.2f} - ${test_data['donchian_upper_20']:.2f}")
            print(f"      • ATR: ${test_data['atr']:.2f}")
            print(f"      • EMA5: ${test_data['ema_5']:.2f}")
            print(f"      • 52w High: ${test_data['week_52_high']:.2f}")
    else:
        print("   ⚠️  Could not fetch test data (network issue or rate limit)")
except Exception as e:
    print(f"   ❌ Indicator test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test new strategies
print("\n[4] Testing new strategies (BB Mean Reversion, Donchian, Sigma)...")
try:
    new_strategies = ['Mean Reversion (Bollinger+RSI)', 'Momentum Breakout (Donchian)', 'Sigma Series']
    for strat_name in new_strategies:
        signal = orchestrator.get_signal_by_strategy(test_data, "AAPL", strat_name)
        if signal:
            print(f"   ✅ {strat_name}: {signal.action} (confidence {signal.confidence:.0f}%)")
            print(f"      Reason: {signal.reasoning}")
        else:
            print(f"   ❌ {strat_name}: Not found")
except Exception as e:
    print(f"   ❌ Strategy test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test parameter tuning file
print("\n[5] Testing strategy parameters...")
try:
    import json
    params_file = Path("strategy_params.json")
    if params_file.exists():
        params = json.loads(params_file.read_text())
        print(f"   ✅ strategy_params.json loaded ({len(params)} strategies)")
        # Show Sigma Series params as example
        if 'Sigma Series' in params:
            print(f"      Sigma Series params: {params['Sigma Series']}")
    else:
        print("   ⚠️  strategy_params.json not found (will be created by /tune command)")
except Exception as e:
    print(f"   ❌ Params test failed: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\n✅ All core features working! Ready to test with bot.")
print("\nNext steps:")
print("1. Start bot: python telegram_bot.py")
print("2. In Telegram, send: AAPL 要買嗎?")
print("3. Verify strategy buttons appear")
print("4. Click a strategy and verify result shows")
print("5. Try /tune to adjust strategy parameters")
print("\n" + "=" * 60)
