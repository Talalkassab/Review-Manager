# CrewAI Framework Documentation

## 🚀 Overview

CrewAI is a cutting-edge Python framework for orchestrating role-playing, autonomous AI agents that work together seamlessly, tackling complex tasks through collaborative intelligence. It's completely independent of LangChain and built for production use.

**Key Stats (2024):**
- 30.5K GitHub stars
- 1M monthly downloads  
- 100,000+ certified developers
- Production-ready with enterprise features

## 📋 Installation & Requirements

### Requirements
- Python >=3.10 <3.14
- UV package manager (recommended)

### Installation
```bash
# Basic installation
pip install crewai

# With tools
pip install 'crewai[tools]'

# For development
pip install crewai-tools
```

### Quick Start via CLI
```bash
# Create new project
crewai create crew latest-ai-development
cd latest-ai-development

# Install dependencies  
crewai install

# Run the crew
crewai run
```

## 🏗️ Core Architecture

### 1. Agents
**Role-playing AI entities with specific responsibilities**

```python
from crewai import Agent

researcher = Agent(
    role="{topic} Senior Data Researcher",
    goal="Uncover cutting-edge developments in {topic}",
    backstory="You're a seasoned researcher with a knack for uncovering the latest developments...",
    tools=[search_tool, scraping_tool],
    verbose=True,
    allow_delegation=False,
    max_iter=3
)
```

**Agent Properties:**
- `role`: Agent's function/position
- `goal`: What the agent aims to achieve  
- `backstory`: Context and personality
- `tools`: Available capabilities
- `verbose`: Detailed output logging
- `allow_delegation`: Can delegate to other agents
- `max_iter`: Maximum thinking iterations

### 2. Tasks  
**Specific assignments with clear objectives**

```python
from crewai import Task

research_task = Task(
    description="Find and summarize the latest AI news",
    expected_output="A bullet list summary of the top 5 most important AI news",
    agent=researcher,
    tools=[search_tool],
    async_execution=False,
    output_file="research_output.md"
)
```

**Task Properties:**
- `description`: What needs to be done
- `expected_output`: Format and content expectations
- `agent`: Responsible agent
- `tools`: Task-specific tools
- `context`: Output from previous tasks
- `async_execution`: Run in parallel
- `output_file`: Save results to file

### 3. Crews
**Orchestrates agents and tasks working together**

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # or Process.hierarchical
    verbose=2,
    memory=True,
    cache=True,
    max_rpm=100
)

result = crew.kickoff()
```

**Crew Properties:**
- `agents`: List of participating agents
- `tasks`: List of tasks to execute
- `process`: Sequential or hierarchical execution
- `verbose`: Logging level (0-2)
- `memory`: Remember past executions
- `cache`: Cache results for efficiency
- `max_rpm`: Rate limit for API calls

### 4. Tools
**Capabilities that agents can use**

```python
from crewai_tools import SerperDevTool, WebsiteSearchTool, FileReadTool

# Built-in tools
search_tool = SerperDevTool()
website_tool = WebsiteSearchTool()
file_tool = FileReadTool()

# Custom tool
from crewai.tools import BaseTool

class SentimentAnalysisTool(BaseTool):
    name: str = "Sentiment Analysis"
    description: str = "Analyze sentiment of customer feedback text"
    
    def _run(self, text: str) -> str:
        # Your sentiment analysis logic
        return "positive|negative|neutral"
```

## 🎯 Restaurant AI Agent System Design

### Agent Roles for Our System

```python
# 1. Customer Feedback Analyst
feedback_analyst = Agent(
    role="Customer Feedback Analyst", 
    goal="Analyze customer feedback sentiment and extract key insights",
    backstory="Expert in understanding customer emotions and satisfaction levels in Arabic and English",
    tools=[sentiment_analysis_tool, text_processor_tool]
)

# 2. WhatsApp Communication Manager  
whatsapp_manager = Agent(
    role="WhatsApp Communication Manager",
    goal="Handle customer communications via WhatsApp Business API",
    backstory="Specialist in customer outreach and message delivery tracking",
    tools=[whatsapp_api_tool, message_template_tool]
)

# 3. Review Routing Specialist
review_router = Agent(
    role="Review Routing Specialist",
    goal="Route feedback to appropriate channels based on sentiment",
    backstory="Expert in directing positive reviews to Google Maps and negative ones to management",
    tools=[google_maps_tool, notification_tool]
)

# 4. Customer Data Manager
data_manager = Agent(
    role="Customer Data Manager", 
    goal="Manage customer information and visit tracking",
    backstory="Database specialist ensuring accurate customer records and preventing duplicates",
    tools=[database_tool, validation_tool]
)

# 5. AI Assistant Chat Handler
chat_handler = Agent(
    role="AI Assistant Chat Handler",
    goal="Provide intelligent responses to restaurant manager queries", 
    backstory="Conversational AI expert helping with dashboard interactions and insights",
    tools=[query_tool, analytics_tool, openrouter_tool]
)
```

### Task Workflow Design

```python
# Task 1: Customer Detection and Outreach
customer_outreach_task = Task(
    description="Monitor new customers and initiate WhatsApp communication",
    expected_output="List of customers contacted with delivery status",
    agent=whatsapp_manager,
    tools=[database_tool, whatsapp_api_tool]
)

# Task 2: Feedback Analysis  
feedback_analysis_task = Task(
    description="Analyze received customer feedback for sentiment and themes",
    expected_output="Sentiment classification and key insights per customer",
    agent=feedback_analyst,
    context=[customer_outreach_task],
    tools=[sentiment_analysis_tool, openrouter_tool]
)

# Task 3: Intelligent Routing
feedback_routing_task = Task(
    description="Route feedback based on sentiment analysis results",
    expected_output="Routing decisions with appropriate actions taken",
    agent=review_router,
    context=[feedback_analysis_task],
    tools=[google_maps_tool, notification_tool]
)

# Task 4: Dashboard Interactions
dashboard_chat_task = Task(
    description="Handle natural language queries from restaurant managers",
    expected_output="Relevant responses and insights based on queries",
    agent=chat_handler,
    async_execution=True,
    tools=[analytics_tool, database_tool, openrouter_tool]
)
```

### Crew Configuration

```python
restaurant_crew = Crew(
    agents=[
        feedback_analyst,
        whatsapp_manager, 
        review_router,
        data_manager,
        chat_handler
    ],
    tasks=[
        customer_outreach_task,
        feedback_analysis_task,
        feedback_routing_task,
        dashboard_chat_task
    ],
    process=Process.sequential,
    verbose=2,
    memory=True,  # Remember past customer interactions
    cache=True,   # Cache sentiment analysis results
    max_rpm=100   # Respect API rate limits
)
```

## 🛠️ Advanced Features

### Memory System
```python
crew = Crew(
    agents=agents,
    tasks=tasks,
    memory=True,
    memory_config={
        'provider': 'redis',  # or 'local'
        'ttl': 3600  # 1 hour cache
    }
)
```

### Error Handling
```python
from crewai.tools import BaseTool

class RobustSentimentTool(BaseTool):
    name: str = "Robust Sentiment Analysis"
    
    def _run(self, text: str) -> str:
        try:
            # Primary analysis
            result = primary_sentiment_analysis(text)
        except Exception as e:
            self.logger.error(f"Primary analysis failed: {e}")
            # Fallback method
            result = fallback_sentiment_analysis(text)
        
        return result
```

### Callbacks and Monitoring
```python
def task_callback(output):
    print(f"Task completed: {output.description}")
    # Log to monitoring system
    
task = Task(
    description="Analyze feedback",
    agent=analyst,
    callback=task_callback
)
```

## 🔗 Integration Points for Our System

### 1. OpenRouter Integration
```python
class OpenRouterTool(BaseTool):
    name: str = "OpenRouter AI"
    description: str = "Connect to OpenRouter for sentiment analysis and chat responses"
    
    def _run(self, prompt: str, model: str = "anthropic/claude-3.5-haiku") -> str:
        # OpenRouter API call
        return ai_response
```

### 2. WhatsApp Business API Tool
```python
class WhatsAppTool(BaseTool):
    name: str = "WhatsApp Business API"
    description: str = "Send messages and handle webhooks"
    
    def _run(self, phone: str, message: str, template_name: str = None) -> dict:
        # WhatsApp API integration
        return delivery_status
```

### 3. Database Operations Tool
```python
class DatabaseTool(BaseTool):
    name: str = "Database Operations"
    description: str = "Manage customer data and interaction history"
    
    def _run(self, operation: str, data: dict) -> dict:
        # Database CRUD operations
        return result
```

## 📊 Production Considerations

### Scalability
- CrewAI supports enterprise-scale deployments
- Memory management for high-volume processing
- Rate limiting and error recovery built-in

### Monitoring
- Verbose logging at multiple levels
- Task execution tracking
- Performance metrics collection

### Security
- API key management through environment variables
- Agent permission controls
- Secure tool integration patterns

## 🎓 Best Practices

1. **Agent Design**
   - Give agents specific, focused roles
   - Provide detailed backstories for context
   - Limit tools to what each agent actually needs

2. **Task Definition**
   - Be specific about expected outputs
   - Use context to chain tasks effectively
   - Set appropriate async execution for parallel work

3. **Error Handling**
   - Implement robust error handling in custom tools
   - Use fallback strategies for critical operations
   - Monitor and log all agent activities

4. **Performance**
   - Use caching for repeated operations
   - Set appropriate rate limits
   - Optimize tool selection per task

This documentation will be our reference guide throughout the backend development process, ensuring we leverage CrewAI's full capabilities for our restaurant AI assistant system.