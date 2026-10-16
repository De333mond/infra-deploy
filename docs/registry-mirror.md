# Зеркало локального registry для K3s

Образы приложений будут иметь адрес `registry.registry.svc.cluster.local:5000/<image>:<tag>`. Runner внутри Kubernetes сможет отправлять их через DNS сервиса. Для скачивания образов `containerd` на ноде нужен отдельный маршрут: Ansible записывает в `/etc/rancher/k3s/registries.yaml` зеркало на `https://<ansible_host>:32443` и сертификат внутреннего CA, затем перезапускает K3s.

CA находится в исключённом из Git каталоге `local/registry/`; если обоих файлов ещё нет, playbook создаёт их при первом запуске. Его закрытый ключ остаётся локально; сделайте резервную копию `ca.key` и `ca.crt`. При переносе на новую машину восстановите именно эти файлы до запуска playbook, иначе новый CA не подойдёт к существующему сертификату registry.

Манифесты registry находятся в `clusters/homelab/infrastructure/registry/`: сервис использует `NodePort` на порту `32443`, данные хранятся в PVC `registry-data`. Серверный TLS-сертификат подписан локальным CA и содержит имена `registry.registry.svc.cluster.local` и IP ноды. Зеркало начнёт работать, когда Flux применит манифесты registry.

```sh
cd ansible
uv run ansible-playbook playbooks/registry-mirror.yaml --ask-become-pass
```

Адрес NodePort берётся из `ansible_host`, порт задаётся переменной `registry_node_port`. Для другой ноды или порта переопределите эти значения в inventory и в манифесте Service. Перед применением манифестов в Git создайте Kubernetes Secrets `registry-tls` и `registry-auth`:

```sh
cd ansible
uv run ansible-playbook playbooks/registry-secrets.yaml --ask-become-pass
```

Пароль пользователя `registry` хранится только в `local/registry/password`. Закрытый ключ CA, серверный ключ и пароль не добавляются в Git. Сохраните резервную копию каталога `local/registry/`: без него невозможно восстановить тот же CA и учётные данные после потери управляющего компьютера. Для загрузки образов приложений отдельно понадобятся учётные данные pull в Kubernetes или в конфигурации K3s.
