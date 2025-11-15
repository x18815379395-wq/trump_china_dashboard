import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
from textblob import TextBlob
import plotly.express as px
import time
import os
from typing import List, Dict, Tuple, Optional

# 配置页面设置（应放在所有Streamlit命令之前）
st.set_page_config(
    page_title="特朗普情绪监测仪表盘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# 常量定义
# ======================
REFRESH_INTERVAL = 5 * 60  # 5分钟刷新间隔（秒）
SENTIMENT_THRESHOLD = 0.1  # 情绪判断阈值
POSTS_CACHE_KEY = "truth_posts"  # 缓存键名
REFRESH_TIME_KEY = "last_refresh_time"  # 上次刷新时间键名
DATA_FILE = "trump_china_sentiment_data.csv"  # 数据保存文件


# ======================
# 数据获取函数
# ======================
def fetch_truth_posts() -> List[Dict]:
    """获取特朗普Truth平台的帖子（模拟实现）"""
    mock_posts = [
        {"id": 1, "text": "China is manipulating trade again! Not fair!", "timestamp": datetime.now()},
        {"id": 2, "text": "Great meeting with American farmers today! China needs to step up!", "timestamp": datetime.now()},
        {"id": 3, "text": "China’s economy is collapsing, terrible leadership!", "timestamp": datetime.now()},
        {"id": 4, "text": "We will bring manufacturing back from China!", "timestamp": datetime.now()},
        {"id": 5, "text": "Stock market doing great! America first, China second!", "timestamp": datetime.now()},
        {"id": 6, "text": "China has shown some cooperation, that’s a good sign.", "timestamp": datetime.now()},
        {"id": 7, "text": "Our trade deal with China is working well for both countries.", "timestamp": datetime.now()},
        {"id": 8, "text": "China must respect our intellectual property rights immediately!", "timestamp": datetime.now()},
    ]
    random.shuffle(mock_posts)
    return mock_posts[:random.randint(3, 6)]


# ======================
# 情绪分析工具
# ======================
def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    分析文本情绪
    
    Args:
        text: 待分析的文本
        
    Returns:
        情绪类别（正面/负面/中性）和情绪得分
    """
    if not text or not isinstance(text, str):
        return "中性", 0.0
        
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity > SENTIMENT_THRESHOLD:
        return "正面", polarity
    elif polarity < -SENTIMENT_THRESHOLD:
        return "负面", polarity
    else:
        return "中性", polarity


# ======================
# 投资建议生成器
# ======================
def generate_trading_signal(sentiment: str) -> str:
    """根据情绪生成投资建议"""
    signal_map = {
        "正面": "📈 做多中国相关资产",
        "负面": "📉 做空中国相关资产",
        "中性": "⚖️ 观望"
    }
    return signal_map.get(sentiment, "⚖️ 观望")


# ======================
# 数据处理函数
# ======================
def process_posts(posts: List[Dict]) -> pd.DataFrame:
    """处理原始帖子数据，生成带情绪分析和投资建议的DataFrame"""
    processed_data = []
    
    for post in posts:
        # 确保必要字段存在
        if not all(key in post for key in ["text", "timestamp", "id"]):
            continue
            
        # 过滤包含China的帖子
        if "china" not in post["text"].lower():
            continue
            
        # 分析情绪并生成建议
        sentiment, score = analyze_sentiment(post["text"])
        signal = generate_trading_signal(sentiment)
        
        processed_data.append({
            "帖子ID": post["id"],
            "时间": post["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "原始时间": post["timestamp"],  # 保存原始时间用于排序
            "内容": post["text"],
            "情绪": sentiment,
            "情绪得分": round(score, 3),
            "投资建议": signal,
            "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return pd.DataFrame(processed_data)


# ======================
# 数据保存函数（修复时间类型问题）
# ======================
def save_data_to_csv(df: pd.DataFrame) -> None:
    """将处理后的数据保存到CSV文件，避免重复数据"""
    if df.empty:
        return
        
    # 检查文件是否存在
    if os.path.exists(DATA_FILE):
        # 读取已有数据
        existing_df = pd.read_csv(DATA_FILE)
        # 关键修复：将现有数据的"原始时间"转换为datetime类型
        existing_df["原始时间"] = pd.to_datetime(existing_df["原始时间"])
        # 合并数据并去重（基于帖子ID）
        combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=["帖子ID"], keep="last")
    else:
        combined_df = df
    
    # 按时间排序并保存
    combined_df = combined_df.sort_values(by="原始时间", ascending=False)
    combined_df.to_csv(DATA_FILE, index=False)


# ======================
# 可视化组件
# ======================
def plot_sentiment_distribution(df: pd.DataFrame) -> None:
    """绘制情绪分布柱状图"""
    sentiment_counts = df["情绪"].value_counts().reset_index()
    sentiment_counts.columns = ["情绪类型", "数量"]
    
    fig = px.bar(
        sentiment_counts,
        x="情绪类型",
        y="数量",
        color="情绪类型",
        text="数量",
        title="特朗普对中国言论的情绪分布",
        color_discrete_map={
            "正面": "green",
            "负面": "red",
            "中性": "gray"
        }
    )
    st.plotly_chart(fig, use_container_width=True)


# ======================
# 缓存管理
# ======================
def refresh_posts() -> List[Dict]:
    """刷新帖子数据并更新缓存"""
    new_posts = fetch_truth_posts()
    st.session_state[POSTS_CACHE_KEY] = new_posts
    st.session_state[REFRESH_TIME_KEY] = time.time()
    return new_posts


def get_cached_posts(force_refresh: bool = False) -> List[Dict]:
    """获取缓存的帖子数据，可强制刷新"""
    if force_refresh:
        return refresh_posts()
        
    current_time = time.time()
    last_refresh = st.session_state.get(REFRESH_TIME_KEY, 0)
    
    # 检查是否需要刷新数据
    if current_time - last_refresh > REFRESH_INTERVAL:
        return refresh_posts()
    
    return st.session_state.get(POSTS_CACHE_KEY, fetch_truth_posts())


# ======================
# 主页面渲染
# ======================
def main():
    # 页面标题
    st.title("🇺🇸 特朗普 Truth 平台 · 中国相关言论监测")
    st.caption("自动抓取、情绪分析、投资建议与数据追踪")
    st.divider()
    
    # 刷新控制
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 手动刷新数据", use_container_width=True):
            with st.spinner("正在刷新最新数据..."):
                get_cached_posts(force_refresh=True)
                st.success("数据已更新!")
                # 刷新页面以显示最新数据
                st.experimental_rerun()
    
    with col2:
        last_refresh_time = datetime.fromtimestamp(
            st.session_state.get(REFRESH_TIME_KEY, time.time())
        ).strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"⏱ 最新更新时间: {last_refresh_time}", icon="ℹ️")
    
    # 获取并处理数据
    posts = get_cached_posts()
    df = process_posts(posts)
    
    # 保存数据到CSV
    if not df.empty:
        save_data_to_csv(df)
        # 显示数据文件信息
        file_size = os.path.getsize(DATA_FILE) if os.path.exists(DATA_FILE) else 0
        st.caption(f"💾 数据已自动保存到 {DATA_FILE}（文件大小: {file_size/1024:.1f} KB）")
    
    # 显示结果
    if df.empty:
        st.info("暂无涉及 China 的帖子，请稍后再试。")
    else:
        # 显示数据表格
        st.subheader("最新言论分析")
        # 显示时排除原始时间列
        display_df = df.drop(columns=["原始时间"])
        st.dataframe(display_df, use_container_width=True)
        
        # 显示情绪分布图表
        st.subheader("📉 情绪分布")
        plot_sentiment_distribution(df)
        
        # 投资建议总结
        st.subheader("💡 投资建议总结")
        sentiment_score = df["情绪得分"].mean()
        
        if sentiment_score > SENTIMENT_THRESHOLD:
            st.success(f"整体情绪偏正面（平均得分: {sentiment_score:.3f}）：可考虑适度做多中国市场。")
        elif sentiment_score < -SENTIMENT_THRESHOLD:
            st.error(f"整体情绪偏负面（平均得分: {sentiment_score:.3f}）：可考虑适度做空中国市场。")
        else:
            st.warning(f"整体情绪中性（平均得分: {sentiment_score:.3f}）：建议观望，等待更多信号。")
    
    # 显示刷新信息
    st.caption(f"数据将每隔 {REFRESH_INTERVAL//60} 分钟自动刷新")


if __name__ == "__main__":
    main()
    
