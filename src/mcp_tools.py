import logging
from brave_api import BraveApi
import concurrent.futures
from page_loader import PageLoader
from llm import Assistant


class SearchTool:

    def __init__(self, brave_api_key):
        self.api_key = brave_api_key
        self.brave_api_instance = BraveApi(api_key=self.api_key)


    def get_raw_results(self, query: str, count: int = 20) -> list[dict]:
        """
        Args:
            query: The search query string.
            count: The maximum number of search results to return.

        Returns:
            A list of dictionaries containing the raw search results,
            or an empty list if there are no results or an error occurred.
        """
        
        try:
            search_results = self.brave_api_instance.search(query, count=count)
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


class PrintPageTool:

    def __init__(self, proxy: str|None = None):
        self.proxy = proxy

    def execute(self, url: str) -> str:
        try:
            page_loader = PageLoader(url, self.proxy)
            markdown_content = page_loader.get_markdown()

            if markdown_content:
                return markdown_content
            logging.error(f"Error: Could not fetch or convert content from URL: {url}")
            return None
        
        except Exception as e:
            logging.error(f"Error processing URL '{url}' in PrintPageTool: {e}")
            return None


class SearchAndPrintPageTool:
    def __init__(self, api_key, api_url, model_name, brave_api_key, proxy: str|None = None):
        
        self.search_tool = SearchTool(brave_api_key=brave_api_key)
        self.print_page_tool = PrintPageTool(proxy)
        self.assistant = Assistant(api_key, api_url, model_name)
    
    def _process_result_sync(self, result_info, query, context):
        url = result_info['url']
        title = result_info['title']
        
        prettified_content = self.print_page_tool.execute(url)
        
        trimmed_content = self.assistant.context_trim(f'{query}: {context}', prettified_content) or ''
        return f"# {title}\n[{url}]\n\n{trimmed_content}\n\n################\n\n"
    
    def execute(self, query: str, context: str) -> str:
        search_results_list = self.search_tool.get_raw_results(query, 4)
        page_outputs = [""] * len(search_results_list)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=None) as executor:
            future_to_index = {
                executor.submit(self._process_result_sync, result_info, query, context): i
                for i, result_info in enumerate(search_results_list)
            }
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    page_outputs[index] = future.result()
                except Exception as exc:
                    logging.error(f"Result {index} generated an exception: {exc}")
                    url = search_results_list[index]['url']
                    title = search_results_list[index]['title']
                    page_outputs[index] = f"# {title}\n[{url}]\n\n\n\n################\n\n"
        
        return "".join(page_outputs).strip()
