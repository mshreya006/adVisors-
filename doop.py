import streamlit as st
from newsapi import NewsApiClient

# Initialize NewsApiClient with your API key
newsapi = NewsApiClient(api_key='4d4e4be81eb342b28974ac7ffd90821d')

# Dictionary to store industry keywords
industry_keywords = {
    'E-commerce': ['e-commerce', 'online shopping', 'digital retail', 'amazon', 'flipkart'],
    'Health and Wellness': ['health', 'hospital', 'drug', 'drugs', 'wellness', 'fitness', 'nutrition', 'skincare', 'longevity', 'aging', 'mood', 'supplement', 'beauty', 'skincare', 'cosmetics', 'personal care'],
    'Food and Beverage': ['food', 'beverage', 'restaurant', 'culinary', 'meat', 'meal', 'coffee', 'tea', 'drinks'],
    'Technology Services': ['tech', 'IT services', 'software', 'cybersecurity', 'amazon', 'products', 'product', 'tesla'],
    'Fashion and Apparel': ['fashion', 'apparel', 'clothing', 'style', 'fabric', 'designer', 'retail'],
    'Education and Tutoring': ['education', 'tutoring', 'learning'],
    'Home Improvement and Interior Design': ['home', 'interior design', 'renovation'],
    'Digital Marketing': ['digital marketing', 'SEO', 'social media', 'content marketing'],
    'Sustainable and Green Businesses': ['sustainability', 'green business', 'eco-friendly']
}

def fetch_business_news():
    # Fetch today's top business headlines, requesting up to 100 articles
    business_news = newsapi.get_top_headlines(category='business', language='en', page_size=100)
    return business_news['articles']

def filter_articles_by_industry(articles, keywords):
    filtered_articles = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        if any(keyword.lower() in (title.lower() if title else '') or 
               keyword.lower() in (description.lower() if description else '') 
               for keyword in keywords):
            filtered_articles.append(article)
    return filtered_articles

def display_articles(articles, title=""):
    if title:
        st.subheader(title)
    if articles:
        for article in articles:
            article_title = article.get('title') or "No title available"
            source = article['source']['name']
            description = article.get('description')
            url = article.get('url', '#')
            
            st.write(f"**{source}**: {article_title}")
            if description:  # Only display the description if it exists
                st.write(description)
            st.markdown(f"[Read more]({url})")
            st.write("---")
    else:
        st.write("Sorry, no articles found for the selected industry.")

def main():
    st.title("Business News Fetcher by Industry")

    # Fetch and display all business news
    business_articles = fetch_business_news()
    display_articles(business_articles, title="All Business News")

    # Dropdown for industry selection
    selected_industry = st.selectbox(
        "Filter news by industry:",
        list(industry_keywords.keys())
    )

    # Filter articles based on the selected industry
    keywords = industry_keywords[selected_industry]
    filtered_articles = filter_articles_by_industry(business_articles, keywords)

    # Display the filtered articles
    if st.button("Show Filtered News"):
        display_articles(filtered_articles, title=f"News related to {selected_industry}")

if __name__ == "__main__":
    main()
