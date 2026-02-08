"""
新闻抓取和过滤系统
自动抓取、分析、过滤重要新闻
"""

import re
import feedparser
import requests
from datetime import datetime
from typing import List, Dict
import json
from pathlib import Path


class NewsSystem:
    """新闻系统 - 抓取、过滤、分析"""

    def __init__(self, client, watchlist):
        self.client = client
        self.watchlist = watchlist
        self.news_cache_file = Path("news_cache.json")
        self.seen_news = self.load_seen_news()

    def load_seen_news(self):
        if self.news_cache_file.exists():
            return set(json.loads(self.news_cache_file.read_text()))
        return set()

    def save_seen_news(self):
        self.news_cache_file.write_text(json.dumps(list(self.seen_news)))

    def fetch_news_rss(self) -> List[Dict]:
        news_items = []
        rss_feeds = [
            *[f"https://finance.yahoo.com/rss/headline?s={s}" for s in self.watchlist],
            "https://seekingalpha.com/feed.xml",
            "https://www.marketwatch.com/rss/topstories",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        ]
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    news_id = entry.get("id", entry.get("link", ""))
                    if news_id in self.seen_news:
                        continue
                    news_items.append({
                        "id": news_id,
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.get("summary", "")[:300],
                        "published": entry.get("published", ""),
                        "source": feed_url,
                    })
            except Exception as e:
                print(f"⚠️ RSS 抓取失败 {feed_url}: {e}")
        return news_items

    def fetch_news_api(self) -> List[Dict]:
        api_key = "YOUR_NEWS_API_KEY"
        if not api_key or api_key == "YOUR_NEWS_API_KEY":
            return []
        news_items = []
        for symbol in self.watchlist:
            try:
                url = f"https://newsapi.org/v2/everything?q={symbol}&language=en&sortBy=publishedAt&apiKey={api_key}"
                response = requests.get(url, timeout=10)
                data = response.json()
                for article in data.get("articles", [])[:5]:
                    news_id = article.get("url", "")
                    if news_id in self.seen_news:
                        continue
                    news_items.append({
                        "id": news_id,
                        "title": article["title"],
                        "link": article["url"],
                        "summary": article.get("description", "")[:300],
                        "published": article.get("publishedAt", ""),
                        "source": "NewsAPI",
                        "symbol": symbol,
                    })
            except Exception as e:
                print(f"⚠️ News API 失败 {symbol}: {e}")
        return news_items

    async def filter_important_news(self, news_items: List[Dict]) -> List[Dict]:
        if not news_items:
            return []
        news_text = "\n".join(f"{i+1}. {n['title']}" for i, n in enumerate(news_items[:20]))
        prompt = f"""你是专业的金融新闻分析师。请从以下新闻中筛选出**真正重要**的新闻。

我的关注股票: {", ".join(self.watchlist)}

新闻列表:
{news_text}

筛选标准:
- ⭐⭐⭐ 高影响: 财报、产品发布、收购、FDA批准、重大合同
- ⭐⭐ 中影响: 分析师评级变化、行业趋势、政策变化
- ⭐ 低影响: 常规新闻、无关信息

只返回 JSON 格式:
{{ "important_news": [1, 5, 8], "reasons": ["原因1", "原因2"] }}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2,
            )
            result_text = response.choices[0].message.content
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                important_indices = result.get("important_news", [])
                reasons = result.get("reasons", [])
                important_news = []
                for idx in important_indices:
                    if 1 <= idx <= len(news_items):
                        news = news_items[idx - 1].copy()
                        news["ai_reason"] = reasons[len(important_news)] if len(important_news) < len(reasons) else "重要新闻"
                        important_news.append(news)
                return important_news
        except Exception as e:
            print(f"❌ AI 过滤失败: {e}")
            return news_items[:5]
        return []

    async def analyze_sentiment(self, news: Dict) -> str:
        prompt = f"""分析以下新闻的情绪。标题: {news['title']}\n摘要: {news['summary']}
返回 JSON: {{ "sentiment": "bullish 或 bearish 或 neutral", "reason": "一句话" }}"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2,
            )
            result_text = response.choices[0].message.content
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                s = result.get("sentiment", "neutral")
                return "🟢 利好" if s == "bullish" else ("🔴 利空" if s == "bearish" else "⚪ 中性")
        except Exception:
            pass
        return "⚪ 中性"

    async def fetch_and_filter(self) -> List[Dict]:
        print("📰 抓取新闻...")
        news_items = []
        news_items.extend(self.fetch_news_rss())
        news_items.extend(self.fetch_news_api())
        print(f"📊 抓取到 {len(news_items)} 条新闻")
        if not news_items:
            return []
        important_news = await self.filter_important_news(news_items)
        print(f"✅ 筛选出 {len(important_news)} 条重要新闻")
        for news in important_news:
            news["sentiment"] = await self.analyze_sentiment(news)
        for news in important_news:
            self.seen_news.add(news["id"])
        self.save_seen_news()
        return important_news

    def format_news_for_telegram(self, news_list: List[Dict]) -> str:
        if not news_list:
            return "📭 暂无重要新闻"
        message = "📰 <b>重要新闻推送</b>\n\n"
        for i, news in enumerate(news_list[:5], 1):
            symbol = news.get("symbol", "市场")
            sentiment = news.get("sentiment", "⚪ 中性")
            reason = news.get("ai_reason", "")
            message += f"<b>{i}. {symbol}</b> {sentiment}\n📄 {news['title']}\n"
            if reason:
                message += f"💡 {reason}\n"
            message += f"🔗 <a href='{news['link']}'>阅读全文</a>\n\n"
        message += f"⏰ {datetime.now().strftime('%H:%M')}"
        return message

    async def get_daily_summary_paragraph(self, news_list: List[Dict]) -> str:
        """One GPT call: condense news list into a short morning digest (2-4 sentences)."""
        if not news_list:
            return "今日暂无重要新闻。"
        titles = "\n".join(f"- {n.get('title', '')}" for n in news_list[:8])
        prompt = f"""Based on these headlines, write a very short morning market digest in 2-4 sentences (Chinese or English). Focus on what matters for trading today.

Headlines:
{titles}

Reply with the digest only, no bullet list."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip() or "今日暂无重要新闻。"
        except Exception as e:
            print(f"❌ Daily summary GPT failed: {e}")
            return "今日暂无重要新闻。"
