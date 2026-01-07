# WhatsApp Integration Guide

## Overview

This document provides comprehensive guidance for integrating WhatsApp support into the Study Agent Chatbot. While the initial implementation uses Telegram, the architecture is designed to support multiple messaging platforms.

## Current State

The application is built with a **clean architecture** that separates the presentation layer (bot interface) from the business logic. This design makes it straightforward to add new messaging platforms.

## Integration Strategy

### Approach 1: Using WhatsApp Business API (Official)

#### Prerequisites
- WhatsApp Business Account
- Meta for Developers account
- Verified business
- Phone number for WhatsApp Business

#### Required Libraries
```bash
pip install whatsapp-business-python  # Official WhatsApp Business API wrapper
# OR
pip install httpx  # Already in project for REST API calls
```

#### Cost Considerations
- **WhatsApp Business API** is a paid service
- Pricing varies by country and message type
- Free tier: 1,000 conversations per month
- Cost per conversation: ~$0.005 - $0.10 depending on region

### Approach 2: Using Unofficial Libraries

#### Libraries
```bash
pip install whatsapp-chatbot-python
# OR
pip install yowsup  # Unofficial WhatsApp protocol implementation
```

#### Considerations
- ⚠️ Against WhatsApp Terms of Service
- Risk of account ban
- Less reliable
- Not recommended for production

### Approach 3: Using Twilio WhatsApp API (Recommended for MVP)

#### Prerequisites
- Twilio account
- WhatsApp-enabled Twilio phone number
- Twilio API credentials

#### Required Libraries
```bash
pip install twilio  # Twilio SDK
```

#### Benefits
- Easier setup than official WhatsApp Business API
- Good for prototyping and small-scale deployment
- No business verification required initially
- Pay-as-you-go pricing

## Recommended Implementation: Twilio WhatsApp API

### Step 1: Account Setup

1. **Create Twilio Account**
   - Sign up at https://www.twilio.com
   - Verify your email and phone number
   - Note your Account SID and Auth Token

2. **Enable WhatsApp Sandbox**
   - Navigate to Messaging > Try it out > Send a WhatsApp message
   - Follow instructions to connect your WhatsApp number
   - Note your WhatsApp-enabled phone number

3. **Configure Webhook**
   - Set webhook URL for incoming messages
   - URL format: `https://your-domain.com/webhook/whatsapp`

### Step 2: Project Structure Updates

Add WhatsApp presentation layer:

```
src/study_agent/presentation/whatsapp/
├── __init__.py
├── bot.py                    # WhatsApp bot initialization
├── webhook.py                # Webhook handler for incoming messages
├── handlers/
│   ├── __init__.py
│   ├── message_handler.py   # Process incoming messages
│   └── command_handler.py   # Handle commands
└── formatters/
    ├── __init__.py
    └── message_formatter.py # Format responses for WhatsApp
```

### Step 3: Environment Configuration

Update `.env`:
```env
# WhatsApp Configuration (Twilio)
WHATSAPP_ENABLED=false
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
WEBHOOK_URL=https://your-domain.com/webhook/whatsapp
```

### Step 4: Implementation

#### 4.1 WhatsApp Client

```python
# src/study_agent/infrastructure/clients/whatsapp_client.py

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Async wrapper for Twilio WhatsApp client."""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """Initialize WhatsApp client.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: WhatsApp-enabled phone number (format: whatsapp:+1234567890)
        """
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        
    async def send_message(
        self, 
        to: str, 
        message: str, 
        media_url: Optional[str] = None
    ) -> bool:
        """Send WhatsApp message.
        
        Args:
            to: Recipient phone number (format: whatsapp:+1234567890)
            message: Message text
            media_url: Optional media URL for images/documents
            
        Returns:
            True if message sent successfully
        """
        try:
            kwargs = {
                "body": message,
                "from_": self.from_number,
                "to": to,
            }
            
            if media_url:
                kwargs["media_url"] = [media_url]
                
            msg = self.client.messages.create(**kwargs)
            logger.info(f"Message sent: {msg.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        parameters: dict
    ) -> bool:
        """Send WhatsApp template message (pre-approved messages).
        
        Args:
            to: Recipient phone number
            template_name: Name of approved template
            parameters: Template parameters
            
        Returns:
            True if message sent successfully
        """
        # Implementation for template messages
        pass
```

#### 4.2 WhatsApp Bot Handler

```python
# src/study_agent/presentation/whatsapp/bot.py

from study_agent.infrastructure.clients.whatsapp_client import WhatsAppClient
from study_agent.config.settings import settings
from study_agent.presentation.whatsapp.handlers.message_handler import MessageHandler
import logging

logger = logging.getLogger(__name__)


class WhatsAppBot:
    """WhatsApp bot implementation."""
    
    def __init__(self):
        """Initialize WhatsApp bot."""
        self.client = WhatsAppClient(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_number=settings.TWILIO_WHATSAPP_NUMBER
        )
        self.message_handler = MessageHandler(self.client)
        
    async def start(self):
        """Start the WhatsApp bot (webhook server)."""
        logger.info("WhatsApp bot initialized")
        # Webhook will be handled by FastAPI/Flask
        
    async def stop(self):
        """Stop the WhatsApp bot."""
        logger.info("WhatsApp bot stopped")
        
    async def process_incoming_message(self, data: dict) -> str:
        """Process incoming webhook message.
        
        Args:
            data: Webhook payload from Twilio
            
        Returns:
            TwiML response string
        """
        from_number = data.get("From", "")
        message_body = data.get("Body", "")
        
        logger.info(f"Received message from {from_number}: {message_body}")
        
        response = await self.message_handler.handle_message(
            from_number, 
            message_body
        )
        
        return response
```

#### 4.3 Webhook Endpoint (using FastAPI)

```python
# src/study_agent/presentation/whatsapp/webhook.py

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from study_agent.presentation.whatsapp.bot import WhatsAppBot
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
whatsapp_bot = WhatsAppBot()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    request: Request = None
):
    """Handle incoming WhatsApp messages via Twilio webhook.
    
    Args:
        From: Sender's WhatsApp number
        Body: Message text
        MessageSid: Message ID
        request: Full request object
        
    Returns:
        TwiML response
    """
    logger.info(f"Webhook triggered: From={From}, Body={Body}")
    
    # Process message through bot
    data = {
        "From": From,
        "Body": Body,
        "MessageSid": MessageSid
    }
    
    response_text = await whatsapp_bot.process_incoming_message(data)
    
    # Create TwiML response
    twiml_response = MessagingResponse()
    twiml_response.message(response_text)
    
    return Response(content=str(twiml_response), media_type="application/xml")


@app.get("/webhook/whatsapp/status")
async def whatsapp_status():
    """Health check endpoint for WhatsApp webhook."""
    return {"status": "ok", "platform": "whatsapp"}
```

#### 4.4 Message Handler

```python
# src/study_agent/presentation/whatsapp/handlers/message_handler.py

from study_agent.infrastructure.clients.whatsapp_client import WhatsAppClient
from study_agent.application.services.user_service import UserService
from study_agent.application.services.study_manager import StudyManager
import logging

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handle incoming WhatsApp messages."""
    
    def __init__(self, client: WhatsAppClient):
        """Initialize message handler.
        
        Args:
            client: WhatsApp client for sending responses
        """
        self.client = client
        # Inject services via dependency injection
        self.user_service: UserService = None  # Set via DI
        self.study_manager: StudyManager = None  # Set via DI
        
    async def handle_message(self, from_number: str, message: str) -> str:
        """Handle incoming message.
        
        Args:
            from_number: Sender's phone number
            message: Message text
            
        Returns:
            Response text
        """
        message = message.strip().lower()
        
        # Check if user exists
        user = await self.user_service.get_user_by_whatsapp_number(from_number)
        
        if not user:
            # New user - register
            user = await self.user_service.create_whatsapp_user(from_number)
            return self._format_welcome_message()
        
        # Route to appropriate handler based on message content
        if message.startswith("/"):
            return await self._handle_command(user, message)
        else:
            return await self._handle_text(user, message)
            
    def _format_welcome_message(self) -> str:
        """Format welcome message for new users."""
        return (
            "👋 Welcome to Study Agent!\n\n"
            "I'm here to help you study and retain knowledge through "
            "periodic quizzes.\n\n"
            "Available commands:\n"
            "/start - Get started\n"
            "/help - Show help\n"
            "/addrepo - Add a GitHub repository\n"
            "/study - Start a study session\n"
            "/stats - View your statistics"
        )
        
    async def _handle_command(self, user, command: str) -> str:
        """Handle command messages."""
        if command == "/start" or command == "/help":
            return self._format_help_message()
        elif command == "/addrepo":
            return "Please send me the GitHub repository URL."
        elif command == "/study":
            return await self._start_study_session(user)
        elif command == "/stats":
            return await self._get_user_stats(user)
        else:
            return "Unknown command. Send /help to see available commands."
            
    async def _handle_text(self, user, text: str) -> str:
        """Handle regular text messages."""
        # Check if user is in a conversation flow (e.g., quiz)
        # This would use a state machine similar to Telegram FSM
        return "I received your message. Use /help to see available commands."
        
    def _format_help_message(self) -> str:
        """Format help message."""
        return (
            "📚 *Study Agent Commands*\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/addrepo <url> - Add a GitHub repository\n"
            "/listrepos - List your repositories\n"
            "/study - Start a study session\n"
            "/stats - View your performance statistics\n"
            "/schedule - Configure study schedule\n"
            "/settings - Manage settings"
        )
```

### Step 5: Database Updates

Update the User model to support both Telegram and WhatsApp:

```python
# src/study_agent/infrastructure/database/models.py

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    
    # Telegram fields
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    telegram_username = Column(String, nullable=True)
    
    # WhatsApp fields
    whatsapp_number = Column(String, unique=True, nullable=True)
    whatsapp_name = Column(String, nullable=True)
    
    # Common fields
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    platform = Column(String, default="telegram")  # 'telegram' or 'whatsapp'
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Step 6: Configuration Updates

Update settings to support multiple platforms:

```python
# src/study_agent/config/settings.py

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # ... existing Telegram settings ...
    
    # WhatsApp settings
    WHATSAPP_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    WEBHOOK_URL: str = ""
    
    # Platform
    ENABLED_PLATFORMS: list[Literal["telegram", "whatsapp"]] = ["telegram"]
    
    class Config:
        env_file = ".env"
        
        
settings = Settings()
```

### Step 7: Main Application Updates

Update main entry point to support both platforms:

```python
# src/study_agent/__main__.py

import asyncio
import logging
from study_agent.config.settings import settings
from study_agent.presentation.telegram.bot import TelegramBot
from study_agent.presentation.whatsapp.bot import WhatsAppBot
from fastapi import FastAPI
import uvicorn

logger = logging.getLogger(__name__)


async def start_telegram_bot():
    """Start Telegram bot."""
    if "telegram" in settings.ENABLED_PLATFORMS:
        logger.info("Starting Telegram bot...")
        telegram_bot = TelegramBot()
        await telegram_bot.start()


async def start_whatsapp_bot():
    """Start WhatsApp webhook server."""
    if "whatsapp" in settings.ENABLED_PLATFORMS:
        logger.info("Starting WhatsApp webhook server...")
        # WhatsApp uses webhook, so we start a web server
        from study_agent.presentation.whatsapp.webhook import app
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point."""
    logger.info("Starting Study Agent...")
    
    # Start both bots if enabled
    tasks = []
    
    if "telegram" in settings.ENABLED_PLATFORMS:
        tasks.append(start_telegram_bot())
        
    if "whatsapp" in settings.ENABLED_PLATFORMS:
        tasks.append(start_whatsapp_bot())
        
    if not tasks:
        logger.error("No platforms enabled!")
        return
        
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Differences: Telegram vs WhatsApp

| Feature | Telegram | WhatsApp |
|---------|----------|----------|
| Architecture | Long polling / Webhooks | Webhooks only |
| Rich UI | Inline keyboards, buttons | Limited (buttons via templates) |
| Media Support | Full support | Images, documents, videos |
| Message Format | Markdown, HTML | Plain text, limited formatting |
| Bot Commands | Native support (/) | Custom implementation |
| State Management | Built-in FSM | Custom state management needed |
| Group Chat | Full support | Limited |
| API Cost | Free | Paid (via Twilio or official API) |

## Platform-Specific Adaptations

### 1. Command Handling

**Telegram**: Native bot commands with autocomplete
**WhatsApp**: Detect commands by prefix, or use button templates

### 2. Quiz Interface

**Telegram**: Inline keyboards with callback buttons
**WhatsApp**: 
- Option 1: Send numbered options, accept number as response
- Option 2: Use reply buttons (limited to 3 buttons)

Example WhatsApp quiz format:
```
Question: What is Python's GIL?

1. Global Interpreter Lock
2. General Interface Library
3. Graphical Interaction Layer
4. Global Import Locator

Reply with the number of your answer (1-4)
```

### 3. Rich Formatting

**Telegram**: Full Markdown/HTML support
**WhatsApp**: Limited to:
- *bold*
- _italic_
- ~strikethrough~
- ```code```

### 4. State Management

Implement custom state management for WhatsApp:

```python
# src/study_agent/presentation/whatsapp/states.py

from enum import Enum
from typing import Dict, Optional
import asyncio


class WhatsAppState(Enum):
    """WhatsApp conversation states."""
    IDLE = "idle"
    AWAITING_REPO_URL = "awaiting_repo_url"
    IN_QUIZ = "in_quiz"
    AWAITING_ANSWER = "awaiting_answer"
    CONFIGURING_SCHEDULE = "configuring_schedule"


class StateManager:
    """Manage user conversation states."""
    
    def __init__(self):
        self._states: Dict[str, WhatsAppState] = {}
        self._context: Dict[str, dict] = {}
        
    async def get_state(self, user_id: str) -> WhatsAppState:
        """Get current state for user."""
        return self._states.get(user_id, WhatsAppState.IDLE)
        
    async def set_state(
        self, 
        user_id: str, 
        state: WhatsAppState, 
        context: Optional[dict] = None
    ):
        """Set state for user."""
        self._states[user_id] = state
        if context:
            self._context[user_id] = context
            
    async def get_context(self, user_id: str) -> dict:
        """Get context for user."""
        return self._context.get(user_id, {})
        
    async def clear_state(self, user_id: str):
        """Clear state for user."""
        self._states.pop(user_id, None)
        self._context.pop(user_id, None)
```

## Testing WhatsApp Integration

### 1. Unit Tests

```python
# tests/unit/test_whatsapp/test_message_handler.py

import pytest
from study_agent.presentation.whatsapp.handlers.message_handler import MessageHandler


@pytest.mark.asyncio
async def test_handle_start_command(mock_whatsapp_client, mock_user):
    """Test handling /start command."""
    handler = MessageHandler(mock_whatsapp_client)
    response = await handler.handle_message("+1234567890", "/start")
    assert "Welcome" in response


@pytest.mark.asyncio
async def test_handle_unknown_command(mock_whatsapp_client, mock_user):
    """Test handling unknown command."""
    handler = MessageHandler(mock_whatsapp_client)
    response = await handler.handle_message("+1234567890", "/unknown")
    assert "Unknown command" in response
```

### 2. Integration Tests

```python
# tests/integration/test_whatsapp_webhook.py

import pytest
from fastapi.testclient import TestClient
from study_agent.presentation.whatsapp.webhook import app


def test_whatsapp_webhook_endpoint():
    """Test WhatsApp webhook endpoint."""
    client = TestClient(app)
    
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+1234567890",
            "Body": "/start",
            "MessageSid": "SM123456"
        }
    )
    
    assert response.status_code == 200
    assert "Welcome" in response.text
```

### 3. Manual Testing with Twilio Sandbox

1. Join Twilio WhatsApp Sandbox
2. Send test messages
3. Verify responses
4. Test various command flows

## Deployment Considerations

### 1. Webhook Requirements

- **HTTPS**: Twilio requires HTTPS webhook endpoint
- **Public URL**: Use ngrok for local testing
- **Response Time**: Must respond within 15 seconds

### 2. Hosting Options

**Option 1: Cloud Functions (Serverless)**
- AWS Lambda + API Gateway
- Google Cloud Functions
- Azure Functions

**Option 2: Traditional Hosting**
- Deploy FastAPI app on VPS
- Use Nginx as reverse proxy
- SSL certificate (Let's Encrypt)

**Option 3: Platform-as-a-Service**
- Heroku
- Railway
- Render

### 3. Environment Setup

```bash
# For local testing with ngrok
ngrok http 8000

# Update webhook URL in Twilio console
# URL: https://your-ngrok-url.ngrok.io/webhook/whatsapp
```

### 4. Scaling Considerations

- Use Redis for distributed state management
- Implement message queues for async processing
- Use database connection pooling
- Implement rate limiting

## Migration Strategy

### Phase 1: Parallel Development
1. Keep Telegram as primary platform
2. Develop WhatsApp integration in separate module
3. Share business logic layer

### Phase 2: Testing
1. Beta test with small user group
2. Collect feedback
3. Iterate on UX

### Phase 3: Full Deployment
1. Enable both platforms
2. Allow users to choose preferred platform
3. Support cross-platform accounts (same user, multiple platforms)

## Cost Analysis

### Twilio Pricing (Approximate)
- WhatsApp messages: $0.005 - $0.02 per message (varies by country)
- Session-based pricing: $0.0042 per session (24-hour window)
- Free tier: Limited messages

### Official WhatsApp Business API
- Meta Business verification required
- Pricing varies significantly by region
- Free tier: 1,000 conversations/month
- Paid: $0.005 - $0.10 per conversation

### Recommendation for MVP
Start with **Twilio WhatsApp Sandbox** for:
- Quick prototyping
- Low initial cost
- Easy setup
- Good documentation

Later, migrate to **official WhatsApp Business API** for:
- Production scale
- Better reliability
- Official support
- No "Sandbox" branding

## Limitations & Workarounds

### Limitation 1: No Inline Keyboards
**Workaround**: Use numbered options or reply buttons

### Limitation 2: Limited Media Support
**Workaround**: Use external links for complex content

### Limitation 3: Template Message Requirements
**Workaround**: 
- Get templates approved for scheduled messages
- Use session messages for interactive conversations

### Limitation 4: 24-Hour Session Window
**Workaround**: 
- Send template message to re-engage users
- Encourage users to initiate conversations

## Security Considerations

1. **Webhook Validation**: Verify Twilio signatures
2. **Phone Number Privacy**: Hash and encrypt phone numbers
3. **Rate Limiting**: Prevent spam and abuse
4. **Data Privacy**: Comply with GDPR/CCPA
5. **Message Encryption**: End-to-end encrypted by WhatsApp

## Conclusion

Adding WhatsApp support to the Study Agent Chatbot is achievable with the proposed architecture. The key is to:

1. Use Twilio WhatsApp API for easier integration
2. Adapt UI patterns to WhatsApp's constraints
3. Implement custom state management
4. Share business logic between platforms
5. Test thoroughly with real users

The modular architecture allows adding WhatsApp without disrupting the existing Telegram implementation, enabling a smooth multi-platform experience.

## Next Steps

1. **Immediate**: Complete Telegram implementation
2. **Phase 2**: Set up Twilio account and sandbox
3. **Phase 3**: Implement WhatsApp webhook handler
4. **Phase 4**: Adapt quiz interface for WhatsApp
5. **Phase 5**: Beta test with users
6. **Phase 6**: Production deployment

## Resources

- [Twilio WhatsApp API Documentation](https://www.twilio.com/docs/whatsapp)
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
