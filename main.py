from typing import Annotated
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
import markdownify
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from openai import BaseModel
from pydantic import AnyUrl, Field
import readabilipy

TOKEN = "51eb25311cbc"
MY_NUMBER = "917982354840"

class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None

class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(token=token, client_id="unknown", scopes=[], expires_at=None)
        return None

class Fetch:
    IGNORE_ROBOTS_TXT = True
    USER_AGENT = "Puch/1.0 (Autonomous)"

    @classmethod
    async def fetch_url(cls, url: str, user_agent: str, force_raw: bool = False) -> tuple[str, str]:
        from httpx import AsyncClient, HTTPError
        async with AsyncClient() as client:
            try:
                response = await client.get(url, follow_redirects=True, headers={"User-Agent": user_agent}, timeout=30)
            except HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))
            if response.status_code >= 400:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - status code {response.status_code}"))
            page_raw = response.text
        content_type = response.headers.get("content-type", "")
        is_page_html = "<html" in page_raw[:100] or "text/html" in content_type or not content_type
        if is_page_html and not force_raw:
            return cls.extract_content_from_html(page_raw), ""
        return page_raw, f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n"

    @staticmethod
    def extract_content_from_html(html: str) -> str:
        ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
        if not ret["content"]:
            return "<error>Page failed to be simplified from HTML</error>"
        return markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)

mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN))

@mcp.tool(description="Serve your resume in plain markdown.")
async def resume() -> str:
    return """
# Aditya

+(91) 7982354840 | aka2005711@gmail.com | [LinkedIn](https://www.linkedin.com/in/aditya-chaudhary)

## EDUCATION
- **B-Tech (ECE with AI and ML)**, Netaji Subhas University of Technology, Delhi (2023-2027)  
  7.73 CGPA (till 3rd Sem)
- **CBSE (Class XII)**, St. Giri Sr. Sec. School, New Delhi (2022-2023)  
  85.4%
- **CBSE (Class X)**, St. Giri Sr. Sec. School, New Delhi (2020-2021)  
  90.4%

## INTERNSHIP
- Intern/Trainee – Teachnook (Edtech)  
  Developed a Sentiment Analysis bot (virtual internship)

## PROJECTS
- **Sentiment Analysis Bot**: Python Streamlit, IMDB dataset
- **Gesture Volume Control**: Use index finger to control volume
- **Gesture Cursor Control**: Use index finger + thumb to control cursor
- **AI Chatbot**: Gemini AI, image/PDF upload, voice commands

## SKILLS
Python, Tensorflow, Scikit Learn, C++, DSA, AI & ML, Communication, Leadership, Teamwork

## CERTIFICATIONS
- Generative AI Workshop (Golden Certificate)
- Wireless Communication with Matlab/Simulink
- Advances in NLP & Generative AI
- Soft Skills (Silver Medalist - NPTEL)
- Design Thinking (Silver Medalist - NPTEL)
"""

@mcp.tool
async def validate() -> str:
    return MY_NUMBER

async def main():
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8080)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
