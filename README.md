# FinFlow - Financial Management System

A modern financial management system built with Django 5, TailwindCSS, Django REST Framework, Channels, Celery, and Redis.

## 🚀 Features

- **Django 5** - Latest Django framework
- **TailwindCSS** - Utility-first CSS framework for rapid UI development
- **Django REST Framework** - Powerful API development
- **Channels** - WebSocket support for real-time features
- **Celery** - Asynchronous task processing
- **Redis** - Caching and message broker
- **Responsive Design** - Mobile-first approach

## 📋 Prerequisites

- Python 3.8+
- Node.js and npm
- Redis server

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finflow
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies**
   ```bash
   npm install
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Build CSS (optional)**
   ```bash
   npm run build-css-prod
   ```

## 🚀 Running the Application

1. **Start Redis server** (in a separate terminal)
   ```bash
   redis-server
   ```

2. **Start Celery worker** (in a separate terminal)
   ```bash
   celery -A finflow worker --loglevel=info
   ```

3. **Start the Django development server**
   ```bash
   python manage.py runserver
   ```

4. **Access the application**
   - Web interface: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - API health check: http://127.0.0.1:8000/api/health/
   - API browsable interface: http://127.0.0.1:8000/api/

## 📁 Project Structure

```
finflow/
├── finflow/                 # Django project settings
│   ├── __init__.py
│   ├── settings.py         # Main settings file
│   ├── urls.py             # URL configuration
│   ├── wsgi.py             # WSGI configuration
│   ├── asgi.py             # ASGI configuration for Channels
│   └── celery.py           # Celery configuration
├── finflow/core/           # Core app
│   ├── views.py            # Views and API endpoints
│   ├── urls.py             # App URL patterns
│   └── apps.py             # App configuration
├── templates/              # HTML templates
│   └── core/
│       └── home.html       # Home page template
├── static/                 # Static files
│   ├── css/
│   │   └── output.css      # Compiled TailwindCSS
│   ├── js/
│   └── images/
├── staticfiles/            # Collected static files
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── tailwind.config.js     # TailwindCSS configuration
├── input.css              # TailwindCSS input file
└── manage.py              # Django management script
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

### Database

The project uses SQLite by default. To use PostgreSQL or MySQL, update the `DATABASES` setting in `finflow/settings.py`.

## 🎨 TailwindCSS Development

To watch for changes and rebuild CSS:

```bash
npm run build-css
```

For production builds:

```bash
npm run build-css-prod
```

## 📚 API Documentation

The API is built with Django REST Framework and includes:

- **Authentication**: Session and Token authentication
- **Pagination**: 20 items per page
- **Health Check**: `/api/health/` endpoint
- **Browsable API**: Available at `/api/`

## 🔄 Background Tasks

Celery is configured to handle background tasks. Example task:

```python
from finflow.celery import app

@app.task
def process_financial_data(data):
    # Your background task logic here
    pass
```

## 🌐 WebSocket Support

Channels is configured for WebSocket support. Add your WebSocket consumers in the `finflow/core/consumers.py` file.

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support, please open an issue in the repository or contact the development team.
