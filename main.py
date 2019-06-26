from AO3Scraper import SearchQuery, SORT_BY

#Fetch the most commonly hit harry potter fanfictions and print their name and hit count
q = SearchQuery(fandom_names=['Harry Potter'], sort_by=SORT_BY.HITS)
results = q.fetch_page_results(1)
for result in results:
    print(result.title, ':', result.hits)
    #NOTE: A good amount of fanfictions have a hit count that is not visible to users, but does exist and can be sorted by, so it's minimum and maximum value can be determined but the exact value is not discoverable