from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
import os
import re
from groq import Groq
import requests
from gtts import gTTS
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

def generate_valid_news_url(keyword: str) -> str:
    """
    Generate Google News RSS URL for the given keyword.
    """
    formatted_keyword = quote_plus(keyword)
    return f"https://news.google.com/rss/search?q={formatted_keyword}&hl=en-IN&gl=IN&ceid=IN:en"

def scrape_news_with_bs4(url: str):
    """
    Scrape news articles using requests and BeautifulSoup (100% Free).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all("item")
        
        articles = []
        for item in items[:5]:  # Top 5 articles
            articles.append({
                "title": item.title.text if item.title else "",
                "link": item.link.text if item.link else "",
                "published": item.pubDate.text if item.pubDate else ""
            })
            
        return articles
    except Exception as e:
        print(f"Error scraping news: {e}")
        return []




def generate_news_urls_to_scrape(list_of_keywords):
    """
    Generates valid RSS news URLs for a list of multiple keywords/topics.
    """
    valid_urls_dict = {}
    for keyword in list_of_keywords:
        valid_urls_dict[keyword] = generate_valid_news_url(keyword)
    return valid_urls_dict

def scrape_reddit_posts(topics_list, limit_per_topic=3):
    reddit_data = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for topic in topics_list:
        subreddit_name = topic.lower().replace(" ", "")
        url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit={limit_per_topic}"
        
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                posts = []
                for item in data['data']['children']:
                    post_data = item['data']
                    posts.append({
                        "title": post_data.get("title"),
                        "url": post_data.get("url")
                    })
                reddit_data[topic] = posts
            else:
                reddit_data[topic] = []
        except Exception as e:
            print(f"Reddit Scrape Error for {topic}: {e}")
            reddit_data[topic] = []

    return reddit_data



def summarize_with_groq_news_script(news_data, reddit_data="", source_mode="both"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY is missing in .env file."

    combined_content = f"News Data:\n{news_data}\n\nReddit Data:\n{reddit_data}"

    prompt = (
        "Role & Persona:\n"
        "You are an elite, senior tech journalist and executive podcast host for a premier Silicon Valley technology briefing. "
        "Your tone is authoritative, highly articulate, analytical, and engaging.\n\n"
        "Objective:\n"
        "Synthesize the provided News and Reddit data into a seamless, high-value audio podcast script that dives deep into technical substance, "
        "trends, and engineering insights regarding the requested topics.\n\n"
        "Strict Constraints & Rules:\n"
        "1. PURE ENGLISH ONLY: The output must be written strictly in professional English. Absolutely no Hindi words, no Hinglish, and no mixed-language translation.\n"
        "2. ZERO FLUFF OR GENERALITIES: Do not wander into generic definitions of Artificial Intelligence or vague high-level concepts. Stay laser-focused on the specific technical updates provided in the source data.\n"
        "3. NO STAGE DIRECTIONS OR METADATA: Do NOT include speaker tags (e.g., 'Host:', 'Presenter:'). Do NOT include bracketed or parenthetical sound cues.\n"
        "4. NARRATIVE FLOW: Write as a single continuous, flowing monologue meant to be read aloud by a Text-to-Speech (TTS) engine.\n"
        "5. SEAMLESS CONTINUITY: If either the News Data or Reddit Data is marked as unavailable or empty, do NOT complain or state that material is missing. Instead, seamlessly focus entirely on the available source material and your deep technical expertise on the topic to deliver a complete, rich podcast script.\n\n"
        "6. SOURCE ATTRIBUTION: Depending on what data is active, begin or frame the podcast strictly according to the source: "
        "if only Reddit data is present, attribute insights according to Reddit discussions; "
        "if only News data is present, attribute insights according to Google News; "
        "if both are present, attribute according to both Reddit and Google News.\n\n"
        f"Source Data to Summarize:\n{combined_content}"
    )

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": "You write clean, direct news narration scripts in pure English with zero stage cues or speaker labels."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=1024
        )
        raw_text = completion.choices[0].message.content
        
        clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', raw_text)
        clean_text = re.sub(r'^(Host|Presenter|Narrator|Speaker\s*\d*):\s*', '', clean_text, flags=re.MULTILINE)
        
        return clean_text.strip()
    except Exception as e:
        print(f"🔥 GROQ ERROR DETAILS: {e}")
        raise e
def convert_text_to_audio(text: str, filename: str = "news_podcast.mp3") -> str:
    """
    Converts summary text into an audio file (.mp3) using gTTS (100% Free).
    """
    try:
        if not text or "Error" in text:
            return "Cannot generate audio due to summary error."

        # gTTS object create karo
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Local folder mein audio file save karo
        tts.save(filename)
        
        return filename
    except Exception as e:
        print(f"Audio Generation Error: {e}")
        return f"Audio Error: {e}"