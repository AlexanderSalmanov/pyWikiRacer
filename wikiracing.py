from typing import List
import requests
import json 

from models import WikiPage 
from db import SessionLocal

from decorators import time_elapsed

REQUESTS_PER_MINUTE = 100
LINKS_PER_PAGE = 200
API_URL = "https://uk.wikipedia.org/w/api.php"
TITLE_RED_FLAGS = ['/', ':']


class InvalidPageException(Exception):
    
    def __init__(self, page_title=None):
        self.page_title = page_title 
        self.message = f"Can't parse wikipedia page {self.page_title or 'this term'}." 
        super().__init__(self.message)
    

class WikiRacer:
    
    def _validate_page(self, title):
        """Helper method for validating pages by the provided search term. 
        Excludes technical articles or non-existing pages.
        Encapsulates _get_links() method in itself to avoid repetitive API calls.

        Args:
            title (str): title of a wikipedia page; search term

        Raises:
            InvalidPageException: Exception which alerts that the provided page 
                                title is invalid.

        Returns:
            tuple(bool, list): Boolean indicating if the validation succeeded or 
                                not and a list of links in case of a successful 
                                validation. 
        """
        valid_title = not all(
            [char in TITLE_RED_FLAGS for char in title]
        )
        page_links = self._get_links(title)
        if not valid_title or not len(page_links):
            raise InvalidPageException(
                page_title=title
            )
        return (True, page_links)
        
    def _get_links(self, page):
        """Fetches links which are contained by a specific wikipage. Response 
        data gets unpacked in several stages. Empty list gets returned in case 
        if an invalid search term.

        Args:
            page (str): title of a wikipedia page; search term
            pllimit (int, optional): Max amount of links to retrieve. Defaults to LINKS_PER_PAGE.

        Returns:
            list: list of links on a desired wikipedia page.
        """
        session = requests.Session()
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'links',
            'pllimit': LINKS_PER_PAGE,
            'titles': page,
        }
        response = session.get(url=API_URL, params=params).json()
        links = response['query']['pages']
        results = [links[key] for key in list(links.keys())]
        try:
            links = [entry['links'] for entry in results][0]
        except KeyError:
            return []
        link_titles = [entry['title'] for entry in links if all([char not in TITLE_RED_FLAGS for char in entry['title']])]
        return link_titles
        
    def _get_backlinks(self, page):
        """Fetches all links that lead to the given page.

        Args:
            page (str): title of a wikipedia page; search term

        Returns:
            list(str): A list of all page titles which lead to the given page.
        """
        session = requests.Session()
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'backlinks',
            'bltitle': page,
            'bllimit': LINKS_PER_PAGE,
        }
        response = session.get(url=API_URL, params=params).json()
        backlinks = [entry.get('title') for entry in response['query']['backlinks']] 
        return backlinks
    
    def _create_link_obj(self, title, links, session):
        """Creates an instance of WikiPage and saves it to the database.

        Args:
            title (str): title of a page instance
            links (list): list of links contained by the given page
            session (Session): current session instance
        Returns:
            WikiPage: newly created WikiPage instance 
        """
        page_obj = WikiPage(
            title=title,
            links=links,
            backlinks=self._get_backlinks(title)
        )
        session.add(page_obj)
        session.commit()
        return page_obj
    
    def _page_leads_to_term(self, page_title, links, term, path):
        """Repeated piece of functionality placed to a separate method for better 
        readability. Checks if the destination search term is in the current page's links,
        and, if so, inserts this page's title to the path. Returns a boolean 
        which indicates whether the check succeeded or not.

        Args:
            page_title (str): title of a page
            links (list): list of links contained by a specific page
            term (str): a desired term to find path to
            path (list): Potential path to be returned by the find_path() method.

        Returns:
            bool: Boolean value indicating if the check succeeded or not.
        """
        path_found = False
        if term in links:
            path_found = True
            path.insert(1, page_title)
        return path_found
        
    @time_elapsed
    def find_path(self, start: str, finish: str) -> List[str]:
        try:
            start_page, start_page_links = self._validate_page(start)
            final_page = self._validate_page(finish) # checking if both start and finish queries lead to existing and valid pages
        except InvalidPageException as e:
            return str(e)

        path = [start, finish]
        path_found = False
        
        with SessionLocal() as session:
            for link in start_page_links:

                    page_db_lookup = session.query(WikiPage).filter_by(
                                            title=link
                                        ).first()
                    if page_db_lookup:
                        path_found = self._page_leads_to_term(
                            page_title=link,
                            links=list(page_db_lookup.links),
                            term=finish,
                            path=path
                        )
                        if path_found:
                            break
                    else:
                        try:
                            current_page, page_links = self._validate_page(link)
                        except InvalidPageException as e:
                            continue 
                        page_obj = self._create_link_obj(link, page_links, session)
                        path_found = self._page_leads_to_term(
                            page_title=link,
                            links=page_links,
                            term=finish,
                            path=path
                        )
                        if path_found:
                            break
                        
        return path if path_found else []
    

racer = WikiRacer()

if __name__ == '__main__':
    res = racer.find_path('Дружба', 'Рим')
    print(res)








