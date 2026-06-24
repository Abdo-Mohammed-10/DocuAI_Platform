from prometheus_client import start_http_server
import time

def main():
    start_http_server(9101)
    print("📊 Celery metrics server running on :9101/metrics")
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()