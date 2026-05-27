precipitation_mm = 12.0

print("=== BROKEN VERSION ===")

# mm -> m
precipitation_m = precipitation_mm / 1000

# BUG: incorrect reverse conversion
precipitation_mm_wrong = precipitation_m * 1000 * 1000

print("original mm:", precipitation_mm)
print("wrong mm:", precipitation_mm_wrong)

print("\n=== FIXED VERSION ===")

precipitation_mm = 12.0

precipitation_m = precipitation_mm / 1000

precipitation_mm_back = precipitation_m * 1000

print("restored mm:", precipitation_mm_back)

assert abs(
    precipitation_mm_back - precipitation_mm
) < 1e-9, "Unit conversion mismatch!"

print("[OK] unit conversion validated")