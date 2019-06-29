import requests
from bs4 import BeautifulSoup

#Useful urls
search_url = 'https://archiveofourown.org/works/search'
work_chapters_url = 'https://archiveofourown.org/downloads/{}/out.html'

#Default values for http requests, so that archiveofourown.com won't block requests
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
tos_cookies = {'accepted_tos': '20180513'}

#Fetch page using default cookies and headers that allow the request to suceed
def fetch_from_ao(url, params={}):
    return requests.get(url, params=params, cookies=tos_cookies, headers=headers).text


class Chapter(object):
    def __init__(self, work_id, chapter_number, title, html):
        self.work_id = work_id
        self.chapter_number = chapter_number
        self.title = title
        self.html = html

    #Fetch and parse all chapters associated with a work id
    @staticmethod
    def fetch_chapters_from_work_id(work_id):
        page_html = fetch_from_ao(work_chapters_url.format(work_id))
        soup = BeautifulSoup(page_html, 'lxml')

        chapters = []
        chapters_elem = soup.find(id='chapters')
        userstuff_elems = chapters_elem.find_all('div', class_='userstuff', recursive=False) if chapters_elem else []
        for chapter_number, elem in enumerate(userstuff_elems, start=1):
            title_elem = None

            elem_prev_sibling = elem.find_previous_sibling()
            if elem_prev_sibling:
                if elem_prev_sibling.name == 'h2':
                    title_elem = elem_prev_sibling
                elif elem_prev_sibling['class']:
                    title_elem = elem_prev_sibling.find('h2')

            title = title_elem.text if title_elem else ''
            chapter_html = elem.decode_contents().strip()

            chapters.append(Chapter(work_id, chapter_number, title, chapter_html))

        return chapters


#Class for storing information relating to a single fanfiction work
class Work(object):
    def __init__(self, work_id, fandom, title, author, summary, language, words, kudos, hits, bookmarks, comment_count, chapter_count, warning_tags, relationship_tags, character_tags, assorted_tags, series_ids):
        self.work_id = work_id
        self.fandom = fandom
        self.title = title
        self.author = author
        self.summary = summary
        self.language = language
        self.words = words
        self.kudos = kudos
        self.hits = hits
        self.bookmarks = bookmarks
        self.comment_count = comment_count
        self.chapter_count = chapter_count
        self.relationship_tags = relationship_tags
        self.character_tags = character_tags
        self.warning_tags = warning_tags
        self.assorted_tags = assorted_tags
        self.series_ids = series_ids

    #Parse required values about a work, from a work search result's html
    @staticmethod
    def parse_result_element(result_element):
        #Parse title, author, and fandom from header
        children = result_element.findChildren()
        headerElements = children[0].findChildren()[0].findChildren()
        title = headerElements[0].text if len(headerElements) >= 1 else ''
        author = headerElements[1].text if len(headerElements) >= 2 else '' 
        fandom = result_element.find(class_='fandoms heading').text

        #Required elements
        work_id = int(result_element['id'].split('_')[1])
        
        summary_elem = result_element.find(class_='userstuff summary')
        summary = summary_elem.text if summary_elem else None

        #Parse tags
        tags_element = result_element.find(class_='tags commas')
        warning_tags = [elem.text for elem in tags_element.find_all('li', class_='warnings')]
        relationship_tags = [elem.text for elem in tags_element.find_all('li', class_='relationships')]
        character_tags = [elem.text for elem in tags_element.find_all('li', class_='characters')]
        assorted_tags = [elem.text for elem in tags_element.find_all('li', class_='freeforms')]

        #Parse stat elements
        stats_element = result_element.find(class_='stats')
        language = stats_element.find('dd', class_='language').text
        words_element = stats_element.find('dd', class_='words')
        try:
            words = int(words_element.text.replace(',', ''))
        except ValueError:
            words = 0
        kudos_element = stats_element.find('dd', class_='kudos')
        kudos = int(kudos_element.text) if kudos_element else 0
        hits_element = stats_element.find('dd', class_='hits')
        hits = int(hits_element.text) if hits_element else 0
        bookmarks_element = stats_element.find('dd', class_='bookmarks')
        bookmarks = int(bookmarks_element.text) if bookmarks_element else 0
        comment_count_element = stats_element.find('dd', class_='comments')
        comment_count = int(comment_count_element.text) if comment_count_element else 0
        chapter_count = int(stats_element.find('dd', class_='chapters').text.split('/')[0])

        #Parse series
        series_elem = result_element.find(class_='series')
        series_ids = [link_elem['href'].split('/')[-1] for link_elem in series_elem.find_all('a')] if series_elem else []

        return Work(work_id, fandom, title, author, summary, language, words, kudos, hits, bookmarks, comment_count, chapter_count, warning_tags, relationship_tags, character_tags, assorted_tags, series_ids)
        
    #Fetch all chapters for a given work
    def fetch_chapters(self):
        return Chapter.fetch_chapters_from_work_id(self.work_id)

#Query paramater constant values
class SORT_DIR:
    DESC = 'desc'
    ASC = 'asc'

class SORT_BY: #TODO: Get rest of values from search page
    BEST_MATCH = '_score'
    HITS = 'hits'
    KUDOS = 'kudos_count'

class CROSSOVERS:
    INCLUDE_CROSSOVERS = ''
    EXCLUDE_CROSSOVERS = 'F'
    ONLY_CROSSOVERS = 'T'

class COMPLETETION_STATUS:
    ANY = ''
    COMPLETE = 'T'
    INPROGRESS = 'F'

class RATING:
    EXPLICIT = '13'
    MATURE = '12'
    TEEN = '11'
    GENERAL_AUDIENCE = '10'
    NOT_RATED = '9'

class LANGUAGE:
    ENGLISH = '1'
    #TODO: Create a script to rip the rest of the languages

#TODO: Throw error if page has no results, MAYBE NOT THOUGHT BECAUSE THIS IS JUST A FETCHER??
#Returns a search result page's html
@staticmethod
def fetch_search_page(query_params, page_num):
    return Fetcher.fetch_url(search_url, query_params)

#TODO: Throw exception if work_id isn't the id of a work
#Returns html of page containing chapters of 
@staticmethod
def fetch_work_chapters_page(work_id):
    return Fetcher.fetch_url(work_url.format(work_id))

#Class for fetching specific search pages
class SearchQuery(object):
    def __init__(self, **kwargs):
        self.query_params = {
            'commit': 'Search',
            'work_search[fandom_names]': ','.join(kwargs.get('fandom_names', [])),
            'work_search[complete]': kwargs.get('completetion_status', COMPLETETION_STATUS.ANY),
            'work_search[crossover]': kwargs.get('crossovers', CROSSOVERS.INCLUDE_CROSSOVERS),
            'work_search[single_chapter]': kwargs.get('single_chapter', 0),
            'work_search[sort_direction]': kwargs.get('sort_direction', SORT_DIR.DESC),
            'work_search[sort_column]': kwargs.get('sort_by', SORT_BY.BEST_MATCH),
            'work_search[rating_ids]': ','.join(kwargs.get('rating_ids', '')),
            'work_search[language_id': kwargs.get('language_id', '')
        }

    #Parse out the works from a results page's html
    def parse_page_results(self, page_html):
        soup = BeautifulSoup(page_html, 'lxml')
        result_elements = soup.find_all('li', class_='work blurb group')
        works = [Work.parse_result_element(result_element) for result_element in result_elements]
        return works

    #Parse out the page count from page's html
    def parse_page_count(self, page_html):
        soup = BeautifulSoup(page_html, 'lxml')
        page_count_element_parent = soup.find(class_='pagination actions')
        page_count_element = page_count_element_parent.find_all('a')[-2]
        page_count = int(page_count_element.text)
        return page_count
        
    #Fetch and parse a page of results
    def fetch_page_results(self, page_number):
        self.query_params['page'] = page_number
        page_html = fetch_from_ao(search_url, params=self.query_params)
        return self.parse_page_results(page_html)

    #Fetch results page and parse out the number of results pages
    def fetch_page_count(self):
        page_html = fetch_from_ao(search_url, params=self.query_params)
        return self.parse_page_count(page_html)
