# Tech Context

## Backend Stack
- Python 3.11, Flask, Gunicorn
- Redis (Render managed)
- Web3.py (implemented for Circle Layer)
- Twilio (WhatsApp), Telegram Bot API
- Stripe, Circle (USDC), Circle Layer (CLAYER)
- Amadeus SDK
- FPDF2, Cloudinary
- Pytest

## Frontend Stack (New)
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript for type safety
- **Styling**: TailwindCSS with custom design system
- **State Management**: React Query (@tanstack/react-query)
- **HTTP Client**: Axios
- **UI Components**: Lucide React (icons), custom components
- **Utilities**: clsx (conditional classes), react-hot-toast (notifications)
- **Build Tool**: Vite (via Next.js)

## Development Environment
- **Backend Setup**:
  - Env via .env or Render environment
  - `pip install -r requirements.txt`
  - `gunicorn app.main:app` or `python -m app.main`
- **Frontend Setup**:
  - Node.js 18+ required
  - `cd frontend && npm install`
  - `npm run dev` (localhost:3000)
- **Full Stack Development**:
  - Terminal 1: Backend on localhost:5000
  - Terminal 2: Frontend on localhost:3000
  - CORS enabled for local development

## Integration Requirements
- **CORS Configuration**: Flask-CORS for localhost:3000 and production domain
- **API Endpoints**: New `/api/chat` JSON endpoint alongside existing webhooks
- **Session Management**: Frontend user ID mapping to Redis keys
- **Environment Variables**:
  - Backend: Existing .env variables
  - Frontend: `NEXT_PUBLIC_API_BASE_URL` for API calls

## Deployment Architecture
- **Backend**: Render web service (existing)
- **Frontend**: Static site deployment (Vercel/Netlify recommended)
- **Database**: Redis managed by Render
- **Storage**: Cloudinary (existing) + frontend static assets

## Dependencies Management
- **Backend**: requirements.txt (existing)
- **Frontend**: package.json with:
  ```json
  {
    "dependencies": {
      "next": "^14.x",
      "react": "^18.x",
      "typescript": "^5.x",
      "tailwindcss": "^3.x",
      "axios": "^1.x",
      "@tanstack/react-query": "^5.x",
      "lucide-react": "^0.x",
      "clsx": "^2.x",
      "react-hot-toast": "^2.x"
    }
  }
  ```

## Constraints
- **Backend**: Single web dyno; background tasks must be lightweight
- **Frontend**: Static site limitations; API calls to backend for all dynamic data
- **Development**: Must follow single terminal rule except when running both services
- **Ephemeral filesystem**: Use cloud storage for media (existing Cloudinary setup)

## Dependencies to watch
- Amadeus rate limits
- Stripe/Circle webhooks vs polling reliability
- RPC stability for Circle Layer testnet
- **New**: CORS policy for production frontend domain
- **New**: API rate limiting for frontend requests 