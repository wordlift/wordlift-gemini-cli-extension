# Scheduling Daily Imports

This guide covers different approaches for scheduling daily Knowledge Graph syncs.

## Option 1: Cron Jobs (Linux/Unix)

Best for: VPS, dedicated servers, or always-on machines

### Basic Setup

```bash
# Edit crontab
crontab -e

# Add daily sync at 2 AM
0 2 * * * cd /path/to/project && /usr/bin/python3 scripts/kg_sync.py \
  --api-key $WORDLIFT_API_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input /path/to/products.json \
  --incremental >> /var/log/wordlift-sync.log 2>&1
```

### With Environment Variables

```bash
# Create .env file
echo "WORDLIFT_API_KEY=your_key_here" > /path/to/project/.env
echo "DATASET_URI=https://data.wordlift.io/wl123" >> /path/to/project/.env

# Create wrapper script: daily_sync.sh
#!/bin/bash
set -a
source /path/to/project/.env
set +a

cd /path/to/project

# Extract products from your source (database, API, files)
python3 scripts/extract_products.py > /tmp/daily_products.json

# Sync to WordLift
python3 scripts/kg_sync.py \
  --api-key "$WORDLIFT_API_KEY" \
  --dataset-uri "$DATASET_URI" \
  --input /tmp/daily_products.json \
  --incremental

# Send notification on completion
if [ $? -eq 0 ]; then
  echo "WordLift sync completed successfully" | mail -s "KG Sync Success" admin@example.com
else
  echo "WordLift sync failed" | mail -s "KG Sync FAILED" admin@example.com
fi
```

```bash
# Make executable
chmod +x /path/to/project/daily_sync.sh

# Add to crontab
0 2 * * * /path/to/project/daily_sync.sh
```

### Multiple Times Per Day

```bash
# Every 6 hours
0 */6 * * * /path/to/project/daily_sync.sh

# Specific times: 2 AM, 10 AM, 6 PM
0 2,10,18 * * * /path/to/project/daily_sync.sh

# Every hour during business hours (9 AM - 5 PM)
0 9-17 * * * /path/to/project/daily_sync.sh
```

## Option 2: GitHub Actions (CI/CD)

Best for: Teams using GitHub, serverless approach, easy monitoring

### Workflow File

Create `.github/workflows/daily-sync.yml`:

```yaml
name: Daily WordLift KG Sync

on:
  schedule:
    # Run daily at 2:00 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual triggering

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests --break-system-packages

      - name: Extract products from database
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          python scripts/extract_products.py > products.json

      - name: Sync to WordLift
        env:
          WORDLIFT_API_KEY: ${{ secrets.WORDLIFT_API_KEY }}
          DATASET_URI: ${{ secrets.DATASET_URI }}
        run: |
          python scripts/kg_sync.py \
            --api-key "$WORDLIFT_API_KEY" \
            --dataset-uri "$DATASET_URI" \
            --input products.json \
            --incremental

      - name: Upload sync logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: sync-logs
          path: |
            *.log
            products.json

      - name: Notify on failure
        if: failure()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: WordLift Sync Failed
          to: admin@example.com
          from: github-actions@example.com
          body: Daily WordLift sync failed. Check the workflow logs.
```

### Configure Secrets

In GitHub repository settings → Secrets and variables → Actions:
- `WORDLIFT_API_KEY`
- `DATASET_URI`
- `DATABASE_URL` (if needed)
- `EMAIL_USERNAME` / `EMAIL_PASSWORD` (for notifications)

### Manual Trigger

You can manually trigger the workflow from GitHub Actions tab using the "Run workflow" button.

## Option 3: Python Scheduler (APScheduler)

Best for: Long-running applications, Docker containers

### Using APScheduler

```python
#!/usr/bin/env python3
"""
Scheduled WordLift KG Sync Service
Runs as a long-running process with scheduled syncs.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os
from datetime import datetime

from scripts.kg_sync import KGSyncOrchestrator
from scripts.extract_products import extract_products_from_source

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wordlift_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.environ.get('WORDLIFT_API_KEY')
DATASET_URI = os.environ.get('DATASET_URI', 'https://data.wordlift.io/wl123')

def run_sync():
    """Execute daily sync."""
    try:
        logger.info("Starting daily sync...")

        # Extract products from your source
        products = extract_products_from_source()
        logger.info(f"Extracted {len(products)} products")

        # Sync to WordLift
        orchestrator = KGSyncOrchestrator(API_KEY, DATASET_URI)
        stats = orchestrator.incremental_update(products)

        logger.info(f"Sync complete - Created: {stats['created']}, Updated: {stats['updated']}, Errors: {stats['errors']}")

        # Send success notification (optional)
        send_notification("Daily sync completed successfully", stats)

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        send_notification("Daily sync FAILED", {"error": str(e)})

def send_notification(subject, data):
    """Send notification (implement based on your needs)."""
    # Email, Slack, SMS, etc.
    pass

def main():
    scheduler = BlockingScheduler()

    # Schedule daily sync at 2 AM
    scheduler.add_job(
        run_sync,
        CronTrigger(hour=2, minute=0),
        id='daily_sync',
        name='Daily WordLift KG Sync',
        replace_existing=True
    )

    logger.info("Scheduler started. Daily sync scheduled for 2:00 AM")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")

if __name__ == '__main__':
    main()
```

### Running as a Service

#### Using systemd (Linux)

Create `/etc/systemd/system/wordlift-sync.service`:

```ini
[Unit]
Description=WordLift KG Sync Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="WORDLIFT_API_KEY=your_key"
Environment="DATASET_URI=https://data.wordlift.io/wl123"
ExecStart=/usr/bin/python3 /path/to/project/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable wordlift-sync
sudo systemctl start wordlift-sync

# Check status
sudo systemctl status wordlift-sync

# View logs
journalctl -u wordlift-sync -f
```

#### Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY scripts/ ./scripts/
COPY scheduler.py .

RUN pip install requests apscheduler --break-system-packages

CMD ["python", "scheduler.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  wordlift-sync:
    build: .
    environment:
      - WORDLIFT_API_KEY=${WORDLIFT_API_KEY}
      - DATASET_URI=${DATASET_URI}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

```bash
# Run
docker-compose up -d

# View logs
docker-compose logs -f
```

## Option 4: Cloud Functions (Serverless)

Best for: Serverless architecture, minimal infrastructure

### AWS Lambda

```python
# lambda_function.py
import json
import os
from scripts.kg_sync import KGSyncOrchestrator
from scripts.extract_products import extract_products_from_source

def lambda_handler(event, context):
    """AWS Lambda handler for scheduled sync."""

    api_key = os.environ['WORDLIFT_API_KEY']
    dataset_uri = os.environ['DATASET_URI']

    try:
        # Extract products
        products = extract_products_from_source()

        # Sync
        orchestrator = KGSyncOrchestrator(api_key, dataset_uri)
        stats = orchestrator.incremental_update(products)

        return {
            'statusCode': 200,
            'body': json.dumps(stats)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

**Schedule with EventBridge:**
- Create Lambda function
- Add EventBridge (CloudWatch Events) trigger
- Set schedule: `cron(0 2 * * ? *)` (daily at 2 AM UTC)

### Google Cloud Functions

```python
# main.py
import functions_framework
from scripts.kg_sync import KGSyncOrchestrator
from scripts.extract_products import extract_products_from_source
import os

@functions_framework.http
def sync_wordlift(request):
    """Google Cloud Function for scheduled sync."""

    api_key = os.environ['WORDLIFT_API_KEY']
    dataset_uri = os.environ['DATASET_URI']

    try:
        products = extract_products_from_source()
        orchestrator = KGSyncOrchestrator(api_key, dataset_uri)
        stats = orchestrator.incremental_update(products)

        return stats, 200

    except Exception as e:
        return {'error': str(e)}, 500
```

**Schedule with Cloud Scheduler:**
- Deploy Cloud Function
- Create Cloud Scheduler job
- Set schedule: `0 2 * * *` (daily at 2 AM)
- Target: Cloud Function HTTP trigger

## Option 5: Airflow (Complex Pipelines)

Best for: Complex data pipelines, multiple dependencies

```python
# dags/wordlift_sync_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def extract_products(**context):
    """Extract products from source."""
    from scripts.extract_products import extract_products_from_source
    products = extract_products_from_source()
    context['ti'].xcom_push(key='products', value=products)

def sync_to_wordlift(**context):
    """Sync products to WordLift."""
    from scripts.kg_sync import KGSyncOrchestrator
    import os

    products = context['ti'].xcom_pull(key='products')

    orchestrator = KGSyncOrchestrator(
        api_key=os.environ['WORDLIFT_API_KEY'],
        dataset_uri=os.environ['DATASET_URI']
    )

    stats = orchestrator.incremental_update(products)
    return stats

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'wordlift_kg_sync',
    default_args=default_args,
    description='Daily WordLift Knowledge Graph sync',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
)

extract_task = PythonOperator(
    task_id='extract_products',
    python_callable=extract_products,
    dag=dag,
)

sync_task = PythonOperator(
    task_id='sync_to_wordlift',
    python_callable=sync_to_wordlift,
    dag=dag,
)

extract_task >> sync_task
```

## Monitoring and Alerting

### Health Check Endpoint

Create a simple health check to monitor the sync service:

```python
# health_check.py
from flask import Flask, jsonify
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

@app.route('/health')
def health():
    """Check if last sync was successful."""

    last_sync_file = Path('/tmp/last_sync.txt')

    if not last_sync_file.exists():
        return jsonify({'status': 'unknown', 'message': 'No sync recorded'}), 503

    with open(last_sync_file, 'r') as f:
        last_sync = f.read().strip()

    last_sync_time = datetime.fromisoformat(last_sync)
    age_hours = (datetime.now() - last_sync_time).total_seconds() / 3600

    if age_hours > 25:  # Daily sync + 1 hour buffer
        return jsonify({
            'status': 'stale',
            'last_sync': last_sync,
            'age_hours': age_hours
        }), 503

    return jsonify({
        'status': 'healthy',
        'last_sync': last_sync,
        'age_hours': age_hours
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Update Health Check After Sync

```python
# In your sync script
from datetime import datetime
from pathlib import Path

def update_health_check():
    """Record successful sync time."""
    health_file = Path('/tmp/last_sync.txt')
    health_file.write_text(datetime.now().isoformat())

# Call after successful sync
stats = orchestrator.sync_products(products)
if stats['errors'] == 0:
    update_health_check()
```

### Monitoring Tools

**UptimeRobot / Pingdom:**
- Monitor health check endpoint
- Alert if endpoint returns error
- Track uptime percentage

**Datadog / New Relic:**
- Send metrics from sync script
- Track sync duration, entity counts, error rates
- Set up anomaly detection

**Slack Notifications:**

```python
import requests

def send_slack_notification(message, stats):
    """Send notification to Slack."""
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    payload = {
        'text': message,
        'attachments': [{
            'color': 'good' if stats['errors'] == 0 else 'danger',
            'fields': [
                {'title': 'Created', 'value': str(stats['created']), 'short': True},
                {'title': 'Updated', 'value': str(stats['updated']), 'short': True},
                {'title': 'Errors', 'value': str(stats['errors']), 'short': True},
            ]
        }]
    }

    requests.post(webhook_url, json=payload)
```

## Best Practices

1. **Error Handling**: Always wrap sync in try-except and log failures
2. **Idempotency**: Ensure syncs can be re-run safely without duplicates
3. **Monitoring**: Track sync success/failure and send alerts
4. **Logging**: Keep detailed logs for troubleshooting
5. **Backups**: Keep previous day's data in case rollback is needed
6. **Rate Limiting**: Respect WordLift API rate limits (use batch operations)
7. **Timezone Awareness**: Schedule in UTC to avoid DST issues
8. **Testing**: Test scheduling in dev/staging before production
9. **Secrets Management**: Never commit API keys (use environment variables)
10. **Gradual Rollout**: Start with small batches, increase over time

## Troubleshooting

### Cron not running

```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test manually
/path/to/daily_sync.sh

# Verify crontab syntax
crontab -l
```

### GitHub Actions not triggering

- Check workflow syntax (YAML validation)
- Verify cron expression (use crontab.guru)
- Check Actions tab for errors
- Ensure workflow file is in `.github/workflows/`

### Docker container exiting

```bash
# Check logs
docker logs wordlift-sync

# Check container status
docker ps -a

# Verify environment variables
docker exec wordlift-sync env | grep WORDLIFT
```

## Recommended Setup

For most users:
- **Small/Medium Sites**: Cron + shell script (simple, reliable)
- **Teams with GitHub**: GitHub Actions (easy to maintain, good visibility)
- **Production Apps**: Docker + systemd or Kubernetes (scalable, robust)
- **Enterprise**: Airflow (complex pipelines, monitoring, retries)

Start simple (cron), scale as needed.