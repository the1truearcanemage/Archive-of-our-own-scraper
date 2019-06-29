import sqlite3
from AO3Scraper import Work, Chapter

class WorkIterator(object):
    def __init__(self, conn, load_chapters=False):
        self.conn = conn
        self.cursor = conn.cursor()
        #Fetch all works, with the row elements matching the order of the Work constructor
        self.cursor.execute('SELECT * FROM works')

    def filter_tags(self, tags, tag_type):
        return [tag[1] for tag in filter(lambda tag: tag[2] == tag_type, tags)]

    def make_work_from_rows(self, work_row, work_tag_rows, series_id_rows):
        warning_tags = self.filter_tags(work_tag_rows, 'warning')
        relationship_tags = self.filter_tags(work_tag_rows, 'relationship')
        character_tags = self.filter_tags(work_tag_rows, 'character')
        assorted_tags = self.filter_tags(work_tag_rows, 'assorted')
        series_ids = [row[1] for row in series_id_rows]
        return Work(*work_row[:-1], warning_tags, relationship_tags, character_tags, assorted_tags, series_ids)

    def __iter__(self):
        return self

    def __next__(self):
        work_row = self.cursor.__next__()
        work_id = work_row[0]
        work_tag_rows = self.conn.cursor().execute('SELECT * FROM work_tags WHERE work_id=?', (work_id, )).fetchall()
        series_id_rows = self.conn.cursor().execute('SELECT * FROM series WHERE work_id=?', (work_id, )).fetchall()

        return self.make_work_from_rows(work_row, work_tag_rows, series_id_rows)

class ChapterIterator(object):
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT * FROM chapters')

    def chapter_from_row(self, chapter_row):
        return Chapter(*chapter_row)

    def __iter__(self):
        return self

    def __next__(self):
        chapter_row = self.cursor.__next__()
        return self.chapter_from_row(chapter_row)

class AO3Database(object):
    def __init__(self, filepath=None):
        if filepath:
            self.open(filepath)

    def open(self, filepath):
        try:
            self.conn = sqlite3.connect(filepath)
            self.cursor = self.conn.cursor()
            self.build_tables()
        except sqlite3.Error as e:
            print('Error connecting to sqlite database!')

    def commit():
        if self.curr:
            self.curr.commit()
        else:
            print('Error: no database open')

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    #Allows the use of with keyword, automatically opens on enterance and closes database upon exit
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def build_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS works (
                work_id             INTEGER NOT NULL,
                work_fandom         TEXT NOT NULL,
                work_title          TEXT NOT NULL,
                work_author         TEXT NOT NULL,
                work_summary        TEXT,
                work_language       TEXT NOT NULL,
                work_word_count     INTEGER NOT NULL,
                work_kudos          INTEGER NOT NULL,
                work_hits           INTEGER NOT NULL,
                work_bookmarks      INTEGER NOT NULL,
                work_comment_count  INTEGER NOT NULL,
                work_chapter_count  INTEGER NOT NULL,
                stored_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                work_id         INTEGER NOT NULL,
                chapter_number  INTEGER NOT NULL,
                title           TEXT NOT NULL,
                html            TEXT NOT NULL
            );
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_tags (
                work_id     INTEGER NOT NULL,
                tag         TEXT NOT NULL,
                tag_type    TEXT CHECK(tag_type IN ('character', 'relationship', 'assorted', 'warning')) NOT NULL
            );
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS series (
                work_id     INTEGER NOT NULL,
                series_id   INTEGER NOT NULL
            );
        ''')
        

    def insert_work(self, work, save_chapters=False):
        w = work

        #Insert non-list values of work
        work_params = (w.work_id, w.fandom, w.title, w.author, w.summary, w.language,
            w.words, w.kudos, w.hits, w.bookmarks, w.comment_count, w.chapter_count)
        self.cursor.execute('INSERT INTO works VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DateTime("now"))', work_params)

        #Split each list value into it's own table using the work_id as a common key
        #Insert each tag as it's own row
        tag_lists = [w.relationship_tags, w.character_tags, w.warning_tags, w.assorted_tags]
        tag_types = ['relationship', 'character', 'warning', 'assorted']
        for tags, tag_type in zip(tag_lists, tag_types):
            for tag in tags:
                self.insert_tag(w.work_id, tag, tag_type)
        #Insert each series as it's own row
        for series_id in w.series_ids:
            self.insert_series(w.work_id, series_id)

        if save_chapters:
            for chapter in w.fetch_chapters():
                self.insert_chapter(chapter)
        

    def insert_chapter(self, chapter):
        params = (chapter.work_id, chapter.chapter_number, chapter.title, chapter.html)
        self.cursor.execute('INSERT INTO chapters VALUES (?,?,?,?)', params)

    def insert_tag(self, work_id, tag, tag_type):
        self.cursor.execute('INSERT INTO work_tags VALUES (?,?,?)', (work_id, tag, tag_type))

    def insert_series(self, work_id, series_id):
        self.cursor.execute('INSERT INTO series VALUES (?,?)', (work_id, series_id))

    #Returns an iterator that iterates over the 
    def get_work_iterator(self, load_chapters=False):
        return WorkIterator(self.conn)

    #Returns the cursor that can be used as an iterator
    def get_chapter_iterator(self):
        return ChapterIterator(self.conn)
