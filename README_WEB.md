# AI Research Processor - Web Application

A modern web-based interface for the AI Research Processor, featuring real-time hypothesis generation, multi-user support with ephemeral sessions, and a professional React/Next.js frontend.

## 🏗️ Architecture

### Technology Stack

**Frontend:**
- Next.js 14 (React framework with App Router)
- TypeScript for type safety
- TailwindCSS for styling
- shadcn/ui for UI components
- WebSocket for real-time updates

**Backend:**
- FastAPI (Python) for REST API
- WebSocket support for live progress
- Session management with ephemeral storage
- Integration with existing RAG system

**Infrastructure:**
- Docker & Docker Compose
- Nginx reverse proxy (production)
- M3 machine for web server + vLLM
- Mystery machine for ChromaDB

## 🚀 Quick Start (Development)

### Prerequisites

- Docker and Docker Compose
- Access to M3 and Mystery machines
- ChromaDB running on Mystery
- vLLM/Ollama running on M3 (optional, can use Gemini)

### 1. Clone and Setup

```bash
cd AI-Research-Processor
```

### 2. Configure Environment

Copy environment template:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` with your actual values:
- `CHROMA_HOST`: IP address of Mystery machine
- `GEMINI_API_KEY`/`GOOGLE_API_KEY`: If using Gemini
- `SECRET_KEY`: Generate with `openssl rand -hex 32`

### 3. Start Services

```bash
# Development mode (simpler, no Nginx)
docker-compose up -d

# OR Production mode (with Nginx)
chmod +x scripts/start_web.sh
./scripts/start_web.sh
```

### 4. Access Application

Open your browser to:
- **Frontend**: http://localhost:3000 (dev) or http://localhost (prod)
- **API Docs**: http://localhost:8000/docs (dev) or http://localhost/api/docs (prod)

## 📁 Project Structure

```
AI-Research-Processor/
├── backend/                    # FastAPI backend
│   ├── api/                    # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── hypothesis.py      # Hypothesis generation
│   │   ├── database.py        # Database status
│   │   └── export_api.py      # Export functionality
│   ├── services/              # Business logic
│   │   ├── session_service.py # Session management
│   │   ├── hypothesis_service.py # Hypothesis operations
│   │   ├── cleanup_service.py # Background cleanup
│   │   ├── database_service.py # ChromaDB operations
│   │   └── export_service.py  # File export
│   ├── adapters/              # Integration adapters
│   │   └── rag_adapter.py     # RAG system adapter
│   ├── models/                # Pydantic models
│   ├── main.py                # FastAPI application
│   ├── config.py              # Configuration
│   └── Dockerfile
│
├── frontend/                   # Next.js frontend
│   ├── app/                    # App router pages
│   │   ├── (auth)/            # Authentication pages
│   │   │   └── login/
│   │   ├── (dashboard)/       # Protected pages
│   │   │   └── dashboard/
│   │   │       ├── page.tsx           # Main dashboard
│   │   │       ├── generate/page.tsx  # Generation interface
│   │   │       └── results/page.tsx   # Results viewer
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   └── ui/                # shadcn/ui components
│   ├── lib/                   # Utilities
│   │   ├── api.ts             # API client
│   │   ├── websocket.ts       # WebSocket manager
│   │   ├── types.ts           # TypeScript types
│   │   └── utils.ts           # Helper functions
│   ├── hooks/                 # Custom React hooks
│   │   ├── useSession.ts
│   │   ├── useWebSocket.ts
│   │   └── useHypothesis.ts
│   └── Dockerfile
│
├── nginx/                      # Nginx configuration
│   └── nginx.conf
├── scripts/                    # Utility scripts
│   ├── start_web.sh
│   └── stop_web.sh
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
└── README_WEB.md              # This file
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env` or `.env.production`:

```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=<generate-with-openssl>
SESSION_TIMEOUT_HOURS=2

# ChromaDB (Mystery)
EXECUTION_MODE=distributed
CHROMA_HOST=192.168.1.XXX
CHROMA_PORT=8000

# LLM (M3 vLLM or Gemini)
LLM_PROVIDER=local  # or 'gemini'
LLM_API_BASE=http://host.docker.internal:11434/v1
LLM_MODEL_NAME=llama3

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=10
MAX_CONCURRENT_GENERATIONS=3
```

### Frontend Configuration

Frontend environment variables are set at build time:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🎯 Features

### User Session Management
- **Ephemeral Sessions**: All user data is temporary
- **Auto-cleanup**: Sessions expire after 2 hours (configurable)
- **Session Tracking**: SQLite database logs IP, timestamps, actions
- **Isolated Storage**: Each session gets separate temp directory

### Hypothesis Generation
- **Real-time Progress**: WebSocket updates during generation
- **Configurable Output**: 1-50 hypotheses per request
- **AI-Powered**: Integrated with existing RAG system
- **Rich Metadata**: Scores, citations, key concepts

### Export Functionality
- **Multiple Formats**: JSON, Excel, CSV, PDF
- **Customizable**: Include/exclude citations and scores
- **Temporary Storage**: Files cleaned up with session

### Database Integration
- **ChromaDB Status**: Real-time connectivity and statistics
- **Source Breakdown**: Documents by source (PubMed, etc.)
- **Collection Info**: Available collections and counts

## 🔒 Security

### Session Security
- JWT tokens in HTTP-only cookies
- Server-side session validation
- Automatic session expiry
- Rate limiting per session

### Data Privacy
- No persistent user data storage
- Automatic cleanup on logout/expiry
- Isolated session directories
- Audit logs only (IP, timestamp, actions)

### Network Security
- CORS protection
- HTTPS support (production)
- WebSocket authentication
- Nginx rate limiting

## 🚢 Deployment

### Development Deployment

```bash
docker-compose up -d
```

Access at http://localhost:3000

### Production Deployment (M3)

1. **Configure environment:**
   ```bash
   cp .env.production.example .env.production
   # Edit with actual values
   ```

2. **Start services:**
   ```bash
   chmod +x scripts/start_web.sh
   ./scripts/start_web.sh
   ```

3. **Configure SSL (optional but recommended):**
   - Place SSL certificates in `nginx/ssl/`
   - Uncomment HTTPS server block in `nginx/nginx.conf`
   - Update environment variables with https:// URLs

4. **Monitor logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

### System Requirements (M3)

- **CPU**: 8+ cores recommended
- **RAM**: 16GB+ (32GB+ for large models)
- **Storage**: 100GB+ free space
- **Network**: Access to Mystery machine for ChromaDB
- **Ports**: 80, 443, 3000, 8000 available

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Check Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Session Logs

SQLite database at `logs/sessions.db`:

```bash
sqlite3 logs/sessions.db "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10;"
```

## 🐛 Troubleshooting

### Cannot connect to ChromaDB

```bash
# Test connection
curl http://MYSTERY_IP:8000/api/v1/heartbeat

# Check environment variable
echo $CHROMA_HOST

# Verify network access
ping MYSTERY_IP
```

### vLLM not accessible

```bash
# Test vLLM
curl http://localhost:11434/v1/models

# Check if Ollama is running
systemctl status ollama  # or your vLLM service
```

### Frontend can't reach backend

```bash
# Check backend health
curl http://localhost:8000/health

# Check Docker networks
docker network ls
docker network inspect ai-research-processor_app-network
```

### WebSocket connection fails

- Ensure Nginx WebSocket configuration is correct
- Check CORS settings in backend
- Verify `NEXT_PUBLIC_WS_URL` is set correctly

## 🔄 Updates and Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Backup Session Logs

```bash
# Backup sessions database
cp logs/sessions.db logs/sessions_backup_$(date +%Y%m%d).db
```

### Clean Up Old Sessions

Sessions are automatically cleaned up by the cleanup service. Manual cleanup:

```bash
# Remove all expired sessions
docker-compose -f docker-compose.prod.yml exec backend python -c "
from backend.services.session_service import SessionService
import asyncio
asyncio.run(SessionService().cleanup_expired_sessions())
"
```

## 📞 Support

For issues or questions:
- **Backend Issues**: Check `logs/` directory
- **Frontend Issues**: Check browser console
- **ChromaDB Issues**: Check Mystery machine logs
- **General**: Review this documentation and existing guides

## 📝 Development

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Adding New Features

1. Backend: Add routes in `backend/api/`, logic in `backend/services/`
2. Frontend: Add pages in `frontend/app/`, components in `frontend/components/`
3. Types: Update `frontend/lib/types.ts` and `backend/models/`
4. Test locally before deploying

## 🎓 Usage Guide

### For Researchers

1. **Login**: Enter username (no password required for demo)
2. **Generate**: Describe your research topic
3. **Monitor**: Watch real-time progress
4. **Review**: Examine generated hypotheses
5. **Export**: Download results in preferred format
6. **Logout**: Data is automatically cleaned up

### Session Workflow

```
Login → Generate Hypotheses → View Results → Export → Logout
  ↓                                ↓
Session Created              Data Saved Temporarily
  ↓                                ↓
2hr Timeout                  Can Re-export Later
  ↓                                ↓
Auto-cleanup                 Deleted on Logout/Expiry
```

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Maintainer**: AI Research Processor Team

