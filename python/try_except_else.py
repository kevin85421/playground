print("Case 1: No exception raised in `try`")
try:
    print("try")
except Exception as e:
    print("except")
else:
    print("else")

print("Case 2: Exception raised in `try`")
try:
    raise Exception("raise exception in `try`")
except Exception as e:
    print("except")
else:
    print("else")
