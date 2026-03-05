import os
import sys

print("=== STARTUP TEST ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"BOT_TOKEN set: {bool(os.environ.get('BOT_TOKEN'))}", flush=True)
print(f"ANTHROPIC_API_KEY set: {bool(os.environ.get('ANTHROPIC_API_KEY'))}", flush=True)

try:
    import telegram
    print(f"python-telegram-bot: {telegram.__version__}", flush=True)
except Exception as e:
    print(f"ERROR importing telegram: {e}", flush=True)
    sys.exit(1)

try:
    import anthropic
    print(f"anthropic: {anthropic.__version__}", flush=True)
except Exception as e:
    print(f"ERROR importing anthropic: {e}", flush=True)
    sys.exit(1)

print("=== ALL OK ===", flush=True)

# Тримаємо процес живим
import time
while True:
    print("heartbeat", flush=True)
    time.sleep(30)
