import pandas as pd


df = pd.DataFrame({"x": [1, None, 3]})


print("=== BROKEN ASSERT ===")

try:
    # BUG: notna without parentheses is a method object, not a boolean result
    assert df["x"].notna, "x has nulls"
    print("[BROKEN] Test passed, but NULL exists")
except AssertionError as error:
    print("[BROKEN] Test failed:", error)


print("\n=== FIXED ASSERT ===")

try:
    assert df["x"].notna().all(), "x has nulls"
    print("[FIXED] Test passed")
except AssertionError as error:
    print("[FIXED] Test failed correctly:", error)