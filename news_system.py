"""
新闻抓取和过滤系统
自动抓取、分析、过滤重要新闻
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json
from pathlib import Path

class NewsSystem:
    """新闻系统 - 抓取、过滤、分析"""
    
    def __init__(self, client, watchlist):
        self.client = client  # OpenAI client
        self.watchlist = watchlist  # ['NVDA', 'PLTR', ...]
        self.news_cache_file = Path("news_cache.json")
        self.seen_news = self.load_seen_news()
    
    def load_seen_news(self):
        """加载已读新闻（避免重复推送）"""
        if self.news_cache_file.exists():
            return set(json.loads(self.news_cache_file.read_text()))
        return set()
    
    def save_seen_news(self):
        """保存已读新闻"""
        self.news_cache_file.write_text(json.dumps(list(self.seen_news)))
    
    def fetch_news_rss(self) -> List[Dict]:
        """从 RSS 源抓取新闻"""
        news_items = []
        
        # RSS 源列表
        rss_feeds = [
            # Yahoo Finance - 你的 watchlist
            *[f"https://finance.yahoo.com/rss/headline?s={symbol}" for symbol in self.watchlist],
            
            # SeekingAlpha - Market news
            "https://seekingalpha.com/feed.xml",
            
            # MarketWatch
            "https://www.marketwatch.com/rss/topstories",
            
            # CNBC
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # 每个源取5条
                    news_id = entry.get('id', entry.get('link', ''))
                    
                    # 跳过已读新闻
                    if news_id in self.seen_news:
                        continue
                    
                    news_items.append({
                        'id': news_id,
                        'title': entry.title,
                        'link': entry.link,
                        'summary': entry.get('summary', '')[:300],
                        'published': entry.get('published', ''),
                        'source': feed_url
                    })
                    
            except Exception as e:
                print(f"⚠️ RSS 抓取失败 {feed_url}: {e}")
        
        return news_items
    
    def fetch_news_api(self) -> List[Dict]:
        """从 News API 抓取新闻（需要 API key）"""
        # 可选：使用 newsapi.org
        # 免费版每天 100 requests
        
        api_key = "YOUR_NEWS_API_KEY"  # https://newsapi.org/
        if not api_key or api_key == "YOUR_NEWS_API_KEY":
            return []
        
        news_items = []
        
        # 搜索你的 watchlist 股票
        for symbol in self.watchlist:
            try:
                url = f"https://newsapi.org/v2/everything?q={symbol}&language=en&sortBy=publishedAt&apiKey={api_key}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                for article in data.get('articles', [])[:5]:
                    news_id = article.get('url', '')
                    
                    if news_id in self.seen_news:
                        continue
                    
                    news_items.append({
                        'id': news_id,
                        'title': article['title'],
                        'link': article['url'],
                        'summary': article.get('description', '')[:300],
                        'published': article.get('publishedAt', ''),
                        'source': 'NewsAPI',
                        'symbol': symbol
                    })
                    
            except Exception as e:
                print(f"⚠️ News API 失败 {symbol}: {e}")
        
        return news_items
    
    async def filter_important_news(self, news_items: List[Dict]) -> List[Dict]:
        """AI 过滤重要新闻"""
        if not news_items:
            return []
        
        # 构建新闻列表
        news_text = ""
        for i, news in enumerate(news_items[:20]):  # 最多分析20条
            news_text += f"{i+1}. {news['title']}\n"
        
        prompt = f"""你是专业的金融新闻分析师。请从以下新闻中筛选出**真正重要**的新闻。

我的关注股票: {', '.join(self.watchlist)}

新闻列表:
{news_text}

筛选标准:
- ⭐⭐⭐ 高影响: 财报、产品发布、收购、FDA批准、重大合同
- ⭐⭐ 中影响: 分析师评级变化、行业趋势、政策变化
- ⭐ 低影响: 常规新闻、无关信息

只返回 JSON 格式:
{{
    "important_news": [1, 5, 8],  // 重要新闻的序号
    "reasons": ["原因1", "原因2", "原因3"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )
            
            # 解析 AI 返回
            result_text = response.choices[0].message.content
            # 提取 JSON
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                important_indices = result.get('important_news', [])
                reasons = result.get('reasons', [])
                
                # 筛选重要新闻
                important_news = []
                for idx in important_indices:
                    if 1 <= idx <= len(news_items):
                        news = news_items[idx - 1].copy()
                        news['ai_reason'] = reasons[len(important_news)] if len(important_news) < len(reasons) else '重要新闻'
                        important_news.append(news)
                
                return important_news
        
        except Exception as e:
            print(f"❌ AI 过滤失败: {e}")
            # 失败时返回所有新闻
            return news_items[:5]
        
        return []
    
    async def analyze_sentiment(self, news: Dict) -> str:
        """分析新闻情绪（利好/利空）"""
        prompt = f"""分析以下新闻的情绪。

标题: {news['title']}
摘要: {news['summary']}

返回 JSON:
{{
    "sentiment": "bullish" 或 "bearish" 或 "neutral",
    "confidence": 0-100,
    "reason": "一句话原因"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2
            )
            
            result_text = response.choices[0].message.content
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                sentiment = result.get('sentiment', 'neutral')
                
                # 转换成中文 emoji
                if sentiment == 'bullish':
                    return "🟢 利好"
                elif sentiment == 'bearish':
                    return "🔴 利空"
                else:
                    return "⚪ 中性"
        
        except:
            pass
        
        return "⚪ 中性"
    
    async def fetch_and_filter(self) -> List[Dict]:
        """抓取并过滤新闻（主入口）"""
        print("📰 抓取新闻...")
        
        # 1. 抓取新闻
        news_items = []
        news_items.extend(self.fetch_news_rss())
        news_items.extend(self.fetch_news_api())
        
        print(f"📊 抓取到 {len(news_items)} 条新闻")
        
        if not news_items:
            return []
        
        # 2. AI 过滤重要新闻
        important_news = await self.filter_important_news(news_items)
        
        print(f"✅ 筛选出 {len(important_news)} 条重要新闻")
        
        # 3. 分析情绪
        for news in important_news:
            news['sentiment'] = await self.analyze_sentiment(news)
        
        # 4. 标记为已读
        for news in important_news:
            self.seen_news.add(news['id'])
        self.save_seen_news()
        
        return important_news
    
    def format_news_for_telegram(self, news_list: List[Dict]) -> str:
        """格式化新闻用于 Telegram"""
        if not news_list:
            return "📭 暂无重要新闻"
        
        message = "📰 <b>重要新闻推送</b>\n\n"
        
        for i, news in enumerate(news_list[:5], 1):
            symbol = news.get('symbol', '市场')
            sentiment = news.get('sentiment', '⚪ 中性')
            reason = news.get('ai_reason', '')
            
            message += f"<b>{i}. {symbol}</b> {sentiment}\n"
            message += f"📄 {news['title']}\n"
            if reason:
                message += f"💡 {reason}\n"
            message += f"🔗 <a href='{news['link']}'>阅读全文</a>\n\n"
        
        message += f"⏰ {datetime.now().strftime('%H:%M')}"
        
        return message


# 使用示例
async def test_news_system():
    from openai import OpenAI
    import os
    
    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
    watchlist = ['NVDA', 'PLTR', 'RKLB', 'SOFI']
    
    news_system = NewsSystem(client, watchlist)
    
    # 抓取并过滤新闻
    important_news = await news_system.fetch_and_filter()
    
    # 格式化
    message = news_system.format_news_for_telegram(important_news)
    print(message)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_news_system())