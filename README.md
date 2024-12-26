# AI Learning Manager Agent (ALMA)

A hierarchical AI agent system for learning and development, starting with a core Manager Agent and gradually expanding to a multi-agent system.

## Current Status

- Phase 1 (Core Infrastructure): COMPLETED ✓
- Phase 2 (GUI Integration): IN PROGRESS
- Next: Integration testing and performance optimization

## Quick Start

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
npm run dev
```

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

ALMA is built on verified hardware specifications:
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU (CUDA enabled)
- RAM: 32GB - Sufficient for concurrent agent operations
- CPU: Intel Core Ultra 7 155H - Strong processing capabilities
- System: 64-bit Windows, VSCode/Cursor with Git Bash

## Complete Development Roadmap

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

### Phase 2: GUI Integration [CURRENT PHASE]
#### Frontend Development
- [x] Next.js 14 structure
- [x] shadcn/ui components
- [x] Task type selection
- [x] Loading states
- [x] Error handling
- [x] WebSocket hook implementation
- [ ] Integration testing
- [ ] Performance monitoring UI

#### Backend API
- [x] FastAPI endpoints
- [x] WebSocket support
- [x] Error handling
- [x] Environment configuration
- [ ] Response streaming
- [ ] Request caching
- [ ] Load testing

#### WebSocket Features
- [x] Basic WebSocket implementation
- [x] Reconnection logic
- [x] Error handling
- [ ] Message queueing
- [ ] Connection health monitoring
- [ ] Multi-room support

### Phase 3: Performance Optimization [PENDING]
#### Memory Management
- [x] CUDA memory tracking
- [x] Memory cleanup protocols
- [x] Resource optimization
- [ ] Memory usage analytics
- [ ] Automated scaling
- [ ] Memory prediction

#### Response Optimization
- [ ] Token management
- [ ] Streaming improvements
- [ ] Caching strategy
- [ ] Request batching
- [ ] Response compression

#### Monitoring System
- [ ] Performance metrics
- [ ] Resource utilization
- [ ] Error tracking
- [ ] Usage analytics
- [ ] Health monitoring

### Phase 4: Memory System [PLANNED]
#### Vector Database
- [ ] Database selection
- [ ] Infrastructure setup
- [ ] Embedding pipeline
- [ ] Retrieval system
- [ ] Integration testing

#### Context Management
- [ ] Sliding context window
- [ ] Priority system
- [ ] Memory pruning
- [ ] Threading support

### Phase 5: Multi-Agent System [FUTURE]
#### CrewAI Integration
- [ ] Framework setup
- [ ] Architecture design
- [ ] Communication protocols
- [ ] Role definitions

#### Agent Implementation
- [ ] Research Agent
- [ ] Logger Agent
- [ ] Synthesizer Agent
- [ ] Inter-agent communication

## Current Performance Metrics
- Creative tasks: ~30 seconds response time
- Analytical tasks: ~600 seconds with token overflow issues
- Memory optimization and error handling systems in place

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