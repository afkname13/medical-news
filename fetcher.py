import hashlib
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
import feedparser
from bs4 import BeautifulSoup

TARGET_JOURNALS = [
    "Nature", "The Lancet", "New England Journal of Medicine", "NEJM", 
    "Cell", "Science", "JAMA", "BMJ", "PNAS", "Nature Medicine", "Science Immunology",
    "Science Translational Medicine"
]

VIRAL_KEYWORDS = [
    "breakthrough", "miracle", "life saving", "instant", "discovery", 
    "new treatment", "cancer", "brain", "heart", "AI", "genetics", 
    "vaccine", "surgery", "longevity", "Alzheimer", "Diabetes", "reversal",
    "anti-aging", "nutrition", "weight loss", "Ozempic", "sleep", "biohacking",
    "superfood", "fitness", "mental health"
]

RSS_FEEDS = {
    "ScienceDaily": "https://www.sciencedaily.com/rss/health_medicine.xml",
    "MedicalXpress": "https://medicalxpress.com/rss-feed/",
    "Nature Medicine": "https://www.nature.com/nm.rss",
    "Harvard Health": "https://www.health.harvard.edu/blog/feed",
    "The Lancet": "https://www.thelancet.com/rssfeeds/lancet/current.xml",
    "JAMA": "https://jamanetwork.com/rss/site/67/mostreadall.xml",
    "NEJM": "https://www.nejm.org/rss/recentActivity.xml",
    "NIH News": "https://www.nih.gov/news-events/news-releases/rss",
    "WHO News": "https://www.who.int/rss-feeds/news-english.xml",
    "Mayo Clinic": "https://newsnetwork.mayoclinic.org/feed/",
    "BMJ": "https://www.bmj.com/rss/recent.xml",
    "Science": "https://www.science.org/rss/news_highlights.xml",
    "Medical News Today": "https://rss.medicalnewstoday.com/medicalnewstoday.xml",
    "HealthDay": "https://www.healthday.com/rss-feeds/healthday-news.xml",
    "Johns Hopkins": "https://www.hopkinsmedicine.org/news/news-releases/feed"
}

TOPIC_STOP_WORDS = {
    "about", "after", "against", "among", "brain", "cancer", "cells",
    "clinical", "could", "daily", "disease", "during", "early", "health",
    "human", "humans", "medical", "medicine", "people", "research",
    "study", "studies", "system", "their", "these", "those", "treatment",
    "using", "with", "from", "into", "over", "under", "news"
}

def normalize_title(title):
    # Lowercase and remove non-alphanumeric characters for robust comparison
    return re.sub(r'[^a-z0-9]', '', title.lower())

def get_article_id(title):
    # MD5 hash of lowercase alphanumeric title
    clean_title = normalize_title(title)
    return hashlib.md5(clean_title.encode('utf-8')).hexdigest()

def score_article(article):
    score = 0
    
    # 1. Freshness Bonus (+5): Published within the current month.
    current_month_year = datetime.now().strftime("%Y-%m")
    if article.get('publish_date') and article['publish_date'].startswith(current_month_year):
        score += 5
        
    # 2. Abstract Depth (+5): >150 words. Favor punchy but descriptive news.
    abstract = article.get('abstract', '')
    word_count = len(abstract.split())
    if word_count > 150:
        score += 5
        
    # 3. Target Journals (+10 Bonus Points)
    journal = article.get('journal', '')
    if any(target.lower() in journal.lower() for target in TARGET_JOURNALS):
        score += 10
        
    # 4. Viral Keywords (+8 Bonus Points to heavily favor viral topics)
    title_and_abstract = (article.get('title', '') + " " + abstract).lower()
    keyword_hits = 0
    for keyword in VIRAL_KEYWORDS:
        if keyword.lower() in title_and_abstract:
            keyword_hits += 1
    score += min(keyword_hits, 3) * 8
            
    article['score'] = score
    return score

def article_sort_key(article):
    publish_date = article.get('publish_date') or ''
    abstract_len = len((article.get('abstract') or '').split())
    journal = article.get('journal') or ''
    return (
        int(article.get('score', 0)),
        publish_date,
        abstract_len,
        len(journal),
    )

def extract_topic_terms(text):
    words = [w.lower() for w in re.findall(r'\w+', text or '') if len(w) > 4]
    return {
        word for word in words
        if word not in TOPIC_STOP_WORDS and not word.isdigit()
    }

def fetch_pubmed():
    articles = []
    print("Fetching PubMed...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        # Broadened search to include highly cited past research and breakthroughs
        "term": '(medical OR health OR clinical OR disease) AND (breakthrough OR discovery OR new treatment OR life saving) AND ("Nature"[ta] OR "Science"[ta] OR "Cell"[ta] OR "New England Journal of Medicine"[ta] OR "Lancet"[ta])',
        "retmode": "json",
        "retmax": 15
    }
    
    try:
        res = requests.get(search_url, params=search_params, timeout=10)
        res.raise_for_status()
        id_list = res.json().get('esearchresult', {}).get('idlist', [])
        
        if not id_list:
            return articles
            
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        f_res = requests.get(fetch_url, params=fetch_params, timeout=10)
        f_res.raise_for_status()
        summaries = f_res.json().get('result', {})
        
        # Fetch article bodies in XML so abstracts align to PMIDs reliably.
        abs_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        abs_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
            "rettype": "abstract"
        }
        abs_res = requests.get(abs_url, params=abs_params, timeout=10)
        abs_res.raise_for_status()
        xml = ET.fromstring(abs_res.text)
        abstracts_by_pmid = {}
        for article_node in xml.findall('.//PubmedArticle'):
            pmid_node = article_node.find('.//PMID')
            if not pmid_node:
                continue
            pmid = "".join(pmid_node.itertext()).strip()
            abstract_sections = article_node.findall('.//AbstractText')
            abstract_parts = []
            for section in abstract_sections:
                label = section.attrib.get('Label')
                text = " ".join("".join(section.itertext()).split())
                if not text:
                    continue
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstracts_by_pmid[pmid] = " ".join(abstract_parts).strip()
        
        for uid in id_list:
            data = summaries.get(uid, {})
            title = data.get('title', '')
            if not title:
                continue
            
            pubdate = data.get('sortpubdate', '').split(' ')[0]
            abstract_text = abstracts_by_pmid.get(uid, "")
            
            article = {
                'id': get_article_id(title),
                'title': title,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                'journal': data.get('fulljournalname', ''),
                'abstract': abstract_text,
                'publish_date': pubdate.replace('/', '-') if pubdate else '',
                'source': 'PubMed'
            }
            articles.append(article)
    except Exception as e:
        print(f"PubMed fetch error: {e}")
        
    return articles

def fetch_rss():
    articles = []
    print("Fetching RSS feeds...")
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title
                abstract = getattr(entry, 'summary', getattr(entry, 'description', ''))
                
                pubdate = ""
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pubdate = f"{entry.published_parsed.tm_year}-{entry.published_parsed.tm_mon:02d}-{entry.published_parsed.tm_mday:02d}"
                
                # Cleanup HTML from abstract
                clean_abstract = BeautifulSoup(abstract, 'html.parser').get_text() if abstract else ''
                
                article = {
                    'id': get_article_id(title),
                    'title': title,
                    'url': getattr(entry, 'link', ''),
                    'journal': source,
                    'abstract': clean_abstract,
                    'publish_date': pubdate,
                    'source': 'RSS',
                    'score_bonus': 10 # Bonus for real-world news diversity
                }
                articles.append(article)
        except Exception as e:
            print(f"RSS fetch error for {source}: {e}")
            
    return articles

def get_top_article(posted_data):
    # posted_data can be a list of IDs or a list of dicts
    posted_ids = set()
    posted_titles_norm = set()
    
    # Round 54: Topic Lock - Block specific keywords for X days
    TOPIC_LOCK_DAYS = 7
    blocked_topics = set()
    
    now = datetime.now()
    
    for item in posted_data:
        if isinstance(item, dict):
            article_id = item.get('id')
            posted_ids.add(article_id)
            title = item.get('title', '')
            if title:
                posted_titles_norm.add(normalize_title(title))
            
            # Check if within Lock window
            ts_str = item.get('timestamp')
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if (now - ts).days < TOPIC_LOCK_DAYS:
                        # Extract basic keywords from title for locking
                        # We block common nouns/terms that define the topic
                        blocked_topics.update(extract_topic_terms(title))
                except: pass
        else:
            posted_ids.add(item)

    # Specific "Hard Blocks" for problematic repetitions
    HARD_BLOCKS = ["viagra", "sildenafil", "erectile", "dysfunction", "sexual", "sex", "libido"]
    # If any hard block was posted recently, add it to blocked_topics
    for hb in HARD_BLOCKS:
        # If we see Viagra in any recent title, block all related terms
        for title_norm in posted_titles_norm:
            if hb in title_norm:
                blocked_topics.update(HARD_BLOCKS)
                break

    articles = fetch_rss() + fetch_pubmed()
    
    new_articles = []
    for a in articles:
        a_id = a['id']
        a_title = a['title']
        a_title_norm = normalize_title(a_title)
        
        if a_id in posted_ids or a_title_norm in posted_titles_norm:
            continue
            
        # Topic Lock Check
        title_words = extract_topic_terms(a_title)
        if any(word in blocked_topics for word in title_words):
            print(f"Skipping article (Topic Lock Active): '{a_title}'")
            continue
            
        new_articles.append(a)
    
    if not new_articles:
        print("No matches after filtering already posted content and Topic Locks.")
        return None
        
    for a in new_articles:
        score_article(a)
        if a.get('score_bonus'):
            a['score'] = int(a['score']) + int(a['score_bonus'])
        
    new_articles.sort(key=article_sort_key, reverse=True)
    top_article = new_articles[0]
    
    print(f"Top article selected: '{top_article['title']}' (Score: {top_article['score']}) [Best of {len(new_articles)} candidates]")
    return top_article

if __name__ == "__main__":
    top = get_top_article([])
    if top:
        print(f"Source: {top['source']} | Journal: {top['journal']}")
        print(f"Publish Date: {top['publish_date']}")
        print(f"Abstract Snippet: {top['abstract'][:200]}...")
