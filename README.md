# Product Importer API

A scalable web application for importing and managing products from CSV files, built with FastAPI, PostgreSQL, Celery, and Redis.

## Features

- 📤 **CSV Upload**: Import up to 500,000 products with real-time progress tracking
- 📦 **Product Management**: Full CRUD operations with filtering and pagination
- 🔔 **Webhooks**: Configure webhooks for product events (created, updated, deleted)
- ⚡ **Async Processing**: Large file imports handled asynchronously via Celery
- 🎨 **Modern UI**: Clean, responsive web interface

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis
- **Frontend**: Vanilla JavaScript, HTML, CSS

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (or Memurai on Windows)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Product_importer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/product_importer
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Set up database**
   ```bash
   # Create database
   createdb product_importer
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start services**
   
   Terminal 1 - FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   
   Terminal 2 - Celery worker:
   ```bash
   celery -A app.celery_app worker --pool=solo --loglevel=info
   ```
   (On Windows, use `--pool=solo`. On Linux/Mac, you can omit it.)

7. **Access the application**
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs


## API Endpoints

### Products
- `GET /api/products` - List products (with pagination and filters)
- `GET /api/products/{id}` - Get single product
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product
- `DELETE /api/products/bulk/all` - Delete all products

### Upload
- `POST /api/upload` - Upload CSV file
- `GET /api/upload/status/{task_id}` - Get upload progress (polling)
- `GET /api/upload/stream/{task_id}` - Stream upload progress (SSE)

### Webhooks
- `GET /api/webhooks` - List all webhooks
- `GET /api/webhooks/{id}` - Get webhook
- `POST /api/webhooks` - Create webhook
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook

## CSV Format

The CSV file should have the following columns:
- `sku` (required) - Product SKU (case-insensitive, unique)
- `name` (required) - Product name
- `description` (optional) - Product description

Example:
```csv
sku,name,description
PROD-001,Product One,First product
PROD-002,Product Two,Second product
```

## Webhook Events

- `product.created` - Fired when a product is created
- `product.updated` - Fired when a product is updated
- `product.deleted` - Fired when a product is deleted

Webhook payload format:
```json
{
  "event": "product.created",
  "data": {
    "id": 1,
    "sku": "PROD-001",
    "name": "Product One",
    "description": "Description",
    "active": true
  },
  "timestamp": 1234567890.123
}
```

## License

MIT

