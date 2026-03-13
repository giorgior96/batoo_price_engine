import hashlib

target = "1a4016215d8bb56a94885eba473448f8"

strings_to_test = [
    "Yacht Studio Srls.",
    "yachtstudio",
    "yacht studio",
    "8fb5f8be",
    "info@yachtstudio.it",
    "http://www.yachtstudio.it",
    "www.yachtstudio.it",
    "Roma",
    "IT",
    "Yacht Studio",
    "yachtstudio.it",
    "1", "2", "3", "1234", "12345", "123456",
    # maybe it's the dealer id on boat24?
]

for s in strings_to_test:
    # Test lowercase, uppercase, original
    for variant in [s, s.lower(), s.upper()]:
        h = hashlib.md5(variant.encode('utf-8')).hexdigest()
        if h == target:
            print(f"MATCH FOUND: '{variant}'")

print("Done.")
