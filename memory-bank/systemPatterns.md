# System Patterns

## Backend Architecture
- Single-service Flask app; background tasks via threading for non-blocking UX.
- Redis-backed session store keyed by user_id with state machine per conversation.
- External integrations:
  - IO Intelligence (LLM) for slot-filling and confirmation control tokens.
  - Amadeus API for IATA lookup and flight offers; simple in-memory caches.
  - Stripe webhooks for card payments; unified success handler.
  - Circle USDC via Payment Intents + polling.
  - Circle Layer EVM payments via Web3 polling (completed).
- PDF generation via FPDF2; uploaded to Cloudinary for WhatsApp/Telegram.
- Render deployment using render.yaml; Redis provisioned as service.
- Testing via pytest; services mocked in unit tests.

## Frontend Architecture (New)
- Next.js 14 with App Router and TypeScript for type safety
- TailwindCSS for styling with custom design system from Figma
- React Query for server state management and API caching
- Single-page application with real-time chat interface
- Component-based architecture:
  - `components/ui/` - Reusable UI primitives
  - `components/Chat/` - Chat-specific components
  - `components/Travel/` - Booking workflow components
  - `components/Payment/` - Payment integration components

## Integration Patterns
- **API Bridge**: New `/api/chat` Flask endpoint serves JSON responses for frontend
- **Session Correlation**: Frontend generates user IDs that map to Redis session keys
- **State Synchronization**: React Query syncs frontend state with backend conversation state
- **Payment Flow**: Web components integrate with existing Stripe/Circle/Circle Layer services
- **PDF Delivery**: Web-based preview and download instead of Cloudinary URLs

## Development Patterns
- **Single Terminal Rule**: All frontend work in one terminal session
- **Separate Processes**: Frontend (localhost:3000) + Backend (localhost:5000) when testing
- **Branch Strategy**: Continue development on `circle-layer-integration` branch
- **CORS Setup**: Development CORS for localhost:3000, production for deployed frontend

## Deployment Patterns
- **Backend**: Existing Render deployment remains unchanged
- **Frontend**: Static site deployment (Vercel/Netlify) or Render static site
- **Environment**: Frontend calls backend API via environment-configured base URL
