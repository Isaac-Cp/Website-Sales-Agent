import sys
import os

print("--- Integration Test ---")

try:
    print("1. Testing 'config' import...", end=" ")
    import config
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")

try:
    print("2. Testing 'spintax' import...", end=" ")
    import spintax
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")

try:
    print("3. Testing 'validator' import...", end=" ")
    import validator
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")

try:
    print("4. Testing 'llm_helper' import...", end=" ")
    import llm_helper
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")

try:
    print("5. Testing 'requests' library...", end=" ")
    import requests
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")

try:
    print("6. Testing Spintax Logic...", end=" ")
    res = spintax.spin("{A|B}")
    if res in ["A", "B"]:
        print("OK")
    else:
        print(f"FAIL (Output: {res})")
except Exception as e:
    print(f"FAIL: {e}")

print("--- Test Complete ---")
