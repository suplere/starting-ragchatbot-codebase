# User Interaction Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (script.js)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                              ┌─────────┴─────────┐
                              │   User Input      │
                              │  (chatInput)      │
                              └─────────┬─────────┘
                                       │
                              ┌─────────▼─────────┐
                              │   sendMessage()   │
                              │                   │
                              │ • Get query text  │
                              │ • Add user msg    │
                              │ • Show loading    │
                              └─────────┬─────────┘
                                       │
                                       │ POST /api/query
                                       │ {query, session_id}
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (app.py)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                              ┌─────────▼─────────┐
                              │ query_documents() │
                              │                   │
                              │ if !session_id:   │
                              │   create_session()│
                              └─────────┬─────────┘
                                       │
                                       │ rag_system.query()
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG SYSTEM (rag_system.py)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌─────────────────────▼─────────────────────┐
                    │                query()                    │
                    │                                          │
                    │  1. Get conversation history             │
                    │     session_manager.get_conversation()   │
                    │                                          │
                    │  2. Generate AI response with tools      │
                    │     ai_generator.generate_response()     │
                    │                                          │
                    │  3. Save exchange to history             │
                    │     session_manager.add_exchange()       │
                    └─────────────────────┬─────────────────────┘
                                        │
          ┌─────────────────────────────────────────────────────────┐
          │                                                         │
          ▼                                                         ▼
┌──────────────────┐                                    ┌──────────────────┐
│  SESSION MGR     │                                    │   AI GENERATOR   │
│ (session_mgr.py) │                                    │ (ai_generator.py)│
│                  │                                    │                  │
│ • create_session │                                    │ • Claude API     │
│ • add_exchange   │                                    │ • Tool calling   │
│ • get_history    │                                    │ • Vector search  │
└──────────────────┘                                    └──────────────────┘
          │                                                         │
          │                                              ┌─────────▼─────────┐
          │                                              │   VECTOR STORE    │
          │                                              │ (vector_store.py) │
          │                                              │                   │
          │                                              │ • ChromaDB        │
          │                                              │ • Embeddings      │
          │                                              │ • Course chunks   │
          │                                              └───────────────────┘
          │
          │ Response: {answer, sources, session_id}
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (script.js)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                              ┌─────────▼─────────┐
                              │  Response Handler │
                              │                   │
                              │ • Update session  │
                              │ • Remove loading  │
                              │ • Add AI message  │
                              │ • Show sources    │
                              └───────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              SESSION FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

First Query:
sessionId = null → Backend creates session_1 → Frontend stores session_1

Subsequent Queries:
sessionId = session_1 → Backend uses existing session → History context

Session History (max 5 exchanges = 10 messages):
[
  {role: "user", content: "What is..."},
  {role: "assistant", content: "Based on..."},
  ...
]
```