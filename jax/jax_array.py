import jax.numpy as jnp

x = jnp.arange(5)
print("JAX array:", x)
print("Devices:", x.devices())
print("Sharding:", x.sharding)