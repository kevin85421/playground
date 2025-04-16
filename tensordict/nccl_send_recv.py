import torch
from tensordict import TensorDict
from torch import multiprocessing as mp

def client():
    torch.distributed.init_process_group(
        "gloo",
        rank=1,
        world_size=2,
        init_method=f"tcp://localhost:10003",
    )
    td = TensorDict(
        {
            ("a", "b"): torch.randn(2),
            "c": torch.randn(2, 3),
            "_": torch.ones(2, 1, 5),
        },
        [2],
    )
    print("[client] send ", td)
    td.isend(0)

def server(queue, return_premature=True):
    torch.distributed.init_process_group(
        "gloo",
        rank=0,
        world_size=2,
        init_method=f"tcp://localhost:10003",
    )
    td = TensorDict(
        {
            ("a", "b"): torch.zeros(2),
            "c": torch.zeros(2, 3),
            "_": torch.zeros(2, 1, 5),
        },
        [2],
    )# Access nested tensor with tuple key
    out = td.irecv(1, return_premature=return_premature)
    if return_premature:
        for fut in out:
            fut.wait()
    print("[server] recv ", td)
    assert (td != 0).all()
    queue.put("yuppie")

if __name__ == "__main__":
    queue = mp.Queue(1)
    main_worker = mp.Process(
        target=server,
        args=(queue, )
        )
    secondary_worker = mp.Process(target=client)

    main_worker.start()
    secondary_worker.start()
    out = queue.get(timeout=10)
    assert out == "yuppie"
    main_worker.join()
    secondary_worker.join()