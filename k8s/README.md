# Kubernetes Pod Subdomain

## 什麼是 Pod Subdomain？

Pod subdomain 功能允許 Pod 擁有可預測的 DNS 名稱。當設定了 `hostname` 和 `subdomain` 後，Pod 可以通過以下格式訪問：

```
<hostname>.<subdomain>.<namespace>.svc.cluster.local
```

## 前提條件

1. **必須有一個 Headless Service**（`clusterIP: None`）
2. Service 的名稱必須與 Pod 的 `subdomain` 欄位相同
3. Pod 必須設定 `hostname` 和 `subdomain` 欄位

## Example: `pod_subdomain_example.yaml`

```bash
kubectl apply -f pod_subdomain_example.yaml

kubectl exec -it test-pod -- sh
ping web-1.my-service.default.svc.cluster.local
ping web-2.my-service.default.svc.cluster.local
# [Example output]:
# 64 bytes from 10.42.0.16: seq=70 ttl=64 time=0.108 ms
```

## Example: `pod.spec.subdomain` 和 headless service 不一致

* [pod_subdomain_bad_example.yaml](./pod_subdomain_bad_example.yaml) 中 headless service 的名稱是 `my-service`，但是 Pod 的 `subdomain` 是 `wrong-service-name`。

```bash
kubectl apply -f pod_subdomain_bad_example.yaml

kubectl exec -it test-bad-pod -- sh

ping web-1.wrong-service-name.default.svc.cluster.local
# [Example output]:
# ping: bad address 'web-1.wrong-service-name.default.svc.cluster.local'

ping web-1.my-service.default.svc.cluster.local
# [Example output]:
# ping: bad address 'web-1.my-service.default.svc.cluster.local'
```
