#!/usr/bin/env python3
import requests
import time
import threading
import json

API_URL = "http://localhost:8080/v1/chat/completions"

results_lock = threading.Lock()
results_list = []


def make_request(request_id):
    """Make a single request and record timing"""
    start = time.time()
    response = requests.post(
        API_URL,
        json={
            "model": "qwen",
            "messages": [
                {
                    "role": "user",
                    "content": f"Request {request_id}: What is the capital of France?",
                }
            ],
            "max_tokens": 50,
        },
    )
    elapsed = (time.time() - start) * 1000

    data = response.json()
    usage = data.get("usage", {})
    timings = data.get("timings", {})

    result = {
        "id": request_id,
        "elapsed_ms": elapsed,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "tps": timings.get("predicted_per_second", 0),
    }

    with results_lock:
        results_list.append(result)

    print(
        f"  Request {request_id}: {elapsed:.0f}ms, {usage.get('completion_tokens', 0)} tokens, {timings.get('predicted_per_second', 0):.2f} tps"
    )


def main():
    print("=" * 60)
    print("Concurrent Benchmark - 5 Parallel Requests")
    print("=" * 60)

    # Warmup
    print("\nWarmup...")
    requests.post(
        API_URL,
        json={
            "model": "qwen",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        },
    )

    print("\nRunning 5 concurrent requests...")
    start = time.time()

    threads = []
    for i in range(1, 6):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total_elapsed = (time.time() - start) * 1000

    print(f"\nTotal time for 5 concurrent requests: {total_elapsed:.0f}ms")
    print(f"Average per request: {total_elapsed / 5:.0f}ms")

    # Calculate throughput
    total_tokens = sum(r["completion_tokens"] for r in results_list)
    avg_tps = sum(r["tps"] for r in results_list) / len(results_list)

    print(f"Total tokens generated: {total_tokens}")
    print(f"Average tokens/sec: {avg_tps:.2f}")
    print(f"Throughput: {total_tokens / (total_elapsed / 1000):.2f} tokens/sec overall")


if __name__ == "__main__":
    main()
