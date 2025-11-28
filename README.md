# Product Importer

A scalable web application to import products from CSV files, manage them via a dashboard, and trigger webhooks. Built with FastAPI, Celery, Redis, and PostgreSQL.

## Features

- **High Performance Import**: Asynchronously process large CSV files (500k+ records) using Celery workers.
- **Real-time Progress**: Track upload status via Server-Sent Events (SSE).
- **Product Management**: Create, Read, Update, Delete (CRUD) products via UI or API.
- **Webhooks**: Configure and trigger webhooks on product events.
- **Modern UI**: Server-side rendered templates with HTMX for dynamic interactions and Tailwind CSS for styling.

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (Async SQLAlchemy)
- **Queue**: Celery + Redis
- **Frontend**: Jinja2 Templates + HTMX + Tailwind CSS
- **Deployment**: Docker / Docker Compose

## Local Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd fulfil
    ```

2.  **Start services with Docker Compose**:
    ```bash
    docker-compose up --build
    ```

3.  **Access the application**:
    - Web UI: [http://localhost:8000](http://localhost:8000)
    - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Configuration

Environment variables are defined in `.env`.

- `DATABASE_URL`: PostgreSQL connection string.
- `CELERY_BROKER_URL`: Redis URL for Celery broker.
- `CELERY_RESULT_BACKEND`: Redis URL for Celery results.
- `UPLOAD_DIR`: Directory to store uploaded CSVs temporarily.

## API Endpoints

- `POST /api/upload`: Upload CSV file.
- `GET /api/progress/{task_id}`: SSE stream for upload progress.
- `GET /api/products`: List products (pagination, search).
- `POST /api/products`: Create product.
- `GET /api/products/{sku}`: Get product details.
- `PUT /api/products/{sku}`: Update product.
- `DELETE /api/products/{sku}`: Delete product.
- `DELETE /api/products`: Bulk delete all products.
- `GET /api/webhooks`: List webhooks.
- `POST /api/webhooks`: Create webhook.
- `DELETE /api/webhooks/{id}`: Delete webhook.

## Deployment

The application is Dockerized and ready for deployment on platforms like Render, Railway, or AWS ECS.

1.  **Build the image**:
    ```bash
    docker build -t product-importer .
    ```

2.  **Run the container** (ensure Redis and Postgres are available):
    ```bash
    docker run -p 8000:8000 --env-file .env product-importer
    ```
