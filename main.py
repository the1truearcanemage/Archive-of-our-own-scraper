from AO3Scraper import SearchQuery, SORT_BY
from AO3Database import AO3Database

#Fetch the most commonly hit harry potter fanfictions and print their name and hit count
q = SearchQuery(fandom_names=['Harry Potter'], sort_by=SORT_BY.HITS)
results = q.fetch_page_results(1)

with AO3Database('works.db') as db:
        #Fetch and insert works and chapters
        for work in results:
                db.insert_work(work)
                for chapter in work.fetch_chapters():
                        db.insert_chapter(chapter)

        #Print fetched work's titles
        print('works:')
        work_iter = db.get_work_iterator()
        for work in work_iter:
                print('\t' + work.title)