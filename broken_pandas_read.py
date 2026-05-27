import pandas as pd
from io import StringIO


csv_text = "id;value\n1;10\n2;20\n3;30\n"


print("BROKEN VERSION")

df = pd.read_csv(StringIO(csv_text))

print(df.head())
print(df.dtypes)

try:
    print(df["value"].mean())
except KeyError:
    print("[ERROR] Column 'value' was not created because sep was not specified.")


print("\nFIXED VERSION")

df_fixed = pd.read_csv(StringIO(csv_text), sep=";")

print(df_fixed.head())
print(df_fixed.dtypes)
print("mean:", df_fixed["value"].mean())


print("\nTEST 1: EMPTY LINE")

csv_text_2 = "id;value\n1;10\n\n3;30\n"

df_test_1 = pd.read_csv(StringIO(csv_text_2), sep=";")

print(df_test_1)
print("shape:", df_test_1.shape)


print("\nTEST 2: MISSING VALUE")

csv_text_3 = "id;value\n1;10\n2;\n3;30\n"

df_test_2 = pd.read_csv(StringIO(csv_text_3), sep=";")

print(df_test_2)
print(df_test_2.dtypes)
print("mean:", df_test_2["value"].mean())
print("missing values:")
print(df_test_2.isna().sum())