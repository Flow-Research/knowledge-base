"""AI prompt templates for content generation."""

SYSTEM_PROMPT = """You are a technical content curator specializing in technology knowledge bases.
Your role is to create high-quality, well-structured articles from source materials.

Guidelines:
- Write clear, concise technical content
- Focus on educational value
- Include practical examples when relevant
- Cite sources accurately
- Use proper markdown formatting
- Keep content between 500-2000 words
"""

CONTENT_GENERATION_TEMPLATE = """Generate a comprehensive technical article based on the following source material.

**Source Information:**
Title: {title}
URL: {url}
Source Type: {source_type}
Description: {description}
Published: {published_at}

**Full Content:**
{body}

**Target Audience:**
Domain: {domain}
Level: {level}
Category: {category}

**Requirements:**
1. Create an engaging title (if needed, improve the original)
2. Write a clear introduction explaining what this is and why it matters
3. Organize content into logical sections with headers
4. Include code examples if relevant to the source material
5. Add a conclusion with key takeaways
6. Ensure content is appropriate for {level} level readers
7. Focus on the {domain} domain context

**Output Format:**
Return ONLY the markdown content (without YAML frontmatter).
Use proper markdown formatting with headers (##, ###), lists, code blocks, etc.

**Important:**
- DO NOT include any YAML frontmatter (no --- at start)
- Start directly with the article title as # Header
- Write in a clear, educational tone
- Cite the source appropriately in the content
"""

DESCRIPTION_GENERATION_TEMPLATE = """Create a concise description (max 500 characters) for this content:

Title: {title}
Content Preview: {content_preview}

Return ONLY the description text, no other formatting or explanation.
"""

TAGS_GENERATION_TEMPLATE = """Generate 5-10 relevant tags for this technical content.

Title: {title}
Description: {description}
Content: {content_preview}

Return ONLY a comma-separated list of tags, no other text.
Example: machine-learning, python, neural-networks, tutorial
"""
