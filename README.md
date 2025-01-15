# AI Learning Manager Agent (ALMA)

A personal learning project focused on understanding and developing AI agent systems. The primary goal is to explore and learn about building AI-based software systems, with emphasis on agent architectures and their interactions.

## Project Context

This project serves as a learning platform for:
1. Understanding AI agent system development
2. Experimenting with different architectural approaches
3. Building a foundation for future specialized AI implementations
4. Learning about real-time AI processing and memory management

## Current Status

- Phase 1 (Core Infrastructure): COMPLETED ✓
- Phase 2 (Streaming and Performance): PARTIALLY COMPLETED
  - Basic WebSocket implementation complete ✓
  - Creative task processing working (~30s) ✓
  - Analytical task processing working with streaming ✓
  - Memory management implemented ✓
  - Token-by-token processing implemented ✓
  - Currently optimizing streaming performance

## Recent Updates
- Implemented analytical task streaming
- Enhanced memory management system
- Added token-by-token processing
- Improved WebSocket communication
- Enhanced configuration management

## Quick Start

### Backend Setup
```bash
# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install PyTorch with CUDA support first (critical for other dependencies)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install remaining dependencies
pip install -r requirements.txt
```

### Important Notes on Dependencies
- PyTorch must be installed first with CUDA support
- The order of installation matters due to interdependencies
- If you encounter any issues:
  1. Ensure your virtual environment is clean (remove and recreate if necessary)
  2. Upgrade pip to the latest version
  3. Install PyTorch with CUDA support before other packages
  4. Install remaining requirements

### Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

### System Requirements
- NVIDIA GPU with CUDA support
- Python 3.10 or higher
- Node.js 18.17 or higher
- npm 9.6.7 or higher

## Project Structure

```
alma/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── manager_agent.py      # Core agent with memory mgmt ✓
│   │   └── prompt_system.py      # Prompt engineering system ✓
│   ├── models/
│   │   └── __init__.py
│   ├── main.py                   # FastAPI backend with WebSocket ✓
│   ├── requirements.txt          # Updated dependencies ✓
│   └── tests/                    # Test files ✓
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js 14 structure ✓
│   │   ├── components/
│   │   │   ├── ui/              # shadcn components ✓
│   │   │   └── CoreAgent.tsx    # Main agent interface ✓
│   │   └── hooks/
│   │       └── useWebSocket.ts   # WebSocket management ✓
│   └── package.json             # Dependencies ✓
```

## System Overview

ALMA is a learning project built on:
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU (CUDA enabled)
- RAM: 32GB - Sufficient for concurrent agent operations
- CPU: Intel Core Ultra 7 155H
- System: 64-bit Windows, VSCode/Cursor with Git Bash

## Project Evolution

### Initial Phase (Core Infrastructure)
- Basic setup and environment ✓
- Manager Agent implementation ✓
- WebSocket foundation ✓
- Frontend basics ✓

### GUI Integration Phase
- [x] Frontend Development
  - [x] Next.js 14 structure
  - [x] shadcn/ui components
  - [x] Task type selection
  - [x] Loading states
  - [x] Error handling
  - [x] WebSocket hook
  - [x] Working creative task UI
  - [x] Performance monitoring UI

- [x] Backend API
  - [x] FastAPI endpoints
  - [x] WebSocket support
  - [x] Error handling
  - [x] Environment configuration
  - [x] Response streaming
  - [x] Performance metrics

- [x] Initial WebSocket Features
  - [x] Basic implementation
  - [x] Reconnection logic
  - [x] Error handling
  - [x] Connection monitoring
  - [x] Message streaming

### Performance Enhancement Phase [COMPLETED]
- [x] Memory Management
  - [x] CUDA memory tracking
  - [x] Memory cleanup protocols
  - [x] Resource optimization
  - [x] Memory usage analytics

- [x] Response Optimization
  - [x] Basic token management
  - [x] Initial streaming implementation
  - [x] Basic caching strategy
  - [x] Token-by-token processing

- [x] Monitoring System
  - [x] Basic performance metrics
  - [x] Resource utilization tracking
  - [x] Error tracking system
  - [x] Usage analytics
  - [x] Health monitoring

### Current Focus: Streaming Optimization
Enhancing the streaming-first architecture with:
- Performance optimization for token processing
- Enhanced memory patterns
- Improved real-time processing
- Preparation for vector DB integration

## Development Roadmap

### Phase 1: Core Infrastructure [COMPLETED] ✓
- [x] Python environment and dependencies
- [x] CUDA toolkit and GPU acceleration
- [x] Mistral 7B integration
- [x] Development environment tools
- [x] Environment variable configuration
- [x] Basic project structure
- [x] Manager Agent implementation
- [x] Prompt engineering system
- [x] Task handling mechanisms
- [x] Error handling system
- [x] CUDA memory management
- [x] FastAPI endpoints
- [x] Basic WebSocket implementation
- [x] Frontend foundation with Next.js 14
- [x] Initial UI components with shadcn/ui

### Phase 2: Streaming and Performance [CURRENT PHASE]
#### Streaming Implementation [IN PROGRESS]
- [ ] Analytical task streaming
  - [ ] Token-by-token implementation
  - [ ] Memory management per token
  - [ ] Error handling
  - [ ] Design for vector DB integration
- [x] WebSocket Features
  - [x] Reconnection logic
  - [x] Error handling
  - [x] Connection health monitoring
  - [x] Basic message streaming
  - [ ] Enhanced message streaming
  - [ ] Message queueing

#### Performance Optimization
- [x] Initial Memory Management
  - [x] CUDA memory tracking
  - [x] Basic cleanup protocols
  - [x] Resource optimization
  - [x] Usage analytics
- [ ] Enhanced Memory Features
  - [ ] Token management
  - [ ] Memory usage optimization
  - [ ] Response caching
  - [ ] Automated scaling

#### Frontend Enhancements
- [x] Completed Features
  - [x] Task type selection
  - [x] Loading states
  - [x] Basic error handling
  - [x] WebSocket hook implementation
  - [x] Working creative task UI
- [ ] Upcoming Features
  - [ ] Real-time updates
  - [ ] Streaming display
  - [ ] Enhanced error handling
  - [ ] Performance metrics display

### Phase 3: Vector Database Integration [UPCOMING]
- [ ] Vector DB selection and setup
  - [ ] Research and evaluate options
  - [ ] Integration planning
  - [ ] Initial setup
- [ ] Embedding Generation System
  - [ ] Text processing pipeline
  - [ ] Embedding generation
  - [ ] Chunking strategy
- [ ] Memory Management Integration
  - [ ] Vector storage connection
  - [ ] Similarity search
  - [ ] Memory persistence
- [ ] Learning Components
  - [ ] Feedback mechanisms
  - [ ] Pattern recognition
  - [ ] Knowledge refinement
- [ ] Experimental Features
  - [ ] Context awareness
  - [ ] Dynamic updates
  - [ ] Memory optimization

### Phase 4: Advanced Agent Architecture [FUTURE]
- [ ] Multi-agent System Implementation
  - [ ] Agent specialization
  - [ ] Role definition
  - [ ] Memory patterns
- [ ] Agent Coordination
  - [ ] Communication protocols
  - [ ] Task delegation
  - [ ] Shared memory access
- [ ] Learning and Adaptation
  - [ ] Performance-based evolution
  - [ ] Dynamic prompt engineering
  - [ ] Interaction pattern learning
- [ ] Complex Task Handling
  - [ ] Task decomposition
  - [ ] Parallel processing
  - [ ] Result synthesis
- [ ] System Optimization
  - [ ] Resource allocation
  - [ ] Load balancing
  - [ ] Memory optimization

## Current Performance Metrics
- Creative tasks: ~30 seconds response time
- Analytical tasks: In development
- Target: Sub-60 second analytical responses

## Development Guidelines
1. Code Quality
   - Comprehensive error handling
   - Memory management best practices
   - Type safety (TypeScript/Python)
   - Documentation standards

2. Testing Strategy
   - Unit tests for core components
   - Integration tests for API
   - End-to-end testing
   - Performance benchmarking

3. Monitoring
   - Resource utilization
   - Error rates and types
   - Response times
   - Memory usage

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - feel free to use this project for learning and development purposes.