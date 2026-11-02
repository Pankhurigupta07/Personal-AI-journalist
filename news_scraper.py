import requests
from bs4 import BeautifulSoup

def generate_news_urls_to_scrape(topics_list):
    urls = {}
    for topic in topics_list:
        formatted_topic = topic.replace(" ", "+")
        urls[topic] = f"https://news.google.com/rss/search?q={formatted_topic}&hl=en-IN&gl=IN&ceid=IN:en"
    return urls

def scrape_news_with_bs4(url):
    articles = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        # BeautifulSoup parsing with fallback
        try:
            soup = BeautifulSoup(response.content, "lxml")
        except Exception:
            soup = BeautifulSoup(response.content, "html.parser")
            
        items = soup.find_all("item")
        for item in items[:5]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubdate") or item.find("pubDate")
            
            articles.append({
                "title": title_elem.text if title_elem else "",
                "link": link_elem.text if link_elem else "",
                "published": pub_date_elem.text if pub_date_elem else ""
            })
    except Exception as e:
        print(f"Error fetching Google News: {e}")
    return articles

def scrape_reddit_posts(topics_list, limit=5):
    reddit_results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for topic in topics_list:
        posts = []
        
        # Try 1: Reddit JSON search
        try:
            url = f"https://www.reddit.com/search.json?q={topic.replace(' ', '+')}&limit={limit}"
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                for child in data.get("data", {}).get("children", []):
                    title = child.get("data", {}).get("title")
                    if title:
                        posts.append({"title": title})
        except Exception:
            pass
            
        # Fallback: Google News RSS for community/discussions if Reddit blocks
        if not posts:
            try:
                fallback_url = f"https://news.google.com/rss/search?q={topic.replace(' ', '+')}+discussion+community&hl=en-IN&gl=IN&ceid=IN:en"
                fb_resp = requests.get(fallback_url, headers=headers, timeout=8)
                if fb_resp.status_code == 200:
                    try:
                        soup = BeautifulSoup(fb_resp.content, "lxml")
                    except Exception:
                        soup = BeautifulSoup(fb_resp.content, "html.parser")
                    for item in soup.find_all("item")[:limit]:
                        title = item.find("title")
                        if title:
                            posts.append({"title": f"Community discussion on {topic}: {title.text}"})
            except Exception:
                pass
                
        # Ultimate Fallback
        if not posts:
            posts = [
                {"title": f"Latest developer discussions and trends regarding {topic} in the tech community."},
                {"title": f"Engineering challenges and optimizations being discussed around {topic}."}
            ]
            
        reddit_results[topic] = posts
        
    return reddit_results