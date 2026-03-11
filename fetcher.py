import hashlib
import re
from datetime import datetime
import requests
import feedparser
from bs4 import BeautifulSoup

TARGET_JOURNALS = [
    "Nature", "The Lancet", "New England Journal of Medicine", "NEJM", 
    "Cell", "Science", "JAMA", "BMJ", "PNAS", "Nature Medicine"
]

VIRAL_KEYWORDS = [
    "breakthrough", "miracle", "life saving", "instant", "discovery", 
    "new treatment", "cancer", "brain", "heart", "AI"
]

RSS_FEEDS = {
    "ScienceDaily": "https://www.sciencedaily.com/rss/health_medicine.xml",
    "MedicalXpress": "https://medicalxpress.com/rss-feed/",
    "Nature Medicine": "https://www.nature.com/nm.rss",
    "Harvard Health": "https://www.health.harvard.edu/blog/feed"
}

def get_article_id(title):
    # MD5 hash of lowercase alphanumeric title
    clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
    return hashlib.md5(clean_title.encode('utf-8')).hexdigest()

def score_article(article):
    score = 0
    
    # 1. Freshness Bonus (+5): Published within the current month.
    current_month_year = datetime.now().strftime("%Y-%m")
    if article.get('publish_date') and article['publish_date'].startswith(current_month_year):
        score += 5
        
    # 2. Abstract Depth (+5): >500 words. (Reduced to >300 to capture punchy but impactful past papers)
    abstract = article.get('abstract', '')
    word_count = len(abstract.split())
    if word_count > 300:
        score += 5
        
    # 3. Target Journals (+10 Bonus Points)
    journal = article.get('journal', '')
    if any(target.lower() in journal.lower() for target in TARGET_JOURNALS):
        score += 10
        
    # 4. Viral Keywords (+5 Bonus Points each instead of +3 to heavily favor viral topics)
    title_and_abstract = (article.get('title', '') + " " + abstract).lower()
    for keyword in VIRAL_KEYWORDS:
        if keyword.lower() in title_and_abstract:
            score += 5
            
    article['score'] = score
    return score

def fetch_pubmed():
    articles = []
    print("Fetching PubMed...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        # Broadened search to include highly cited past research and breakthroughs
        "term": '(clinical trial OR breakthrough OR discovery OR new treatment OR life saving) AND ("Nature"[ta] OR "Science"[ta] OR "Cell"[ta] OR "New England Journal of Medicine"[ta] OR "Lancet"[ta])',
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
        
        # We need abstracts too. Let's get them via efetch.
        abs_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        abs_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "text",
            "rettype": "abstract"
        }
        abs_res = requests.get(abs_url, params=abs_params, timeout=10)
        # Using a simple split fallback, but abstract blocks are separated by double/triple newlines usually
        abstracts_text = abs_res.text.split('\n\n\n')
        
        for idx, uid in enumerate(id_list):
            if uid == 'uids': continue
            data = summaries.get(uid, {})
            title = data.get('title', '')
            if not title:
                continue
            
            pubdate = data.get('sortpubdate', '').split(' ')[0]
            abstract_text = abstracts_text[idx].strip() if idx < len(abstracts_text) else ""
            
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
                    'source': 'RSS'
                }
                articles.append(article)
        except Exception as e:
            print(f"RSS fetch error for {source}: {e}")
            
    return articles

def get_top_article(posted_ids):
    articles = fetch_rss() + fetch_pubmed()
    
    new_articles = [a for a in articles if a['id'] not in posted_ids]
    
    if not new_articles:
        print("No new articles found.")
        return None
        
    for a in new_articles:
        score_article(a)
        
    new_articles.sort(key=lambda x: x['score'], reverse=True)
    
    top_article = new_articles[0]
    print(f"Top article selected: '{top_article['title']}' (Score: {top_article['score']})")
    return top_article

if __name__ == "__main__":
    top = get_top_article([])
    if top:
        print(f"Source: {top['source']} | Journal: {top['journal']}")
        print(f"Publish Date: {top['publish_date']}")
        print(f"Abstract Snippet: {top['abstract'][:200]}...")
