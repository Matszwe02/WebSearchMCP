import os
import logging
import re
from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT="""
You are an expert text analyzer. Your task is to identify the most relevant contiguous block of lines in the provided line-numbered text that directly addresses the topics mentioned in the context. Ignore irrelevant sections like navigation menus, sidebars, headers, footers, advertisements, and unrelated comments. Focus solely on the core content related to the context.
Based *only* on the provided context and line-numbered content, identify the single most relevant contiguous block of lines that discusses the topics in the context. Exclude any surrounding noise (navbars, footers, irrelevant comments, etc.).

Respond *only* with the starting and ending line numbers of this block, formatted exactly as: `START: <start_line_number>, END: <end_line_number>`.

Example Response: `START: 15, END: 88`

If no relevant block is found, respond only with `START: 0, END: 0`.
"""

USER_PROMPT = """
Context:
"{context}"

Line-numbered Content:
```
{numbered_content}
```
"""


class Assistant:

    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.api_url = os.environ.get("OPENAI_API_URL", None)
        self.model_name = os.environ.get("OPENAI_MODEL_NAME")
        self.client = OpenAI(api_key=self.api_key,base_url=self.api_url)


    def get_response(self, system_prompt: str, query: str) -> str | None:
        
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]
        try:
            response = self.client.chat.completions.create(model=self.model_name, messages=messages)
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            return None
        
        except Exception as e:
            logging.error(f"An unexpected error occurred during LLM call: {e}")
            return None


    def context_trim(self, context: str, content: str) -> str|None:
        """
        Analyzes content based on context and returns the trimmed content string
        containing the most relevant section, excluding noise like navbars, footers, etc.
        
        Args:
            context: A string describing the relevant topics or context.
            content: The content (e.g., markdown) to analyze.
        
        Returns:
            A string containing the trimmed relevant content, empty string when no relevant content, or None.
        """
        
        lines = content.splitlines()
        numbered_content = ""
        for i, line in enumerate(lines):
            numbered_content += f"{i+1} | {line}\n"
        
        system_prompt = SYSTEM_PROMPT
        user_prompt = USER_PROMPT.format(context=context, numbered_content=numbered_content)
                    
        llm_output = self.get_response(system_prompt, user_prompt)
        
        start_match = re.search(r"start:\s*(\d+)", llm_output, re.IGNORECASE | re.MULTILINE)
        end_match = re.search(r"end:\s*(\d+)", llm_output, re.IGNORECASE | re.MULTILINE)
        
        if start_match and end_match:
            start_line = int(start_match.group(1))
            end_line = int(end_match.group(1))
            
            if start_line == 0 and end_line == 0:
                logging.info("LLM indicated no relevant block found.")
                return ""
            
            if 0 < start_line <= end_line <= len(lines):
                logging.info(f"Context trim successful. Range: {start_line}-{end_line}")
                trimmed_content_lines = lines[start_line-1:end_line]
                trimmed_content = "\n".join(trimmed_content_lines)
                return trimmed_content
            else:
                logging.error(f"LLM returned invalid line range: {start_line}-{end_line} for content with {len(lines)} lines.")
                return None
        else:
            logging.error(f"LLM response did not match expected format 'start: <num>\\nend: <num>'. Response:\n'{llm_output}'")
            return None
