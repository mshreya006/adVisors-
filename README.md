# adVisors-
# Latest Trend Updates

## Overview

Latest Trend Updates is a Streamlit-based web application that retrieves real-time news using the NewsAPI and categorizes articles based on different industries. The application enables users to stay informed about the latest trends in their chosen domain while filtering out negative news to provide a more business-focused and informative experience.

In addition to industry-specific news, the application also displays today's top headlines in a sidebar for quick access to current events.

---

## Features

- Retrieves real-time news articles using NewsAPI
- Filters news by industry
- Displays top headlines in the sidebar
- Removes articles containing negative or sensitive news
- Displays article title, source, description, and link
- Interactive and user-friendly Streamlit interface
- Automatic retry mechanism for failed API requests
- Easy to extend with new industries and keywords

---

## Technologies Used

- Python 3
- Streamlit
- NewsAPI
- Requests
- urllib3

---

## Project Structure

```
Latest-Trend-Updates/
│
├── app.py               # Main Streamlit application
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/latest-trend-updates.git

cd latest-trend-updates
```

---

### Step 2: Create a Virtual Environment (Optional but Recommended)

#### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

#### Linux/macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

### Step 3: Install Dependencies

Using requirements.txt

```bash
pip install -r requirements.txt
```

Or install manually

```bash
pip install streamlit newsapi-python requests urllib3
```

---

### Step 4: Obtain a NewsAPI Key

1. Visit https://newsapi.org
2. Create a free account.
3. Generate your API key.
4. Replace the API key in `app.py`.

Example:

```python
newsapi = NewsApiClient(api_key="YOUR_API_KEY")
```

Also replace

```python
'apiKey': 'YOUR_API_KEY'
```

inside the request parameters.

---

## Running the Application

Run the following command:

```bash
streamlit run app.py
```

The application will open automatically in your default web browser.

---

## Application Workflow

1. The application launches the Streamlit interface.

2. The latest top headlines are fetched using the NewsAPI Top Headlines endpoint and displayed in the sidebar.

3. The user selects an industry from the dropdown menu.

4. The application searches NewsAPI using predefined keywords associated with the selected industry.

5. Retrieved articles are filtered by:
   - Matching industry keywords.
   - Removing articles containing negative keywords.

6. The filtered articles are displayed with:
   - Source
   - Title
   - Description
   - Read More link

---

## Supported Industries

The application currently supports the following industries:

- E-commerce
- Health and Wellness
- Food and Beverage
- Technology Services
- Fashion and Apparel
- Education and Tutoring
- Home Improvement and Interior Design
- Digital Marketing
- Sustainable and Green Businesses

---

## Industry Keywords

Each industry contains a predefined list of keywords used to search NewsAPI.

Example:

### Technology Services

- tech
- techs
- software
- IT services
- cybersecurity
- amazon
- tesla
- product
- products

### Health and Wellness

- health
- wellness
- fitness
- nutrition
- skincare
- beauty
- longevity
- supplements
- aging
- mood

### Food and Beverage

- food
- restaurant
- coffee
- tea
- drinks
- meal
- chocolate
- latte

Additional industries and keywords can be added by updating the `industry_keywords` dictionary.

---

## Negative News Filtering

To improve the relevance of displayed articles, news containing the following keywords is filtered out:

- tragedy
- disaster
- attack
- crime
- shooting
- death
- injury
- accident
- scandal

Filtering is performed on both the article title and article description.

---

## Function Description

### fetch_news_by_keywords(keywords)

Retrieves up to 100 articles matching the selected industry's keywords.

Responsibilities:

- Creates an HTTP session
- Implements retry logic
- Sends requests to NewsAPI
- Collects matching articles
- Stops after collecting 100 articles

---

### fetch_general_news()

Retrieves the latest top headlines from NewsAPI and displays them in the sidebar.

---

### filter_articles_by_industry(articles, keywords)

Filters articles by:

- Matching industry keywords
- Removing articles containing negative keywords

Returns only relevant articles.

---

### display_articles()

Displays:

- Source
- Title
- Description
- Read More link

---

### display_general_news()

Displays the latest general news articles in the Streamlit sidebar.

---

### main()

Controls the complete application workflow by:

- Displaying sidebar headlines
- Creating the industry dropdown
- Fetching articles
- Filtering articles
- Displaying the final results

---

## Retry Mechanism

The application uses the Retry class from urllib3 to improve reliability.

Benefits include:

- Handles temporary network failures
- Automatically retries failed requests
- Improves application stability
- Reduces interruptions caused by connection issues

---

## User Interface

### Main Page

- Application title
- Industry selection dropdown
- Show Filtered News button
- Filtered news articles

### Sidebar

- Today's headlines
- Article descriptions
- Read More links

---

## Dependencies

```
streamlit
newsapi-python
requests
urllib3
```

Install using:

```bash
pip install streamlit newsapi-python requests urllib3
```

---

## Requirements

- Python 3.8 or higher
- Internet connection
- Valid NewsAPI API key

---

## Advantages

- Lightweight application
- Easy to use
- Real-time news updates
- Industry-specific filtering
- Removes negative news articles
- Interactive interface
- Modular code structure
- Easy to extend with additional industries

---

## Limitations

- Depends on NewsAPI availability.
- Free NewsAPI plans have API request limitations.
- Keyword-based filtering may occasionally exclude relevant articles.
- Negative news filtering relies on predefined keywords.
- Only supported industries can be searched.

---

## Future Enhancements

Potential improvements include:

- AI-based news summarization
- Sentiment analysis
- Personalized news recommendations
- User authentication
- Bookmark favorite articles
- Search using custom keywords
- Multi-language news support
- Pagination
- Dark mode
- Daily email notifications
- Machine learning-based article classification

---

## Author

Developed as a Streamlit-based news aggregation application that provides users with industry-specific trend updates using the NewsAPI. The project focuses on delivering relevant, organized, and easily accessible news through a clean and interactive user interface.
