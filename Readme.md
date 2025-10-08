# MCP Agent Project Documentation

## 1. Project Overview

This project implements an MCP (Model Context Protocol) Agent designed to interact with various specialized backend servers. The agent leverages large language models (LLMs) to understand natural language queries and route them to the appropriate tools provided by these servers. This allows for a flexible and extensible system capable of performing diverse tasks such as mathematical calculations, file system operations, database interactions, and more.

The primary goal of this project is to demonstrate the power of integrating LLMs with external tools and services, enabling intelligent automation and enhanced user interaction through a conversational interface. The Streamlit application provides a user-friendly frontend for interacting with the agent.


## 2. Technology Stack

This project utilizes a robust and modern technology stack to achieve its goals. Below are the key technologies employed:

*   **Python**: The primary programming language for the entire project, chosen for its versatility, extensive libraries, and strong community support.
*   **Streamlit**: Used for building the interactive web-based user interface (UI). Streamlit's simplicity and rapid development capabilities make it ideal for creating data applications and dashboards with minimal code.
*   **LangChain**: A framework for developing applications powered by language models. It provides tools and abstractions for chaining together different components (LLMs, tools, agents, memory) to create complex LLM-driven applications.
*   **MCP (Model Context Protocol)**: A custom framework that enables the agent to interact with various specialized backend servers (e.g., math, files, postgres). It facilitates the creation and integration of custom tools that the LLM agent can utilize. This platform is designed to be extensible, allowing for easy addition of new server functionalities and tools.
*   **OpenWeatherMap API**: Used by the `weather_server.py` to fetch current weather data.
*   **PostgreSQL**: A powerful, open-source relational database system used for storing and managing structured data. It provides reliability, data integrity, and advanced features necessary for complex data operations.
*   **Groq**: An inference engine that provides fast and efficient execution of large language models. It is used here to power the LLM agent, enabling quick responses and efficient processing of natural language queries.


## 3. Project Structure

The project is organized into the following key directories and files:

*   `main.py`: The main entry point for the backend logic and testing of the MCP agent. It initializes the servers, loads tools, creates the agent, and demonstrates various interactions.
*   `app.py`: The Streamlit application that provides the graphical user interface (GUI) for interacting with the MCP agent. It handles chat interactions, document summarization, and displays agent responses.
*   `agent.py`: Contains the core logic for the MCP agent, including how it processes natural language queries, selects tools, and executes actions.
*   `llm.py`: Defines the configuration and integration with the Large Language Model (LLM) used by the agent, specifically Groq.
*   `memory.py`: Manages the conversational memory of the agent, allowing it to maintain context across multiple turns of interaction.
*   `requirements.txt`: Lists all the Python dependencies required for the project.
*   `servers/`: This directory contains the implementations of various backend servers that provide tools to the MCP agent:
    *   `csv_server.py`: Provides tools for interacting with CSV files.
    *   `files_server.py`: Provides tools for file system operations (e.g., listing, reading, writing, deleting, renaming files).
    *   `math_server.py`: Offers tools for performing mathematical calculations.
    *   `postgres_server.py`: Enables interaction with a PostgreSQL database.
    *   `prompt_server.py`: Manages and serves various prompts used by the agent.
    *   `weather_server.py`: Provides tools for fetching current weather information.
    *   `xml_server.py`: Provides tools for interacting with XML files.
*   `tmp/`: A temporary directory used for file manipulation operations by the `files_server.py`.


## 4. Setup Instructions

To get the MCP Agent project up and running, follow these steps:

1.  **Clone the Repository (if applicable)**:

    ```bash
    git clone <repository_url>
    cd mcp-agent-project
    ```

2.  **Create a Virtual Environment**:

    It's highly recommended to use a virtual environment to manage project dependencies.

    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment**:

    *   **On Windows**:

        ```bash
        .venv\Scripts\activate
        ```

    *   **On macOS/Linux**:

        ```bash
        source .venv/bin/activate
        ```

4.  **Install Dependencies**:

    Install all required Python packages using pip:

    ```bash
    pip install -r requirements.txt
    ```

5.  **Environment Variables**: (If applicable)

    Create a `.env` file in the root directory of the project and add any necessary environment variables, such as API keys for LLMs, weather, or database connection strings. Refer to `.env.example` (if provided) for required variables.

    ```
    # Example .env content
    GROQ_API_KEY="your_groq_api_key"
    WEATHER_API_KEY="your_openweathermap_api_key"
    DATABASE_URL="postgresql://user:password@host:port/database"
    ```

6.  **PostgreSQL Setup**:

    Ensure you have a PostgreSQL server running and accessible. Update the `DATABASE_URL` in your `.env` file with the correct connection details.

7.  **Run the Streamlit Application**:

    Once all dependencies are installed and environment variables are set, you can launch the Streamlit application:

    ```bash
    streamlit run app.py
    ```

    This will open the application in your web browser.


## 5. Usage Guide

Once the Streamlit application is running, you can interact with the MCP Agent through the chat interface. Here's how to use it:

1.  **Access the Application**: Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

2.  **Chat with the Agent**: Type your queries or commands into the chat input box and press Enter. The agent will process your request using its available tools.

    *   **Mathematical Operations**: Ask the agent to perform calculations. For example: "What is 123 + 456?" or "Calculate the square root of 64."
    *   **File System Operations**: Instruct the agent to interact with files in the `tmp/` directory. For example:
        *   "List all files in the `tmp/` directory."
        *   "Read the content of `tmp/my_document.txt`."
        *   "Create a file named `tmp/new_file.txt` with the content 'Hello, MCP!'."
        *   "Delete the file `tmp/old_file.txt`."
    *   **Database Interactions**: If the PostgreSQL server is configured, you can ask the agent to query or manipulate data. For example: "Show me the first 5 entries from the 'users' table."
    *   **Document Summarization**: Provide text or a document for the agent to summarize.

3.  **Review Responses**: The agent's responses, including the results of tool executions, will be displayed in the chat interface.

4.  **Chat History**: The application maintains chat history, allowing you to review past interactions.


## 6. Troubleshooting

Here are some common issues you might encounter and how to resolve them:

*   **"Failed to load resources from files: unhandled errors in a TaskGroup (1 sub-exception)" or "Could not load tools from MCP client: unhandled errors in a TaskGroup (1 sub-exception)"**: These errors often indicate that one or more of the backend servers (e.g., `files_server.py`, `postgres_server.py`, `weather_server.py`) failed to initialize correctly or maintain a connection. 
    *   **Check Server Logs**: Examine the terminal where `streamlit_app.py` is running for more detailed error messages from the `try-except` blocks in the server files. This will provide specific clues about which server is failing and why.
    *   **Verify Dependencies**: Ensure all dependencies are correctly installed by running `pip install -r requirements.txt`.
    *   **Environment Variables**: Double-check that all necessary environment variables (e.g., `GROQ_API_KEY`, `DATABASE_URL`, `WEATHER_API_KEY`) are set correctly in your `.env` file.
    *   **PostgreSQL Status**: If `postgres_server.py` is failing, ensure your PostgreSQL server is running and accessible, and that the connection details in `DATABASE_URL` are accurate.
    *   **Port Conflicts**: Ensure that no other applications are using the same ports that the MCP servers are trying to bind to.

*   **Streamlit Application Not Loading**: If the Streamlit application doesn't load or shows a blank page:
    *   **Check Terminal Output**: Look for any error messages in the terminal where you ran `streamlit run streamlit_app.py`.
    *   **Port Availability**: Ensure that port 8501 (or the port Streamlit is trying to use) is not blocked by a firewall or another application.

*   **Agent Not Responding or Incorrect Responses**: 
    *   **LLM API Key**: Verify that your `GROQ_API_KEY` is correct and has not expired.
    *   **Server Connectivity**: Confirm that all backend servers are running and accessible by the `MultiServerMCPClient`.
    *   **Prompt Engineering**: If the agent is consistently giving incorrect responses, you might need to refine the prompts used in `prompt_server.py` or the agent's internal logic.

If you encounter an issue not listed here, please refer to the specific server logs for more detailed error messages or consult the project maintainers.