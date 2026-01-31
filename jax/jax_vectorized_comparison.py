import jax.numpy as jnp

array = jnp.array([-2, -1, 0, 1, 2, 2, 3])
mask = (array >= 0).astype(jnp.float32)
print(mask) # [0. 0. 1. 1. 1. 1. 1.]
