# AI Learning Manager Agent (ALMA)

A hierarchical AI agent system for learning and development, starting with a core Manager Agent and gradually expanding to a multi-agent system.

## Current Status

- Phase 1 (Core Infrastructure): COMPLETED ✓
- Phase 2 (GUI Integration): IN PROGRESS
  - Frontend and WebSocket implementation complete ✓
  - Creative task processing tested and working ✓
  - Performance monitoring implemented ✓
  - Token tracking and analytics complete ✓
  - Memory management and model unloading implemented ✓
- Next: Response truncation fix and request caching

## Recent Updates
- Added model unloading capability to manage GPU memory
- Implemented memory usage tracking and visualization
- Enhanced token tracking system
- Improved performance monitoring with real-time metrics
- Added memory cleanup protocols

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
- [x] shadcn/ui components implementation
- [x] Task type selection
- [x] Loading states
- [x] Error handling
- [x] WebSocket hook implementation
- [x] Working creative task UI
- [x] Analytical task optimization
- [x] Performance monitoring UI
- [ ] Integration testing

#### Backend API
- [x] FastAPI endpoints
- [x] WebSocket support
- [x] Error handling
- [x] Environment configuration
- [x] Response streaming
- [x] Performance metrics tracking
- [ ] Request caching
- [ ] Load testing

#### WebSocket Features
- [x] Basic WebSocket implementation
- [x] Reconnection logic
- [x] Error handling
- [x] Connection health monitoring
- [x] Message streaming
- [ ] Message queueing
- [ ] Multi-room support

### Phase 3: Performance Optimization [PENDING]
#### Memory Management
- [x] CUDA memory tracking
- [x] Memory cleanup protocols
- [x] Resource optimization
- [x] Memory usage analytics
- [ ] Enhanced memory analytics
- [ ] Automated scaling
- [ ] Memory prediction

#### Response Optimization
- [x] Token management
- [x] Streaming improvements
- [ ] Caching strategy
- [ ] Request batching
- [ ] Response compression

#### Monitoring System
- [x] Basic performance metrics
- [x] Enhanced resource utilization tracking
- [x] Error tracking system
- [x] Usage analytics
- [x] Health monitoring dashboard

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
- Analytical tasks: ~60 seconds with streaming support
- Memory optimization and error handling systems in place
- Real-time performance monitoring implemented
- Token usage tracking and analytics operational

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