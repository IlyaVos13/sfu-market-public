"""Запустить уже собранный API, проверить контракт и освободить процесс."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

root = Path(__file__).resolve().parents[1]
dll = root / "backend/SfuMarket.Api/bin/Release/net10.0/SfuMarket.Api.dll"
if not dll.is_file():
    raise SystemExit("Сначала выполните dotnet build backend/SfuMarket.Api -c Release")

env = dict(os.environ, ASPNETCORE_URLS="http://127.0.0.1:0")
log_path = root / "tests/health-check.log"
with log_path.open("w+") as log:
    process = subprocess.Popen([os.environ.get("DOTNET", "dotnet"), str(dll)],
                               cwd=dll.parent, env=env, stdout=log, stderr=log)
    try:
        deadline = time.monotonic() + 30
        url = None
        while time.monotonic() < deadline:
            log.seek(0)
            for line in log.read().splitlines():
                if "Now listening on: http://127.0.0.1:" in line:
                    url = line.split("Now listening on: ", 1)[1].strip()
            if url:
                break
            if process.poll() is not None:
                raise RuntimeError("API завершился до запуска; см. tests/health-check.log")
            time.sleep(0.1)
        if not url:
            raise TimeoutError("API не запустился за 30 секунд")
        with urllib.request.urlopen(url + "/health", timeout=5) as response:
            assert response.status == 200
            assert response.headers.get_content_type() == "application/json"
            assert json.load(response) == {"status": "ok", "service": "sfu-market", "version": "0.1.0"}
        try:
            urllib.request.urlopen(url + "/unknown", timeout=5)
        except urllib.error.HTTPError as error:
            assert error.code == 404, error.code
        else:
            raise AssertionError("Неизвестный адрес должен возвращать 404")
        print("PASS: HTTP 200, JSON content-type, health contract, HTTP 404")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
