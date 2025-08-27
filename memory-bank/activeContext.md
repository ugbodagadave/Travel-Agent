# Active Context

## Current Focus
- Develop Next.js frontend chatbot interface to integrate with existing WhatsApp/Telegram travel booking system.
- Create web-based chat UI that maintains the same conversation flow and functionality as messaging platforms.

## Recent Changes
- Completed Next.js 14 project setup with TypeScript, Tailwind CSS, ESLint
- Installed required dependencies: axios, @tanstack/react-query, lucide-react, clsx, react-hot-toast
- Created comprehensive Frontend Implementation Plan (frontendplan.md) with 8 phases
- Set up project structure: `frontend/` directory alongside existing `app/` backend

## Next Steps
- **Phase 1.1**: Awaiting Figma design link to begin design system integration
- Extract design assets and create theme configuration using Figma MCP tool
- Build core chat interface components (ChatContainer, MessageBubble, MessageInput)
- Create new Flask API endpoint `/api/chat` for frontend communication
- Implement CORS configuration for localhost:3000 frontend

## Active Development Branch
- Working on `circle-layer-integration` branch
- Frontend development will continue on same branch
- Following single terminal rule for frontend work, separate terminals only when running both frontend + backend

## Technical Decisions
- Next.js 14 with App Router for modern React development
- TailwindCSS for styling following project memory requirements
- TypeScript for type safety
- React Query for server state management
- Maintain existing Flask backend, add JSON API endpoints
- PDF delivery to work like Telegram - preview/download in browser

## Integration Points
- Backend: Modify core_logic.py to support JSON responses
- Frontend: Create API client to communicate with Flask endpoints
- Session Management: Bridge Redis sessions with frontend state
- Payment Systems: Integrate existing Stripe/Circle USDC/Circle Layer payments into web UI
- PDF Handling: Web-based PDF viewer and download functionality

## Current Blockers
- Waiting for Figma design link to proceed with Phase 1.1 (Design Integration)

## Risks
- CORS configuration for production deployment
- Session correlation between frontend user IDs and backend Redis keys
- PDF delivery mechanism for web vs WhatsApp/Telegram differences
