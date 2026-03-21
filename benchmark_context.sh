#!/bin/bash

echo "=== Context Window Benchmark ==="
echo "Testing large context (16000 tokens prompt, 100 tokens generation)"
echo ""

# Generate a very large prompt (approximately 16000 tokens)
# Each word is roughly 1.3 tokens, so we need about 12000 words
BASE_TEXT="The quick brown fox jumps over the lazy dog. "
LONG_PROMPT="Please analyze the following text and provide a comprehensive summary: "

# Repeat to reach ~12000 words (~16000 tokens)
for i in {1..400}; do
  LONG_PROMPT+="$BASE_TEXT"
done

echo "Prompt length: ${#LONG_PROMPT} characters"
echo ""

# Make the request
START=$(date +%s%N)
RESULT=$(curl -s -X POST "http://localhost:8080/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen\",
    \"messages\": [{\"role\": \"user\", \"content\": $(echo "$LONG_PROMPT" | jq -Rs .)}],
    \"max_tokens\": 100
  }")
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))

# Extract metrics
PROMPT_TOKENS=$(echo "$RESULT" | jq -r '.usage.prompt_tokens')
COMPL_TOKENS=$(echo "$RESULT" | jq -r '.usage.completion_tokens')
TOTAL_TOKENS=$(echo "$RESULT" | jq -r '.usage.total_tokens')
TTFT=$(echo "$RESULT" | jq -r '.timings.prompt_ms')
GEN_MS=$(echo "$RESULT" | jq -r '.timings.predicted_ms')
TPS=$(echo "$RESULT" | jq -r '.timings.predicted_per_second')
PROMPT_TPS=$(echo "$RESULT" | jq -r '.timings.prompt_per_second')

echo "=== Results ==="
echo "Total time: ${ELAPSED}ms"
echo "Time to first token: ${TTFT}ms"
echo "Generation time: ${GEN_MS}ms"
echo ""
echo "Tokens:"
echo "  Prompt tokens: $PROMPT_TOKENS"
echo "  Completion tokens: $COMPL_TOKENS"
echo "  Total tokens: $TOTAL_TOKENS"
echo "  Context utilization: $(( (TOTAL_TOKENS * 100) / 32768 ))%"
echo ""
echo "Performance:"
echo "  Tokens/second (prompt): $PROMPT_TPS"
echo "  Tokens/second (generation): $TPS"
echo ""

# GPU memory check
echo "=== GPU Memory ==="
nvidia-smi --query-gpu=memory.total,memory.used,memory.free,utilization.gpu,utilization.memory --format=csv,noheader,nounits | awk -F', ' '{
  print "Total: " $1 " MB"
  print "Used: " $2 " MB"
  print "Free: " $3 " MB"
  print "GPU Util: " $4 "%"
  print "Memory Util: " $5 "%"
}'
