Python 3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> # filename: trump_china_dashboard.py
... import time
... import requests
... import pandas as pd
... import streamlit as st
... from datetime import datetime
... from bs4 import BeautifulSoup
... from transformers import pipeline
... import plotly.express as px
... 
... # ---------------------------
... # 初始化 NLP 模型
... # ---------------------------
... @st.cache_resource
... def load_models():
...     summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
...     sentiment = pipeline("sentiment-analysis")
...     return summarizer, sentiment
... 
... summarizer, sentiment = load_models()
... 
... # ---------------------------
... # 实际抓取函数：从 Google News 抓取特朗普 + China 相关新闻
... # ---------------------------
... def fetch_truth_posts(keyword="Trump China", limit=5):
...     """
...     从 Google News 抓取包含特朗普 + China 的相关新闻标题和摘要
...     返回 DataFrame 格式
...     """
...     url = f"https://news.google.com/rss/search?q={keyword}&hl=en-US&gl=US&ceid=US:en"
...     response = requests.get(url, timeout=10)
...     soup = BeautifulSoup(response.text, "xml")
...     items = soup.find_all("item")
... 
...     data = []
...     for item in items[:limit]:
        title = item.title.text
        desc = item.description.text
        pub_date = item.pubDate.text
        link = item.link.text
        data.append({
            "time": pub_date,
            "content": f"{title}. {desc}",
            "source": link
        })

    df = pd.DataFrame(data)
    return df

# ---------------------------
# 数据处理函数
# ---------------------------
def analyze_posts(df):
    summaries = []
    sentiments = []
    for text in df["content"]:
        summary = summarizer(text, max_length=50, min_length=10, do_sample=False)[0]["summary_text"]
        sentiment_result = sentiment(text)[0]
        summaries.append(summary)
        sentiments.append(sentiment_result["label"])
    df["summary"] = summaries
    df["sentiment"] = sentiments
    return df

# ---------------------------
# Streamlit 页面配置
# ---------------------------
st.set_page_config(page_title="Trump & China Monitor", layout="wide")
st.title("🇺🇸 特朗普相关 'China' 新闻监测仪表盘")
st.caption("自动抓取 Google News 新闻摘要与情绪分析（每 5 分钟刷新一次）")

REFRESH_INTERVAL = 300  # 秒（5分钟）
placeholder = st.empty()

while True:
    with placeholder.container():
        st.info(f"正在抓取最新数据……（时间：{datetime.now().strftime('%H:%M:%S')}）")
        posts = fetch_truth_posts()
        analyzed = analyze_posts(posts)

        # 展示表格
        st.subheader("📰 最新相关新闻摘要")
        st.dataframe(analyzed[["time", "content", "summary", "sentiment", "source"]])

        # 📉 情绪分布柱状图
        st.subheader("📉 情绪分布图（正面 / 负面 / 中性）")
        sentiment_counts = analyzed["sentiment"].value_counts().reset_index()
        sentiment_counts.columns = ["Sentiment", "Count"]
        chart = px.bar(sentiment_counts, x="Sentiment", y="Count", color="Sentiment",
                       title="新闻报道的整体情绪分布", text="Count")
        chart.update_traces(textposition="outside")
        st.plotly_chart(chart, use_container_width=True)

        st.write(f"⏳ 下次刷新时间：{datetime.now().strftime('%H:%M:%S')} + {REFRESH_INTERVAL//60} 分钟")
        time.sleep(REFRESH_INTERVAL)
