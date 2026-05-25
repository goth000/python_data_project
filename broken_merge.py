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


print("\nFIXED VERSION")


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