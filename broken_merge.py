import pandas as pd


left = pd.DataFrame({
    "id": [1, 1, 2],
    "value": [10, 11, 20]
})

right = pd.DataFrame({
    "id": [1, 1, 2],
    "name": ["A", "A_dup", "B"]
})


print("LEFT")
print(left)

print("\nRIGHT")
print(right)


merged = left.merge(right, on="id", how="left")

print("\nMERGED")
print(merged)

print("\nROWS:")
print(len(left), "->", len(merged))

print("\nWHY ROWS INCREASED")
print("The key id=1 is duplicated in both tables, so the join creates")
print("all matching combinations: 2 left rows x 2 right rows = 4 rows.")
print("This can inflate sum and count metrics and distort averages.")

print("\nTWO FIX STRATEGIES")
print("1. Make the reference key unique when duplicates are data errors.")
print("2. Aggregate the reference to one meaningful row per key.")
print("Use validate='many_to_one' to reject an unsafe join.")

print("\nFIXED VERSION: UNIQUE REFERENCE + CARDINALITY VALIDATION")

right_fixed = right.drop_duplicates(subset=["id"])

merged_fixed = left.merge(
    right_fixed,
    on="id",
    how="left",
    validate="many_to_one"
)

print(merged_fixed)

print("\nROWS:")
print(len(left), "->", len(merged_fixed))

print("\nMETRIC CHECK")
print("sum before join:", left["value"].sum())
print("sum after unsafe join:", merged["value"].sum())
print("sum after fixed join:", merged_fixed["value"].sum())
