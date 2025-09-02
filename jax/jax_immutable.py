import jax.numpy as jnp
import numpy

# NumPy array is immutable
x = numpy.array([1, 2, 3])
print("Original NumPy array:", x)
x[0] = 10
print("NumPy array after modification:", x)

# JAX array is immutable
x = jnp.array([1, 2, 3])
print("Original JAX array:", x)
try:
    x[0] = 10  # This will raise an error
except Exception as e:
    print("Error occurred while modifying JAX array:", e)

y = x.at[0].set(10)
print("JAX array after modification:", y)
