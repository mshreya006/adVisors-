import streamlit as st

# Page configuration MUST be the very first Streamlit command called
st.set_page_config(
    page_title="News Intelligence Platform",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

import logging
from database.database import init_db, set_bookmark_status, get_bookmarked_articles, get_search_history
from services.article_service import ArticleService
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize database schema
init_db()

# Initialize core services
@st.cache_resource
def get_article_service():
    return ArticleService()

article_service = get_article_service()

# Custom CSS for premium design (Adaptive Light/Dark mode)
st.markdown("""
<style>
    /* Styling for news cards */
    .news-card {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        border-radius: 12px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 25px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        border-color: var(--primary-color);
    }
    .news-card h3 {
        margin-top: 0px !important;
        margin-bottom: 8px !important;
        font-weight: 700;
        font-size: 1.25rem;
    }
    .news-card p {
        margin-bottom: 12px !important;
        line-height: 1.5;
    }
    
    /* Badge styling */
    .badge-container {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
        flex-wrap: wrap;
    }
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        display: inline-flex;
        align-items: center;
        color: white !important;
    }
    .badge-ind {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    }
    .badge-real {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    }
    .badge-fake {
        background: linear-gradient(135deg, #dc2626 0%, #f87171 100%);
    }
    
    /* Sidebar styling enhancements */
    .sidebar-section {
        background-color: rgba(128, 128, 128, 0.05);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 3px solid var(--primary-color);
    }
    .status-indicator {
        font-size: 0.85rem;
        margin-bottom: 5px;
    }
    .headline-item {
        font-size: 0.9rem;
        padding: 8px 0px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.15);
    }
    .headline-item:last-child {
        border-bottom: none;
    }
    .headline-title {
        margin-bottom: 2px;
    }
    a {
        color: #6366f1 !important;
        text-decoration: none;
        font-weight: 600;
    }
    a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Streamlit session states for tracking interactive filters
if "active_industry" not in st.session_state:
    st.session_state.active_industry = None

def main():
    st.title("Latest Trend Updates")
    st.subheader("AI-Powered News Intelligence Platform")

    # ==========================
    # SIDEBAR: GENERAL HEADLINES & BOOKMARKS & STATUS
    # ==========================
    
    # 1. General Top Headlines (uses DB cache + fallback API)
    st.sidebar.subheader("Today's Headlines")
    
    with st.sidebar:
        with st.spinner("Loading headlines..."):
            headlines, hl_source = article_service.fetch_and_process_headlines()
        
    if headlines:
        for idx, article in enumerate(headlines[:5]):
            st.sidebar.markdown(f"""
            <div class="headline-item">
                <div class="headline-title">{article.source_name}: {article.title}</div>
                <div style="font-size: 0.8rem; margin-bottom: 4px;">
                    <span style="color: {'#10b981' if article.fake_news_prediction == 'Real' else '#f87171'}">
                        {article.fake_news_prediction} ({(article.fake_news_confidence * 100):.0f}%)
                    </span>
                </div>
                <a href="{article.url}" target="_blank" style="font-size: 0.8rem;">Read more</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.sidebar.write("No headlines available.")

    # 3. Bookmarks Manager
    st.sidebar.markdown("---")
    st.sidebar.subheader("Bookmarked Articles")
    
    bookmarks = get_bookmarked_articles()
    if bookmarks:
        for idx, bookmarked_art in enumerate(bookmarks):
            col_b1, col_b2 = st.sidebar.columns([4, 1])
            with col_b1:
                st.sidebar.markdown(f"**[{bookmarked_art.source_name}]** {bookmarked_art.title}")
                st.sidebar.markdown(f"[Read article]({bookmarked_art.url})")
            with col_b2:
                # Remove bookmark button
                if st.sidebar.button("❌", key=f"del_bookmark_{bookmarked_art.url}_{idx}"):
                    set_bookmark_status(bookmarked_art.url, False)
                    st.rerun()
            st.sidebar.markdown("---")
    else:
        st.sidebar.write("No bookmarked articles yet.")

    # 4. Search History
    st.sidebar.markdown("---")
    st.sidebar.subheader("Recent Searches")
    history = get_search_history(5)
    if history:
        for item in history:
            # Render as clickable options
            if st.sidebar.button(f"🔍 {item['industry']}", key=f"hist_{item['timestamp']}"):
                st.session_state.active_industry = item['industry']
                st.rerun()
    else:
        st.sidebar.write("No search history.")


    # ==========================
    # MAIN PAGE: INDUSTRY CLASSIFIER FEED
    # ==========================
    
    # Selected industry dropdown
    st.markdown("### Choose your Industry Feed")
    options = ["Select an industry"] + list(config.INDUSTRY_KEYWORDS.keys())
    
    # If session state active industry is loaded, locate its index
    default_index = 0
    if st.session_state.active_industry in options:
        default_index = options.index(st.session_state.active_industry)
        
    selected_industry = st.selectbox(
        "Filter news by industry:",
        options=options,
        index=default_index
    )

    # State handler
    if selected_industry != "Select an industry":
        # Check if user clicked the button or if we have an active session state matching
        btn_clicked = st.button("Show Filtered News")
        
        if btn_clicked or st.session_state.active_industry == selected_industry:
            st.session_state.active_industry = selected_industry
            
            with st.spinner(f"Aggregating & analyzing news for {selected_industry}..."):
                try:
                    articles, is_cached, source = article_service.fetch_and_process_industry_news(selected_industry)
                    
                    if articles:
                        # Render articles list
                        for idx, article in enumerate(articles):
                            # Wrapper container for visual isolation
                            st.markdown(f"""
                            <div class="news-card">
                                <h3>{article.title}</h3>
                                <div class="badge-container">
                                    <span class="badge badge-ind">Industry: {article.predicted_industry} ({(article.industry_confidence * 100):.1f}%)</span>
                                    <span class="badge {'badge-real' if article.fake_news_prediction == 'Real' else 'badge-fake'}">
                                        Fact Quality: {article.fake_news_prediction} ({(article.fake_news_confidence * 100):.1f}%)
                                    </span>
                                </div>
                                <p style="font-size: 0.85rem; opacity: 0.8; margin-top: -5px;">
                                    Source: <b>{article.source_name}</b> | Published: {article.published_at.replace('T', ' ').split('.')[0]}
                                </p>
                                <p>{article.description}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Actions row (Streamlit columns)
                            act_col1, act_col2, _ = st.columns([1, 1, 4])
                            with act_col1:
                                # Bookmark toggle button
                                is_bookmarked = article.is_bookmarked == 1
                                label = "⭐ Bookmarked" if is_bookmarked else "🔖 Bookmark"
                                if st.button(label, key=f"bookmark_btn_{article.url}_{idx}"):
                                    set_bookmark_status(article.url, not is_bookmarked)
                                    st.rerun()
                            with act_col2:
                                st.markdown(f'<a href="{article.url}" target="_blank"><button style="padding: 4px 12px; border-radius: 4px; border: 1px solid var(--primary-color); background: transparent; cursor: pointer; color: var(--primary-color) !important;">Read More 🔗</button></a>', unsafe_allow_html=True)
                                
                            st.markdown("<br>", unsafe_allow_html=True)
                    else:
                        st.info("No articles matched this industry category with sufficient confidence.")
                except Exception as e:
                    # Capture stack traces and report a clean error in the UI
                    logger.exception("Error loading news feed")
                    st.error(f"Error fetching news: {str(e)}")
                    st.warning("Please check your network connection or API keys in the configurations.")
    else:
        st.info("Please select an industry from the dropdown above to load the news feed.")

if __name__ == "__main__":
    main()
