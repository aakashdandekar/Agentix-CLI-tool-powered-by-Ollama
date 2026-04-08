# WhatsApp Web Clone

A real-time messaging web application built with FastAPI, featuring a WhatsApp-like interface with WebSocket support for live messaging.

![WhatsApp Clone](https://img.shields.io/badge/WhatsApp-Clone-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)

## Features

- 💬 **Real-time Messaging** - Instant message delivery using WebSockets
- 👥 **Multiple Users** - Pre-configured user accounts for testing
- 🔄 **Online Status** - Real-time presence indicators
- 📝 **Message History** - Persistent message storage
- 🔍 **Search** - Search through conversations
- 📱 **Responsive Design** - Works on desktop and mobile
- ✨ **Modern UI** - Clean, WhatsApp-inspired interface

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Real-time**: WebSockets
- **Styling**: Custom CSS with Font Awesome icons

## Installation

### 1. Clone the repository
```bash
cd whatsapp-clone
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open in browser
Navigate to: `http://localhost:8000`

## Usage

1. **Select User** - Choose a user from the dropdown login screen
2. **Start Chatting** - Click on a conversation from the sidebar
3. **Send Messages** - Type a message and press Enter or click Send
4. **Real-time Updates** - Messages are delivered instantly via WebSocket

## Pre-configured Users

| Username | Display Name |
|----------|--------------|
| alice | Alice Johnson |
| bob | Bob Smith |
| charlie | Charlie Brown |
| diana | Diana Prince |
| emma | Emma Wilson |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main application page |
| GET | `/api/users` | Get all users |
| GET | `/api/conversations/{username}` | Get user conversations |
| GET | `/api/messages/{user1}/{user2}` | Get messages between two users |
| WS | `/ws/{username}` | WebSocket connection |

## WebSocket Events

### Sending a message
```json
{
  "type": "message",
  "to": "bob",
  "content": "Hello Bob!"
}
```

### Typing indicator
```json
{
  "type": "typing",
  "to": "bob"
}
```

## Project Structure

```
whatsapp-clone/
├── main.py              # FastAPI backend
├── templates/
│   └── index.html       # Frontend application
├── static/              # Static files directory
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Screenshots

The application features:
- Sidebar with conversation list
- Search functionality
- Real-time message display
- Typing indicators
- Online status indicators
- Beautiful WhatsApp-style design

## Development

To run in development mode with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --reload
```

## Notes

- This is a demo/educational project
- Messages are stored in memory (not persistent)
- For production, integrate with a proper database
- WebSocket reconnection is handled automatically

## License

MIT License - Feel free to use and modify!
