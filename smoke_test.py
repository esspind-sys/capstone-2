from bedrock_client import call_claude

result = call_claude("Say hello in one sentence.")
print("Text:", result["text"])
print("Input tokens:", result["input_tokens"])
print("Output tokens:", result["output_tokens"])