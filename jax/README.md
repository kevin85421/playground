# JAX

## JAX array 是 immutable

```sh
python3 jax_immutable.py

# [Example output]:
# Original NumPy array: [1 2 3]
# NumPy array after modification: [10  2  3]
# Original JAX array: [1 2 3]
# Error occurred while modifying JAX array: JAX arrays are immutable and do not support in-place item assignment. Instead of x[idx] = y, use x = x.at[idx].set(y) or another .at[] method: https://docs.jax.dev/en/latest/_autosummary/jax.numpy.ndarray.at.html
# JAX array after modification: [10  2  3]
```

* 多數情況 JAX 可以視為 NumPy array 的 drop-in replacement，但是有一點不同是，NumPy array 為 mutable，但是 JAX array 為 immutable。
  ```python
  # 合法
  x = numpy.array([1, 2, 3])
  x[0] = 10

  # 不合法
  x = jnp.array([1, 2, 3])
  x[0] = 10
  
  # 使用 x.at[0].set(10) 回傳一個 updated copy
  y = x.at[0].set(10)
  ```

## JAX array

```sh
python3 jax_array.py

# [Example output]:
# JAX array: [0 1 2 3 4]
# Devices: {CpuDevice(id=0)}
# Sharding: SingleDeviceSharding(device=CpuDevice(id=0), memory_kind=device)
```
* 一個 JAX array 可以被分成多個 shards 放在多個 devices，此例子為一個只在單一 CPU 上的 JAX array。