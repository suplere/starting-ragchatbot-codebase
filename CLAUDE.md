# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Environment Setup
```bash
# Install dependencies
uv sync

# Required environment variable in .env
ANTHROPIC_API_KEY=your_api_key_here
```

### Development URLs
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Architecture Overview

This is a **RAG (Retrieval-Augmented Generation) system** for course materials with a clean separation between frontend, backend, and RAG processing.

### Core Architecture Pattern

The system follows a **tool-based RAG pattern** where the AI uses function calling to search course materials:

```
User Query → FastAPI → RAG System → AI Generator (Claude) → Search Tools → Vector Store → Response
```

### Key Components

**RAG System (`rag_system.py`)**
- Main orchestrator that coordinates all components
- Handles session management and conversation history
- Integrates AI generation with vector search through tools

**AI Generator (`ai_generator.py`)**
- Anthropic Claude integration with tool calling
- Uses function calling paradigm for course searches
- Single search per query limitation to maintain focus

**Search Tools (`search_tools.py`)**
- Tool abstraction layer following Anthropic's function calling spec
- `CourseSearchTool` provides semantic search with course/lesson filtering
- Tool definitions are dynamically registered with the AI

**Vector Store (`vector_store.py`)**
- ChromaDB integration for semantic search
- Stores both course metadata and chunked content
- Handles course deduplication and content indexing

**Session Manager (`session_manager.py`)**
- Manages conversation contexts with configurable history limits
- Automatic session creation on first query
- History-aware responses for follow-up questions

### Data Flow Patterns

**Document Processing**
- Course documents → Text chunking → Embeddings → ChromaDB storage
- Metadata extraction for course/lesson structure
- Deduplication by course title

**Query Processing**
- Session-aware context building
- AI decides when to search vs. use general knowledge
- Tool execution with result synthesis
- Response with source attribution

**Frontend Integration**
- Session ID management for conversation continuity
- Real-time loading states with message streaming
- Course analytics dashboard

### Configuration

All settings centralized in `config.py`:
- Chunk size: 800 characters with 100 character overlap
- Max search results: 5 per query
- Conversation history: 2 exchanges (4 messages)
- Embedding model: all-MiniLM-L6-v2

### Course Data Structure

Documents are processed into structured objects:
- `Course`: Title, instructor, lessons list
- `Lesson`: Number, title, optional link
- `CourseChunk`: Content, metadata, indexing info

Course titles serve as unique identifiers for deduplication and organization.