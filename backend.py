import os
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models import NewsRequest
from utils import (
    generate_news_urls_to_scrape,
    scrape_news_with_bs4,
    scrape_reddit_posts,
    summarize_with_groq_news_script,
    convert_text_to_audio
)

app = FastAPI()
load_dotenv()

import os
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models import NewsRequest
from news_scraper import scrape_news_with_bs4, scrape_reddit_posts, generate_news_urls_to_scrape
from utils import (
    summarize_with_groq_news_script,
    convert_text_to_audio
)

app = FastAPI()
load_dotenv()

@app.post("/generate-news-audio")
async def generate_news_audio(request: NewsRequest):
    try:
        # 1. Topics list extract karo
        topics_list = getattr(request, "topics", None)
        if not topics_list:
            single_topic = getattr(request, "topic", None) or "Artificial Intelligence"
            topics_list = [single_topic]

        news_headlines = []
        reddit_headlines = []

        # 2. Google News Scraping (agar 'news' ya 'both' ho)
        if request.source_type in ["news", "both"]:
            urls_dict = generate_news_urls_to_scrape(topics_list)
            for topic, url in urls_dict.items():
                articles = scrape_news_with_bs4(url)
                for article in articles:
                    if article.get("title"):
                        news_headlines.append(f"- [News/{topic}] {article['title']}")

        # 3. Reddit Scraping (agar 'reddit' ya 'both' ho)
        if request.source_type in ["reddit", "both"]:
            reddit_results = scrape_reddit_posts(topics_list)
            for topic, posts in reddit_results.items():
                for p in posts:
                    if p.get("title"):
                        reddit_headlines.append(f"- [Reddit/{topic}] {p['title']}")

        # 4. Format data based on source_type
        source_mode = request.source_type.lower()
        
        if source_mode == "reddit":
            news_text = "Not requested"
            reddit_text = "\n".join(reddit_headlines) if reddit_headlines else "No Reddit discussions available."
        elif source_mode == "news":
            news_text = "\n".join(news_headlines) if news_headlines else "No news headlines available."
            reddit_text = "Not requested"
        else:  # both
            news_text = "\n".join(news_headlines) if news_headlines else "No news headlines available."
            reddit_text = "\n".join(reddit_headlines) if reddit_headlines else "No Reddit discussions available."

        # 5. Summarize with Groq LLM (passing source_mode for custom attribution)
        news_summary = summarize_with_groq_news_script(news_text, reddit_text, source_mode)

        # 6. Audio Generation (gTTS)
        audio_file = convert_text_to_audio(news_summary)

        if os.path.exists(audio_file):
            return FileResponse(audio_file, media_type="audio/mpeg", filename="news_podcast.mp3")
        else:
            raise HTTPException(status_code=400, detail=f"Audio failed: {audio_file}")

    except Exception as e:
        print(f"🔥 BACKEND ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
           
           