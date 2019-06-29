from AO3Scraper import SearchQuery, RATING, LANGUAGE
from AO3Database import AO3Database
from tqdm import tqdm

#Fetch the most commonly hit harry potter fanfictions and print their name and hit count

ratings = [RATING.EXPLICIT, RATING.MATURE, RATING.TEEN, RATING.GENERAL_AUDIENCE, RATING.NOT_RATED]

with AO3Database('works.db') as db:
    for rating in ratings:
        q = SearchQuery(fandom_names=['Harry Potter - J. K. Rowling'], rating_ids=[rating], langauge=LANGUAGE.ENGLISH)
        page_count = q.fetch_page_count()
    
        #Fetch and insert works and chapters
        for page in tqdm(range(1, page_count+1)):
            results = q.fetch_page_results(page_count)
            for work in results:
                db.insert_work(work)
                for chapter in work.fetch_chapters():
                    db.insert_chapter(chapter)
