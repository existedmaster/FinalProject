## FastAPI Calculator Service

* Now with User Profile & Password Change !
To perfrom a password change or update your profile
Register or Login
Select profile button to update your profile or change your password

Run locally with either Docker Compose (recommended) or a local Python environment.

### Prerequisites
- Docker and Docker Compose, or Python 3.10+ with `pip`
- PostgreSQL available at `postgres://postgres:postgres@localhost:5432/fastapi_db` (Compose will provide this automatically)
- For Playwright UI tests, install browsers with `python -m playwright install chromium`

### Run the application
**Using Docker Compose**
```bash
docker compose up --build
```
The API will be reachable at http://localhost:8000 and pgAdmin at http://localhost:5050.

**Using Python locally (without containers)**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
python -m app.database_init  # initialize tables and seed as needed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run tests locally
Make sure PostgreSQL is reachable and the `DATABASE_URL`/`TEST_DATABASE_URL` environment variables are set. With the virtualenv activated:
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```
If you use Docker Compose, you can reuse the running `db` container and point `TEST_DATABASE_URL` to `postgresql://postgres:postgres@localhost:5432/fastapi_test_db`.

- For end-to-end UI coverage, ensure Playwright browsers are installed (`python -m playwright install chromium`).
- The suite uses `pytest-asyncio` for async tests; it is already pinned in `requirements.txt`.

### Docker Hub image
Published images: `existedmaster/final`
- View on Docker Hub: https://hub.docker.com/r/existedmaster/final
- Pull: `docker pull existedmaster/final:latest`
- Run:
  ```bash
  docker run -p 8000:8000 \
    -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/fastapi_db \
    existedmaster/final:latest
  ```
