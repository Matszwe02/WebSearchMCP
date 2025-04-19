import logging
from brave_api import BraveApi
from page_loader import PageLoader
from llm import Assistant


class SearchTool:

    def __init__(self, brave_api_key = None):
        self.api_key = brave_api_key
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY environment variable not set for SearchTool.")
        self.brave_api_instance = BraveApi(api_key=self.api_key)


    def get_raw_results(self, query: str) -> list[dict]:
        """
        Args:
            query: The search query string.

        Returns:
            A list of dictionaries containing the raw search results,
            or an empty list if there are no results or an error occurred.
        """
        
        try:
            search_results = self.brave_api_instance.search(query)
        except Exception as e:
            logging.error(f"Error calling Brave API in SearchTool (get_raw_results): {e}")
            return []
        
        if not search_results:
            logging.info("No search results found by Brave API (get_raw_results).")
            return []
        
        return search_results


    def execute(self, query: str) -> str:
        
        raw_results = self.get_raw_results(query)
        
        markdown_results = "## Search Results:\n\n"
        for result in raw_results:
            title = result.get('title', 'No Title')
            url = result.get('url', 'No URL')
            description = result.get('description', 'No Description')
            markdown_results += f"- **[{title}]({url})**\n  {description}\n\n"
        
        return markdown_results.strip()


class PrettyPageTool:

    def __init__(self):
        pass

    def execute(self, url: str) -> str:
        try:
            page_loader = PageLoader(url)
            markdown_content = page_loader.get_markdown()

            if markdown_content:
                return markdown_content
            logging.error(f"Error: Could not fetch or convert content from URL: {url}")
            return None
        
        except Exception as e:
            logging.error(f"Error processing URL '{url}' in PrettyPageTool: {e}")
            return None


class SearchAndPrettyPageTool:
    def __init__(self, brave_api_key = None):
        self.search_tool = SearchTool(brave_api_key=brave_api_key)
        self.pretty_page_tool = PrettyPageTool()
        self.assistant = Assistant()


    def execute(self, query: str, context: str) -> str:
        
        search_results_list = self.search_tool.get_raw_results(query)
        page_outputs = []
        
        for result_info in search_results_list:
            url = result_info['url']
            title = result_info['title']

            prettified_content = self.pretty_page_tool.execute(url)
            if prettified_content.startswith("Error:"):
                logging.warning(f"SearchAndPrettyPageTool: Could not prettify page: {url}")
                page_outputs.append(f"# {title}\n[{url}]\n\nCould not fetch or convert content.\n\n################\n\n")
                continue
            
            trimmed_content = self.assistant.context_trim(f'{query}: {context}', prettified_content) or ''
            
            page_outputs.append(f"# {title}\n[{url}]\n\n{trimmed_content}\n\n################\n\n")
        
        return "".join(page_outputs).strip()
