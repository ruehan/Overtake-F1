# OpenF1 Dashboard

A real-time F1 race data visualization dashboard using React and FastAPI.

## Features

- Real-time race position tracking
- Driver and team information
- Weather data integration
- Lap time analysis
- Pit stop tracking
- Team radio archive
- WebSocket support for live updates

## Tech Stack

- **Frontend**: React with TypeScript, D3.js for visualizations, Socket.io for real-time updates
- **Backend**: FastAPI (Python), WebSocket support, Redis for caching
- **API**: OpenF1 API integration

## Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Redis (optional, for caching)

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment file:
```bash
cp .env.example .env
```

5. Edit `.env` and add your OpenF1 API key if you have one (optional)

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start the Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

The API will be available at http://localhost:8000

### Start the Frontend

In a new terminal:

```bash
cd frontend
npm start
```

The application will be available at http://localhost:3000

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
overtake/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality (middleware, exceptions)
│   │   ├── models/       # Data models
│   │   └── services/     # Business logic and external API clients
│   ├── main.py           # Application entry point
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API and WebSocket services
│   │   └── types/        # TypeScript type definitions
│   └── package.json      # Node dependencies
└── README.md
```

## Development

### Backend Development

The backend runs with hot-reload enabled by default. Any changes to Python files will automatically restart the server.

### Frontend Development

The React development server includes hot module replacement. Changes to components will update in the browser without a full reload.

## Environment Variables

### Backend (.env)

- `OPENF1_API_KEY`: Your OpenF1 API key (optional)
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379)
- `RATE_LIMIT_PER_MINUTE`: API rate limit (default: 60)
- `DEBUG`: Enable debug mode (default: true)

### Frontend

Create a `.env` file in the frontend directory:

```
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=http://localhost:8000
```

## License

This project is licensed under the MIT License.