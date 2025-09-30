Developer Tools Research Agent 🔍🏢
An AI-powered research assistant designed to help developers find and analyze developer tools, libraries, and services. Built with LangGraph and Firecrawl, this agent automates the process of researching technical tools and provides structured comparisons.

🚀 Features
🔍 Smart Tool Discovery: Automatically extracts relevant developer tools from technical articles and documentation

🏢 Company Analysis: Provides detailed analysis of developer tools including pricing, tech stack, and capabilities

🛠️ Developer-Focused Insights: Specialized analysis for developer needs including API availability, language support, and integrations

📊 Structured Comparisons: Side-by-side comparison of multiple tools with actionable recommendations

🌐 Web Scraping: Leverages Firecrawl for comprehensive web research and content extraction

🏗️ Architecture
Workflow Engine: LangGraph for orchestrated research workflows

AI Models: OpenAI GPT-4 for analysis and extraction

Web Research: Firecrawl for search and content scraping

Data Models: Pydantic for structured data validation

Configuration: Environment-based configuration with python-dotenv

📦 Installation
Prerequisites
Python 3.13+

Firecrawl API key

OpenAI API key

Setup
Clone the repository

bash
git clone <your-repository-url>
cd advanced-agent
Install dependencies
Using pip:

bash
pip install -r requirements.txt
Using uv (recommended):

bash
uv sync
Configure environment variables
Create a .env file in the project root:

env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
🎯 Usage
Run the research agent:

bash
python main.py
Example interaction:

text
🔍 Developer Tools Query: Python web frameworks

🔍 Finding articles about: Python web frameworks
Extracted tools: Django, Flask, FastAPI, Pyramid, Tornado
🔬 Researching specific tools: Django, Flask, FastAPI, Pyramid
Generating recommendations

📊 Results for: Python web frameworks
============================================================

1. 🏢 Django
   🌐 Website: https://www.djangoproject.com/
   💰 Pricing: Free
   📖 Open Source: True
   🛠️ Tech Stack: Python, Django ORM, Template Engine
   💻 Language Support: Python
   🔌 API: ✅ Available
   🔗 Integrations: PostgreSQL, MySQL, SQLite, Redis
   📝 Description: High-level Python web framework for rapid development

2. 🏢 Flask
   🌐 Website: https://flask.palletsprojects.com/
   💰 Pricing: Free
   📖 Open Source: True
   🛠️ Tech Stack: Python, Werkzeug, Jinja2
   💻 Language Support: Python
   🔌 API: ✅ Available
   🔗 Integrations: SQLAlchemy, MongoDB, Celery
   📝 Description: Lightweight WSGI web application framework

Developer Recommendations:
----------------------------------------
For Python web development, FastAPI is recommended for modern API-first applications due to its excellent performance and automatic OpenAPI documentation. Django provides the most batteries-included experience with built-in admin and ORM, while Flask offers maximum flexibility for custom implementations. All frameworks are free and open source.
🏗️ Project Structure
text
advanced-agent/
├── main.py                 # Main application entry point
├── pyproject.toml         # Project dependencies and configuration
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore rules
├── .python-version       # Python version specification
├── uv.lock              # uv lock file
└── src/
    ├── __init__.py
    ├── workflow.py       # LangGraph workflow definition
    ├── firecrawl.py     # Firecrawl service integration
    ├── models.py        # Pydantic data models
    └── prompts.py       # LLM prompt templates
🔧 Core Components
Workflow (src/workflow.py)
State Management: ResearchState for tracking research progress

Multi-step Process: Extract tools → Research → Analyze → Recommend

Error Handling: Graceful fallbacks for failed operations

Data Models (src/models.py)
CompanyInfo: Structured company and tool information

CompanyAnalysis: Developer-focused analysis results

ResearchState: Workflow state management

Services (src/firecrawl.py)
Web Search: Company and tool discovery

Content Scraping: Detailed information extraction

Error Handling: Robust API integration

🛠️ Configuration
API Keys
Firecrawl: Get your API key from firecrawl.dev

OpenAI: Get your API key from platform.openai.com

Model Configuration
The agent uses gpt-4o-mini by default. You can modify this in src/workflow.py:

python
self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)  # Change model here
📋 Example Queries
"Python testing frameworks"

"JavaScript build tools"

"Database ORM libraries"

"Cloud deployment platforms"

"API development tools"

"Machine learning frameworks"

🚨 Error Handling
The agent includes comprehensive error handling for:

Missing API keys

Network timeouts

Content parsing failures

LLM response validation

Invalid URLs

🔄 Extending the Agent
Adding New Analysis Fields
Update CompanyAnalysis in models.py

Add corresponding prompts in prompts.py

Modify the analysis step in workflow.py

Custom Workflows
Extend the StateGraph in workflow.py to add new research steps:

python
graph.add_node("custom_step", self._custom_step)
graph.add_edge("analyze", "custom_step")
📄 License
MIT License - see LICENSE file for details

🤝 Contributing
Fork the repository

Create a feature branch

Make your changes

Add tests if applicable

Submit a pull request

🐛 Troubleshooting
Common Issues:

Missing API keys: Ensure both FIRECRAWL_API_KEY and OPENAI_API_KEY are set in .env

Import errors: Verify all dependencies are installed with uv sync or pip install -r requirements.txt

Firecrawl errors: Check your Firecrawl account status and API quota

Debug Mode: Add debug prints in the workflow steps to trace execution flow.

