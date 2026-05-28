import os
import re
import ssl
import json
import urllib.request
import urllib.parse
from html.parser import HTMLParser

# Base URL of the documentation
BASE_URL = "https://docs.gpu.aiswlab.co.kr/guide/getting-started/"
DOMAIN_LIMIT = "docs.gpu.aiswlab.co.kr"

class SidebarLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()
        
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href")
            if href:
                # Remove fragment identifier if any
                href_clean = href.split("#")[0]
                if href_clean:
                    self.links.add(href_clean)

def get_all_documentation_urls(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    parser = SidebarLinkParser()
    parser.feed(html_content)
    
    resolved_urls = {}
    for link in parser.links:
        # Ignore external links or mailto/tel links
        if link.startswith(("mailto:", "tel:", "javascript:")):
            continue
            
        # Resolve relative URLs
        absolute_url = urllib.parse.urljoin(BASE_URL, link)
        
        # Parse URL to filter by domain and clean trailing slash
        parsed_url = urllib.parse.urlparse(absolute_url)
        if parsed_url.netloc != DOMAIN_LIMIT:
            continue
            
        # Standardize URL: strip query params and fragments, ensure consistent path format
        path = parsed_url.path
        if not path.endswith("/") and not os.path.basename(path).count("."):
            path += "/"
            
        final_url = urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            path,
            "", "", ""
        ))
        
        resolved_urls[final_url] = path
        
    return resolved_urls

def extract_markdown_from_html(html_content):
    # Regex to find <script type="application/json" id="page-markdown-source">...</script>
    pattern = r'<script[^>]*id="page-markdown-source"[^>]*>(.*?)</script>'
    match = re.search(pattern, html_content, re.DOTALL)
    if not match:
        return None
        
    script_content = match.group(1).strip()
    try:
        # The content of the script tag is a JSON string containing the markdown
        markdown_text = json.loads(script_content)
        return markdown_text
    except Exception as e:
        print(f"Error parsing JSON from script: {e}")
        return None

def url_to_local_path(url_path, base_output_dir):
    # Clean up the path
    parts = [p for p in url_path.split("/") if p]
    
    # If path is empty, it's the root/index
    if not parts:
        return os.path.join(base_output_dir, "index.md")
        
    # Check if the last part is a file or a directory
    last_part = parts[-1]
    if "." in last_part:
        # It's a file like style.css or overview.md
        return os.path.join(base_output_dir, *parts)
    else:
        # It's a directory like guide/getting-started/
        return os.path.join(base_output_dir, *parts, "index.md")

def scrape_site():
    html_file = "getting-started.html"
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found. Run downloading first.")
        return
        
    print("Parsing sidebar links from getting-started.html...")
    urls_to_crawl = get_all_documentation_urls(html_file)
    print(f"Found {len(urls_to_crawl)} unique documentation URLs to crawl.")
    
    # Create SSL context to bypass verification for military/VPN site
    ssl_context = ssl._create_unverified_context()
    
    output_dir = "docs_markdown"
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    # Sort URLs to crawl systematically
    sorted_urls = sorted(urls_to_crawl.keys())
    
    for i, url in enumerate(sorted_urls, 1):
        url_path = urls_to_crawl[url]
        local_file_path = url_to_local_path(url_path, output_dir)
        
        print(f"[{i}/{len(sorted_urls)}] Fetching: {url} -> {local_file_path}")
        
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                html_content = response.read().decode("utf-8")
                
            markdown_content = extract_markdown_from_html(html_content)
            if markdown_content:
                # Create parent directories
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                with open(local_file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                print(f"  Success! Saved {len(markdown_content)} characters of raw Markdown.")
                success_count += 1
            else:
                print("  Warning: No markdown source script tag found in HTML. Saving HTML as fallback.")
                # Save HTML instead
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                html_path = local_file_path.replace(".md", ".html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                fail_count += 1
                
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            fail_count += 1
            
    print("\nScraping complete!")
    print(f"Successfully scraped: {success_count} pages")
    print(f"Failed or missing markdown: {fail_count} pages")

if __name__ == "__main__":
    scrape_site()
