#!/bin/bash

echo "=== Concurrent Request Benchmark ==="
echo "Testing 5 concurrent requests"
echo ""

API_URL="http://localhost:8080/v1/chat/completions"

# Function to make a request
make_request() {
  local id=$1
  local START=$(date +%s%N)
  local RESULT=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"qwen\",
      \"messages\": [{\"role\": \"user\", \"content\": \"Request $id: What is the capital of France?\"}],
      \"max_tokens\": 50
    }")
  local END=$(date +%s%N)
  local ELAPSED=$(( (END - START) / 1000000 ))

  local PROMPT_TOKENS=$(echo "$RESULT" | jq -r '.usage.prompt_tokens')
  local COMPL_TOKENS=$(echo "$RESULT" | jq -r '.usage.completion_tokens')
  local TOTAL_TOKENS=$(echo "$RESULT" | jq -r '.usage.total_tokens')
  local TPS=$(echo "$RESULT" | jq -r '.timings.predicted_per_second')

  echo "Request $id: ${ELAPSED}ms, ${PROMPT_TOKENS} prompt, ${COMPL_TOKENS} completion, ${TOTAL_TOKENS} total, ${TPS} tokens/sec"
}

# Measure total time for all requests
TOTAL_START=$(date +%s%N)

# Run 5 requests in background
for i in {1..5}; do
  make_request $i &
done

# Wait for all to complete
wait

TOTAL_END=$(date +%s%N)
TOTAL_ELAPSED=$(( (TOTAL_END - TOTAL_START) / 1000000 ))

echo ""
echo "Total time for 5 concurrent requests: ${TOTAL_ELAPSED}ms"
echo "Average per request: $(( TOTAL_ELAPSED / 5 ))ms"

# Check GPU memory
echo ""
echo "=== GPU Memory ==="
nvidia-smi --query-gpu=memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits | awk -F', ' '{
  print "Total: " $1 " MB, Used: " $2 " MB, Free: " $3 " MB, Utilization: " $4 "%"
}'
