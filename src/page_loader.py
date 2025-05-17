import requests
from markdownify import markdownify as md
from urllib.parse import quote

class PageLoader:
    """
    A class to fetch the content of a URL and convert it to Markdown.
    """
    def __init__(self, url: str, proxy: str|None = None):
        """
        Initializes the PageLoader with a URL.

        Args:
            url: The URL of the page to load.
        """
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL format. URL must start with http:// or https://")
        
        self.proxy = proxy
        self.url = url
        
        self.html_content = None
        self.markdown_content = None

    def __fetch_html(self, proxy = False) -> str | None:
        """
        Fetches the HTML content from the URL.

        Returns:
            The HTML content as a string, or None if the request fails.
        """
        
        try:
            if proxy:
                print(f'Using proxy: {self.proxy} for request')
                response = requests.get(self.proxy + '?url=' + quote(self.url), timeout=30)
            else:
                response = requests.get(self.url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            self.html_content = response.text
            return self.html_content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {self.url}: {e}")
            self.html_content = None
            return None

    def __convert_to_markdown(self) -> str | None:
        """
        Converts the fetched HTML content to Markdown.

        Returns:
            The Markdown content as a string, or None if HTML content is not available.
        """
        if self.html_content is None:
            print("HTML content not fetched yet. Call __fetch_html() first.")
            return None

        try:
            self.markdown_content = md(self.html_content)
            return self.markdown_content
        except Exception as e:
            print(f"Error converting HTML to Markdown: {e}")
            self.markdown_content = None
            return None

    def get_markdown(self) -> str | None:
        """
        Fetches the HTML content and converts it to Markdown.

        Returns:
            The Markdown content as a string, or None if any step fails.
        """
        if self.__fetch_html():
            return self.__convert_to_markdown()
        elif self.__fetch_html(proxy=True):
            return self.__convert_to_markdown()
        else:
            return None
