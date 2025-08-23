# Deployment Troubleshooting Guide

This guide provides step-by-step solutions for common deployment issues with the AI Travel Agent.

## Quick Diagnosis

### 1. Health Check
First, check the system status:
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "environment_variables": {
    "IO_API_KEY": "set",
    "REDIS_URL": "set",
    "TELEGRAM_BOT_TOKEN": "set",
    "AMADEUS_CLIENT_ID": "set",
    "CIRCLE_API_KEY": "set",
    "STRIPE_SECRET_KEY": "set"
  }
}
```

### 2. E2E Testing
Run comprehensive tests locally:
```bash
python test_e2e_deployment.py
```

## Common Issues & Solutions

### Issue 1: "Sorry, I'm having trouble connecting to my brain right now"

**Symptoms:**
- User receives generic error message
- No specific error in logs
- Health check shows system as healthy

**Root Cause:**
- AI service or Redis connection failure
- Error handling was not providing meaningful responses

**Solution:**
✅ **FIXED** - System now provides helpful fallback responses instead of generic errors

**Prevention:**
- Comprehensive error handling implemented
- AI service fallbacks for different conversation states
- Redis failure graceful degradation

### Issue 2: Redis Connection Failures

**Symptoms:**
- `'NoneType' object has no attribute 'flushall'` error
- Session data not persisting
- Admin tools failing

**Root Cause:**
- Redis service unavailable or misconfigured
- Environment variable not set correctly

**Solution:**
1. Verify `REDIS_URL` in Render environment variables
2. Check Redis service status in Render dashboard
3. Use health check to confirm Redis connection

**Prevention:**
✅ **FIXED** - System continues working with in-memory state when Redis is down

### Issue 3: Missing Environment Variables

**Symptoms:**
- `OpenAIError: The api_key client option must be set`
- Service fails to start
- Health check shows "not_set" for variables

**Root Cause:**
- Required API keys not configured in Render
- Environment variables not loaded properly

**Solution:**
1. Add missing variables in Render Environment tab
2. Verify variable names match exactly
3. Check for typos in API keys

**Required Variables:**
```bash
IO_API_KEY=your_io_intelligence_api_key
REDIS_URL=your_redis_connection_string
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
CIRCLE_API_KEY=your_circle_api_key
STRIPE_SECRET_KEY=your_stripe_secret_key
ADMIN_SECRET_KEY=your_admin_secret_key
```

### Issue 4: Circle Layer Token Configuration

**Symptoms:**
- "Circle Layer token address is not configured" error
- Native token payments not working

**Root Cause:**
- `CIRCLE_LAYER_TOKEN_ADDRESS` should be commented out for native tokens
- Wrong token symbol or decimals

**Solution:**
```bash
# Correct configuration for native CLAYER tokens
CIRCLE_LAYER_TOKEN_SYMBOL=CLAYER
CIRCLE_LAYER_TOKEN_DECIMALS=18
# CIRCLE_LAYER_TOKEN_ADDRESS=  # Comment out for native tokens
```

## Debugging Tools

### 1. Health Check Endpoint
```bash
GET /health
```
Shows:
- Redis connection status
- Environment variable status
- Overall system health

### 2. E2E Test Script
```bash
python test_e2e_deployment.py
```
Tests:
- Environment variables
- Redis connection
- AI service functionality
- Core logic processing
- Webhook simulation

### 3. Redis Management
```bash
GET /admin/clear-redis/{ADMIN_SECRET_KEY}
```
- Clears Redis database
- Useful for testing and debugging

### 4. Render Logs
Check Render dashboard logs for:
- `[Webhook]` - Message processing logs
- `[AI Service]` - AI API call logs
- `[Redis]` - Redis connection logs
- `[Core Logic]` - Session management logs

## Deployment Checklist

### Before Deployment
- [ ] All environment variables set in Render
- [ ] Redis service created and connected
- [ ] API keys valid and have sufficient credits
- [ ] Webhook URLs configured correctly

### After Deployment
- [ ] Health check returns "healthy" status
- [ ] E2E tests pass locally
- [ ] Send test message to verify functionality
- [ ] Check logs for any errors

### Monitoring
- [ ] Regular health check monitoring
- [ ] Log analysis for error patterns
- [ ] Payment processing verification
- [ ] User experience testing

## Recent Fixes Implemented

### Error Handling Improvements
- ✅ **AI Service Fallbacks**: Meaningful responses instead of generic errors
- ✅ **Redis Graceful Degradation**: System works even when Redis is down
- ✅ **Session Management**: Error handling for session operations
- ✅ **Comprehensive Logging**: Detailed debug messages

### Deployment Reliability
- ✅ **Health Check Endpoint**: Real-time system status
- ✅ **Environment Variable Validation**: Clear error messages
- ✅ **E2E Testing**: Complete test suite
- ✅ **Admin Tools**: Redis management and system monitoring

### User Experience
- ✅ **Helpful Error Messages**: Context-aware responses
- ✅ **Graceful Failures**: System continues working during issues
- ✅ **Better Logging**: Easier troubleshooting and debugging

## Support

If you encounter issues not covered in this guide:

1. **Check Render Logs**: Look for specific error messages
2. **Run E2E Tests**: Use `python test_e2e_deployment.py`
3. **Verify Configuration**: Use health check endpoint
4. **Review Recent Changes**: Check git history for recent fixes

The system is now designed to be resilient and provide a good user experience even when components fail. 