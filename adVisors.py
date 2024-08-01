import streamlit as st
from newsapi import NewsApiClient
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Initialize NewsApiClient with your API key
newsapi = NewsApiClient(api_key='4d4e4be81eb342b28974ac7ffd90821d')

# Dictionary to store industry keywords
industry_keywords = {
    'E-commerce': ['e-commerce', 'online shopping', 'retail', 'amazon', 'flipkart', 'offer'],
    'Health and Wellness': ['health', 'wellness', 'fitness', 'nutrition', 'skincare', 'longevity', 'aging', 'mood', 'supplement', 'beauty', 'cosmetics', 'personal care', 'makeup'],
    'Food and Beverage': ['food', 'beverage', 'restaurant', 'culinary', 'meat', 'meal', 'coffee', 'tea', 'drinks', 'chocolate', 'latte'],
    'Technology Services': ['tech', 'techs', 'IT services', 'software', 'cybersecurity', 'amazon', 'products', 'product', 'tesla'],
    'Fashion and Apparel': ['fashion', 'apparel', 'clothing', 'style', 'fabric', 'designer'],
    'Education and Tutoring': ['education', 'tutoring', 'learning'],
    'Home Improvement and Interior Design': ['home', 'interior design', 'renovation'],
    'Digital Marketing': ['digital marketing', 'SEO', 'social media', 'content marketing'],
    'Sustainable and Green Businesses': ['sustainability', 'green business', 'eco-friendly']
}

# List of keywords to exclude negative news
negative_keywords = ['tragedy', 'disaster', 'attack', 'crime', 'shooting', 'death', 'injury', 'accident', 'scandal']

def fetch_news_by_keywords(keywords):
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    pm_all_articles = []
    for keyword in keywords:
        try:
            response = session.get('https://newsapi.org/v2/everything', params={
                'q': keyword,
                'language': 'en',
                'pageSize': 100,
                'apiKey': '4d4e4be81eb342b28974ac7ffd90821d'
            })
            response.raise_for_status()  # Raise HTTPError for bad responses
            articles = response.json().get('articles', [])
            pm_all_articles.extend(articles)
            if len(pm_all_articles) >= 100:
                break  # Stop once we have 100 articles
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching news for keyword '{keyword}': {e}")
    return pm_all_articles[:100]  # Return only the first 100 articles

def fetch_general_news():
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        response = session.get('https://newsapi.org/v2/top-headlines', params={
            'country': 'us',
            'pageSize': 5,
            'apiKey': '4d4e4be81eb342b28974ac7ffd90821d'
        })
        response.raise_for_status()
        articles = response.json().get('articles', [])
        return articles
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching general news: {e}")
        return []

def filter_articles_by_industry(articles, keywords):
    filtered_articles = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        # Check if article matches industry keywords and does not contain negative keywords
        if (any(keyword.lower() in (title.lower() if title else '') or 
                keyword.lower() in (description.lower() if description else '') 
                for keyword in keywords) and
                not any(neg_keyword.lower() in (title.lower() if title else '') or 
                        neg_keyword.lower() in (description.lower() if description else '') 
                        for neg_keyword in negative_keywords)):
            filtered_articles.append(article)
    return filtered_articles

def display_articles(articles, title=""):
    if title:
        st.subheader(title)
    if articles:
        for article in articles:
            article_title = article.get('title', 'No Title')
            source = article.get('source', {}).get('name', 'Unknown Source')
            description = article.get('description', 'No description available')
            url = article.get('url', '#')
            
            st.write(f"{source}: {article_title}")
            st.write(description)  # Display the article's description
            st.markdown(f"[Read more]({url})")
            st.write("---")
    else:
        st.write("Sorry, no articles found for the selected industry.")

def display_general_news():
    articles = fetch_general_news()
    if articles:
        st.sidebar.subheader("Today's Headlines")
        for article in articles:
            article_title = article.get('title', 'No Title')
            source = article.get('source', {}).get('name', 'Unknown Source')
            description = article.get('description', '')
            url = article.get('url', '#')
            
            st.sidebar.write(f"{source}: {article_title}")
            if description:
                st.sidebar.write(description)  # Display the article's description only if available
            st.sidebar.markdown(f"[Read more]({url})")
            st.sidebar.write("---")
    else:
        st.sidebar.write("No general news available.")


def main():
    st.title("Latest Trend Updates")

    # Display general news in the sidebar
    display_general_news()

    # Dropdown for industry selection with a placeholder
    selected_industry = st.selectbox(
        "Filter news by industry:",
        options=["Select an industry"] + list(industry_keywords.keys()),
        format_func=lambda x: x if x != "Select an industry" else "Select an industry"
    )

    # Check if a valid industry is selected
    if selected_industry != "Select an industry":
        # Fetch and filter articles based on the selected industry
        keywords = industry_keywords[selected_industry]
        articles = fetch_news_by_keywords(keywords)
        filtered_articles = filter_articles_by_industry(articles, keywords)

        # Display the filtered articles
        if st.button("Show Filtered News"):
            display_articles(filtered_articles, title=f"Current Trends on {selected_industry}")

if __name__ == "__main__":
    main()