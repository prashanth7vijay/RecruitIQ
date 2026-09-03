$root = "D:\Project\recruitiq"

Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; flask run"

Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; celery -A app.workers.worker_entrypoint worker --loglevel=info --pool=solo"