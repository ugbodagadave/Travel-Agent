
# Flai: AI Travel Agent

**🚀 Deployed on Circle Layer Testnet**  
**🏆 Built at the UK AI Agent Hackathon Ep2 under the Circle Layer bounty**

![Flai Header](Flai%20header-17.png)

> **For detailed documentation on how Circle Layer was integrated in this project, see [Circle-Layer-Integration.md](Circle-Layer-Integration.md)**

An AI-powered travel agent that helps you book flights through natural conversation. Simply chat with Flai on WhatsApp or Telegram, and it will find the best flights for you and handle payments seamlessly.

## 💳 Payment Options

Flai supports three convenient payment methods:

- **💳 Card Payments**: Secure Stripe checkout for traditional card payments
- **🪙 USDC**: Send USDC cryptocurrency to a unique payment address
- **⛓️ On-chain**: Pay with native CLAYER tokens on Circle Layer blockchain

## 📱 Platform Integration

- **WhatsApp**: Chat with Flai through Twilio's WhatsApp Business API
- **Telegram**: Use our Telegram bot for seamless flight booking

## ✨ Key Features

- **Natural Language Understanding**: Just tell Flai where you want to go and when
- **Real-time Flight Search**: Live flight data from Amadeus API
- **Multi-traveler Support**: Book for groups with personalized tickets for each person
- **Smart Payment Processing**: Background monitoring ensures reliable payment confirmation
- **Persistent Conversations**: Flai remembers your booking details throughout the process

## 🛠️ Core Technologies

- **Backend**: Python 3.11, Flask
- **AI**: IO Intelligence API for natural language processing
- **Flight Data**: Amadeus Self-Service APIs
- **Payment Processing**: Stripe, Circle API (USDC), Circle Layer (CLAYER)
- **Session Storage**: Redis
- **Deployment**: Render
- **Testing**: Pytest

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- API keys for Twilio, Telegram, IO Intelligence, Amadeus, and payment services

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ugbodagadave/Travel-Agent
   cd Travel-Agent
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file with your API keys:
   ```bash
   # Twilio (WhatsApp)
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_phone_number

   # Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token

   # AI Service
   IO_API_KEY=your_io_api_key

   # Flight Data
   AMADEUS_CLIENT_ID=your_amadeus_client_id
   AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

   # Payment Services
   CIRCLE_API_KEY=your_circle_api_key
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

   # Circle Layer (CLAYER payments)
   CIRCLE_LAYER_RPC_URL=https://testnet-rpc.circlelayer.com
   CIRCLE_LAYER_CHAIN_ID=28525
   CIRCLE_LAYER_TOKEN_SYMBOL=CLAYER
   CIRCLE_LAYER_TOKEN_DECIMALS=18
   CIRCLE_LAYER_MERCHANT_MNEMONIC=your_mnemonic_here
   CIRCLE_LAYER_MIN_CONFIRMATIONS=3
   CIRCLE_LAYER_POLL_INTERVAL=15

   # Storage
   REDIS_URL=redis://localhost:6379
   BASE_URL=http://127.0.0.1:5000
   ```

5. **Run the application:**
   ```bash
   gunicorn app.main:app
   ```

## 🧪 Testing

Run the test suite to ensure everything is working:
```bash
pytest -sv
```

## 🔧 Troubleshooting

### Health Check
```bash
curl http://localhost:5000/health
```

### Common Issues

**"Sorry, I'm having trouble connecting to my brain right now"**
- Check your IO Intelligence API key
- Verify Redis connection

**Payment Processing Issues**
- Ensure payment service API keys are correct
- Check webhook URLs are properly configured

**Redis Connection Errors**
- Verify Redis server is running
- Check `REDIS_URL` configuration

## 📚 Documentation

- **[How It Works](how-it-works.md)**: Detailed technical documentation
- **[Circle Layer Integration](Circle-Layer-Integration.md)**: Complete guide to blockchain payment integration
- **[User Guide](how-it-works.txt)**: Simple user-focused explanation

## 🚨 Current Status

**Note**: This application is configured for testing. Real flight booking with Amadeus API is not yet implemented. The current flow generates mock itineraries for testing purposes.

## 🏗️ Architecture

Flai runs as a single, multi-threaded web service on Render. It handles:
- Incoming webhooks from Twilio and Telegram
- Background processing for flight searches and payment monitoring
- Session management with Redis
- PDF generation and delivery

The architecture ensures responsiveness while maintaining a great user experience.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest -sv`
5. Submit a pull request

## 📄 License


This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

