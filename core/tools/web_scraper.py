"""Web Scraper with Playwright - Day 10 Implementation.

This module provides web scraping capabilities using Playwright,
with AI-powered data extraction and Neo4j knowledge graph integration.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with: pip install playwright && playwright install")

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j driver not installed. Install with: pip install neo4j")

import logging

logger = logging.getLogger(__name__)


class WebScraperConfig:
    """Configuration for the web scraper."""

    def __init__(
        self,
        timeout: int = 30000,
        wait_for_selector: Optional[str] = None,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        self.timeout = timeout
        self.wait_for_selector = wait_for_selector
        self.user_agent = user_agent
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height


class WebScraper:
    """Web scraper using Playwright for browser automation."""

    def __init__(self, config: Optional[WebScraperConfig] = None):
        self.config = config or WebScraperConfig()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._cookies: Dict[str, str] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Initialize Playwright and browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Run: pip install playwright")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless
        )
        self._page = await self.browser.new_page(
            user_agent=self.config.user_agent,
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height
            }
        )
        await self._page.set_default_timeout(self.config.timeout)
        logger.info("WebScraper started successfully")

    async def stop(self):
        """Close browser and cleanup."""
        if self._page:
            await self._page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("WebScraper stopped")

    @property
    def page(self) -> Page:
        """Get the current page."""
        if not self._page:
            raise RuntimeError("Scraper not started. Use async context manager or call start()")
        return self._page

    async def fetch(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_for_timeout: int = 5000
    ) -> Dict[str, Any]:
        """Fetch a URL and return content.

        Args:
            url: URL to fetch
            wait_for: Optional CSS selector to wait for
            wait_for_timeout: Timeout for waiting

        Returns:
            Dict with url, html, text, title, and metadata
        """
        try:
            response = await self.page.goto(url, wait_until="domcontentloaded")

            if wait_for:
                try:
                    await self.page.wait_for_selector(wait_for, timeout=wait_for_timeout)
                except Exception as e:
                    logger.warning(f"Wait for selector timed out: {e}")

            html = await self.page.content()
            text = await self.page.evaluate("document.body.innerText")
            title = await self.page.title()

            # Extract metadata
            metadata = await self.page.evaluate("""() => {
                const getMeta = (name) => {
                    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return el ? el.content : null;
                };
                return {
                    description: getMeta('description'),
                    keywords: getMeta('keywords'),
                    author: getMeta('author'),
                    og_title: getMeta('og:title'),
                    og_description: getMeta('og:description'),
                    og_image: getMeta('og:image'),
                };
            }""")

            # Extract links
            links = await self.page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                return anchors.slice(0, 50).map(a => ({
                    text: a.innerText.trim().substring(0, 100),
                    href: a.href,
                    title: a.title || ''
                })).filter(l => l.href.startsWith('http'));
            }""")

            # Extract images
            images = await self.page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img[src]'));
                return imgs.slice(0, 20).map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    title: img.title || ''
                })).filter(i => i.src.startsWith('http'));
            }""")

            return {
                "success": True,
                "url": url,
                "status": response.status if response else 200,
                "html": html,
                "text": text[:50000],  # Limit text length
                "title": title,
                "metadata": metadata,
                "links": links,
                "images": images,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    async def click_and_extract(
        self,
        url: str,
        click_selector: str,
        extract_selector: str
    ) -> Dict[str, Any]:
        """Click an element and extract content after page change.

        Args:
            url: Initial URL
            click_selector: CSS selector to click
            extract_selector: CSS selector to extract content from

        Returns:
            Extracted content
        """
        await self.page.goto(url)
        await self.page.click(click_selector)
        await self.page.wait_for_load_state("networkidle")

        content = await self.page.query_selector(extract_selector)
        if content:
            return await content.inner_text()
        return None

    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str],
        submit_selector: str
    ) -> Dict[str, Any]:
        """Fill a form and submit.

        Args:
            url: Form URL
            form_data: Dict of {selector: value}
            submit_selector: Submit button selector

        Returns:
            Result after submission
        """
        await self.page.goto(url)

        for selector, value in form_data.items():
            await self.page.fill(selector, value)

        await self.page.click(submit_selector)
        await self.page.wait_for_load_state("networkidle")

        return {
            "url": self.page.url,
            "title": await self.page.title()
        }

    async def take_screenshot(self, path: str, full_page: bool = False) -> str:
        """Take a screenshot.

        Args:
            path: Path to save screenshot
            full_page: Capture full page or just viewport

        Returns:
            Path to screenshot
        """
        await self.page.screenshot(path=path, full_page=full_page)
        return path

    async def evaluate_js(self, script: str) -> Any:
        """Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of script execution
        """
        return await self.page.evaluate(script)


class AIDataExtractor:
    """AI-powered data extraction from scraped content."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None

    def _get_client(self):
        """Get or create AI client."""
        if not self._client and self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic SDK not installed")
        return self._client

    async def extract_structured_data(
        self,
        content: str,
        schema: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured data from content using AI.

        Args:
            content: Text content to extract from
            schema: JSON schema defining what to extract
            prompt: Optional custom prompt

        Returns:
            Extracted data matching the schema
        """
        default_prompt = f"""Extract structured data from the following content based on this schema:

Schema:
{json.dumps(schema, indent=2)}

Content:
{content[:10000]}

Return valid JSON matching the schema exactly. Include only the extracted fields."""

        extraction_prompt = prompt or default_prompt
        client = self._get_client()

        if not client:
            # Fallback to regex-based extraction
            return self._fallback_extract(content, schema)

        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": extraction_prompt}]
            )

            # Parse JSON from response
            text = response.content[0].text
            # Extract JSON block if present
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())

            return {"raw_text": text, "parsed": False}

        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            return self._fallback_extract(content, schema)

    def _fallback_extract(
        self,
        content: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback regex-based extraction when AI is unavailable."""
        result = {}
        properties = schema.get("properties", {})

        for field, field_schema in properties.items():
            field_type = field_schema.get("type", "string")
            pattern = field_schema.get("pattern")

            if pattern:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    result[field] = match.group(1) if match.groups() else match.group()
            elif field_type == "string":
                # Try to find the field name in content
                pattern = rf"{field.replace('_', ' ')[:20]}[:\s]+([^\n]+)"
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    result[field] = match.group(1).strip()

        return result

    async def extract_people(self, content: str) -> List[Dict[str, str]]:
        """Extract people mentioned in content.

        Args:
            content: Text content

        Returns:
            List of people with name, role, organization
        """
        schema = {
            "type": "object",
            "properties": {
                "people": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "organization": {"type": "string"}
                        }
                    }
                }
            }
        }

        result = await self.extract_structured_data(content, schema)
        return result.get("people", [])

    async def extract_organizations(self, content: str) -> List[Dict[str, str]]:
        """Extract organizations mentioned in content.

        Args:
            content: Text content

        Returns:
            List of organizations with name, type, description
        """
        schema = {
            "type": "object",
            "properties": {
                "organizations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                }
            }
        }

        result = await self.extract_structured_data(content, schema)
        return result.get("organizations", [])


class Neo4jKnowledgeGraph:
    """Neo4j knowledge graph integration for storing extracted data."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password"
    ):
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not installed. Run: pip install neo4j")

        self.uri = uri
        self.username = username
        self.driver = None
        self._connect(password)

    def _connect(self, password: str):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def create_entity(
        self,
        label: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an entity node in the graph.

        Args:
            label: Node label (e.g., 'Person', 'Organization')
            properties: Node properties

        Returns:
            Created node data
        """
        if not self.driver:
            return {"error": "Not connected to Neo4j"}

        with self.driver.session() as session:
            # Build property assignments
            props_str = ", ".join([f"${k}" for k in properties.keys()])
            query = f"CREATE (n:{label} {{{props_str}}}) RETURN id(n) as id, n"

            result = session.run(query, properties)
            record = result.single()

            return {
                "id": record["id"],
                "label": label,
                "properties": properties
            }

    def create_relationship(
        self,
        from_id: int,
        to_id: int,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes.

        Args:
            from_id: Start node ID
            to_id: End node ID
            relationship_type: Type of relationship (e.g., 'WORKS_AT')
            properties: Optional relationship properties

        Returns:
            Created relationship data
        """
        if not self.driver:
            return {"error": "Not connected to Neo4j"}

        props = properties or {}
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()]) if props else ""

        with self.driver.session() as session:
            query = f"""
            MATCH (a), (b)
            WHERE id(a) = $from_id AND id(b) = $to_id
            CREATE (a)-[r:{relationship_type} {{{props_str}}}]->(b)
            RETURN id(r) as id, type(r) as type
            """
            result = session.run(query, {"from_id": from_id, "to_id": to_id, **props})
            record = result.single()

            return {
                "id": record["id"],
                "type": record["type"],
                "from_id": from_id,
                "to_id": to_id
            }

    def find_node(
        self,
        label: str,
        property_key: str,
        property_value: Any
    ) -> List[Dict[str, Any]]:
        """Find nodes by property value.

        Args:
            label: Node label
            property_key: Property to search by
            property_value: Value to match

        Returns:
            List of matching nodes
        """
        if not self.driver:
            return [{"error": "Not connected to Neo4j"}]

        with self.driver.session() as session:
            query = f"MATCH (n:{label}) WHERE n.{property_key} = $value RETURN id(n) as id, n"
            result = session.run(query, {"value": property_value})

            return [
                {"id": record["id"], **dict(record["n"])}
                for record in result
            ]

    def get_relationships(
        self,
        node_id: int,
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all relationships for a node.

        Args:
            node_id: Node ID
            relationship_type: Optional filter by relationship type

        Returns:
            List of relationships
        """
        if not self.driver:
            return [{"error": "Not connected to Neo4j"}]

        rel_filter = f":{relationship_type}" if relationship_type else ""

        with self.driver.session() as session:
            query = f"""
            MATCH (a)-[r{rel_filter}]->(b)
            WHERE id(a) = $node_id
            RETURN id(r) as id, type(r) as type, b
            """
            result = session.run(query, {"node_id": node_id})

            return [
                {
                    "id": record["id"],
                    "type": record["type"],
                    "target": dict(record["b"])
                }
                for record in result
            ]

    def execute_cypher(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a custom Cypher query.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            Query results
        """
        if not self.driver:
            return [{"error": "Not connected to Neo4j"}]

        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]


class KnowledgeGraphBuilder:
    """Build knowledge graphs from web content."""

    def __init__(self, neo4j: Optional[Neo4jKnowledgeGraph] = None):
        self.neo4j = neo4j
        self.extractor = AIDataExtractor()

    async def scrape_and_index(
        self,
        url: str,
        entity_labels: List[str] = None,
        headless: bool = True
    ) -> Dict[str, Any]:
        """Scrape a URL and index content to knowledge graph.

        Args:
            url: URL to scrape
            entity_labels: Labels to extract (e.g., ['Person', 'Organization'])
            headless: Run browser in headless mode

        Returns:
            Indexed data with node IDs
        """
        entity_labels = entity_labels or ["Person", "Organization", "Location"]

        async with WebScraper() as scraper:
            # Scrape the page
            scrape_result = await scraper.fetch(url)
            if not scrape_result.get("success"):
                return {"error": scrape_result.get("error")}

            content = scrape_result["text"]

            # Extract entities based on labels
            indexed_data = {
                "url": url,
                "title": scrape_result.get("title"),
                "nodes": [],
                "relationships": []
            }

            if not self.neo4j:
                return indexed_data

            # Create page node
            page_node = self.neo4j.create_entity(
                "WebPage",
                {
                    "url": url,
                    "title": scrape_result.get("title"),
                    "scraped_at": datetime.utcnow().isoformat(),
                    "text_length": len(content)
                }
            )
            indexed_data["nodes"].append(page_node)

            # Extract people
            people = await self.extractor.extract_people(content)
            for person in people:
                person_node = self.neo4j.create_entity(
                    "Person",
                    person
                )
                indexed_data["nodes"].append(person_node)

                # Link person to page
                rel = self.neo4j.create_relationship(
                    person_node["id"],
                    page_node["id"],
                    "MENTIONED_IN"
                )
                indexed_data["relationships"].append(rel)

            # Extract organizations
            orgs = await self.extractor.extract_organizations(content)
            for org in orgs:
                org_node = self.neo4j.create_entity(
                    "Organization",
                    org
                )
                indexed_data["nodes"].append(org_node)

                # Link org to page
                rel = self.neo4j.create_relationship(
                    org_node["id"],
                    page_node["id"],
                    "MENTIONED_IN"
                )
                indexed_data["relationships"].append(rel)

            # Create relationships between people and orgs
            for person in people:
                if person.get("organization"):
                    # Find the org node
                    orgs_found = self.neo4j.find_node(
                        "Organization",
                        "name",
                        person["organization"]
                    )
                    if orgs_found:
                        person_node = self.neo4j.find_node(
                            "Person",
                            "name",
                            person["name"]
                        )
                        if person_node:
                            rel = self.neo4j.create_relationship(
                                person_node[0]["id"],
                                orgs_found[0]["id"],
                                "WORKS_AT"
                            )
                            indexed_data["relationships"].append(rel)

            return indexed_data


# Convenience functions for quick usage

async def quick_scrape(url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
    """Quickly scrape a URL.

    Args:
        url: URL to scrape
        wait_for: Optional selector to wait for

    Returns:
        Scraped content
    """
    async with WebScraper() as scraper:
        return await scraper.fetch(url, wait_for=wait_for)


async def quick_extract(url: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Scrape and extract structured data from URL.

    Args:
        url: URL to scrape
        schema: Extraction schema

    Returns:
        Extracted data
    """
    async with WebScraper() as scraper:
        content = await scraper.fetch(url)

    if not content.get("success"):
        return content

    extractor = AIDataExtractor()
    return await extractor.extract_structured_data(content["text"], schema)


async def demo():
    """Demo the web scraper functionality."""
    print("=" * 60)
    print("Day 10 - Web Scraper with Playwright Demo")
    print("=" * 60)

    # Demo 1: Basic scraping
    print("\n1. Basic Web Scraping")
    print("-" * 40)

    async with WebScraper() as scraper:
        result = await scraper.fetch("https://example.com")
        print(f"Title: {result.get('title')}")
        print(f"Success: {result.get('success')}")
        print(f"Links found: {len(result.get('links', []))}")
        print(f"Text preview: {result.get('text', '')[:200]}...")

    # Demo 2: AI Extraction (mock if no API key)
    print("\n2. AI Data Extraction")
    print("-" * 40)

    extractor = AIDataExtractor()
    sample_content = """
    John Smith is the CEO of TechCorp, a leading technology company.
    He was previously the CTO at Innovation Labs.
    Jane Doe is the CFO of TechCorp.
    TechCorp was founded in 2010 and is based in San Francisco.
    """

    schema = {
        "type": "object",
        "properties": {
            "people": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "company": {"type": "string"}
                    }
                }
            }
        }
    }

    extracted = await extractor.extract_structured_data(sample_content, schema)
    print(f"Extracted: {json.dumps(extracted, indent=2)}")

    # Demo 3: Neo4j Integration (if available)
    print("\n3. Neo4j Knowledge Graph")
    print("-" * 40)

    try:
        neo4j = Neo4jKnowledgeGraph(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )

        # Create sample nodes
        person = neo4j.create_entity("Person", {"name": "John Smith", "role": "CEO"})
        org = neo4j.create_entity("Organization", {"name": "TechCorp", "type": "Technology"})
        rel = neo4j.create_relationship(person["id"], org["id"], "WORKS_AT")

        print(f"Created person node: {person}")
        print(f"Created org node: {org}")
        print(f"Created relationship: {rel}")

        neo4j.close()
    except Exception as e:
        print(f"Neo4j not available: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())