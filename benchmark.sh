#!/bin/bash

echo "=== llama.cpp Benchmark ==="
echo ""

# API endpoint
API_URL="http://localhost:8080/v1/chat/completions"

# Warmup
echo "Warmup request..."
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 5
  }' > /dev/null

echo ""
echo "=== Benchmark Tests ==="
echo ""

# Test 1: Short prompt, short generation
echo "Test 1: Short prompt, short generation (20 tokens)"
START=$(date +%s%N)
RESULT1=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 20
  }')
END=$(date +%s%N)
ELAPSED1=$(( (END - START) / 1000000 ))

TTFT1=$(echo "$RESULT1" | jq -r '.timings.prompt_ms')
TOKENS1=$(echo "$RESULT1" | jq -r '.usage.total_tokens')
GEN_MS1=$(echo "$RESULT1" | jq -r '.timings.predicted_ms')

echo "  Total time: ${ELAPSED1}ms"
echo "  Time to first token: ${TTFT1}ms"
echo "  Generation time: ${GEN_MS1}ms"
echo "  Tokens generated: $(echo "$RESULT1" | jq -r '.usage.completion_tokens')"
echo "  Prompt tokens: $(echo "$RESULT1" | jq -r '.usage.prompt_tokens')"
echo "  Total tokens: $TOKENS1"
echo ""

# Test 2: Long prompt, short generation
echo "Test 2: Long prompt, short generation (1000 words prompt, 20 tokens)"
LONG_PROMPT="The quick brown fox jumps over the lazy dog. "
LONG_PROMPT+=$(printf "%s" "$LONG_PROMPT"{1..20})  # Repeat 21 times (~1000 words)
LONG_PROMPT="Please summarize this: $LONG_PROMPT"

START=$(date +%s%N)
RESULT2=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen\",
    \"messages\": [{\"role\": \"user\", \"content\": $(echo "$LONG_PROMPT" | jq -Rs .)}],
    \"max_tokens\": 20
  }")
END=$(date +%s%N)
ELAPSED2=$(( (END - START) / 1000000 ))

TTFT2=$(echo "$RESULT2" | jq -r '.timings.prompt_ms')
PROMPT_TOKENS2=$(echo "$RESULT2" | jq -r '.usage.prompt_tokens')
GEN_MS2=$(echo "$RESULT2" | jq -r '.timings.predicted_ms')
COMPL_TOKENS2=$(echo "$RESULT2" | jq -r '.usage.completion_tokens')

echo "  Total time: ${ELAPSED2}ms"
echo "  Time to first token: ${TTFT2}ms"
echo "  Prompt tokens: $PROMPT_TOKENS2"
echo "  Generation time: ${GEN_MS2}ms"
echo "  Tokens generated: $COMPL_TOKENS2"
echo ""

# Test 3: Short prompt, long generation
echo "Test 3: Short prompt, long generation (200 tokens)"
START=$(date +%s%N)
RESULT3=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Write a detailed explanation of quantum computing"}],
    "max_tokens": 200
  }')
END=$(date +%s%N)
ELAPSED3=$(( (END - START) / 1000000 ))

TTFT3=$(echo "$RESULT3" | jq -r '.timings.prompt_ms')
GEN_MS3=$(echo "$RESULT3" | jq -r '.timings.predicted_ms')
COMPL_TOKENS3=$(echo "$RESULT3" | jq -r '.usage.completion_tokens')
TPS3=$(echo "$RESULT3" | jq -r '.timings.predicted_per_second')

echo "  Total time: ${ELAPSED3}ms"
echo "  Time to first token: ${TTFT3}ms"
echo "  Generation time: ${GEN_MS3}ms"
echo "  Tokens generated: $COMPL_TOKENS3"
echo "  Tokens per second: $TPS3"
echo ""

# GPU memory after tests
echo "=== GPU Memory After Tests ==="
nvidia-smi --query-gpu=memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits | awk -F', ' '{print "Total: " $1 " MB, Used: " $2 " MB, Free: " $3 " MB, Utilization: " $4 "%"}'

echo ""
echo "=== Summary ==="
echo "Test 1 (Short/Short): ${ELAPSED1}ms total"
echo "Test 2 (Long/Short):  ${ELAPSED2}ms total"
echo "Test 3 (Short/Long):  ${ELAPSED3}ms total, ${TPS3} tokens/sec"
