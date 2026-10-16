# Infrastructure deployment

Принятые решения и открытые вопросы: [docs/decisions.md](docs/decisions.md). Задачи по Flux CD: [docs/flux-todo.md](docs/flux-todo.md).

Ansible использует локальный inventory как конфиг подключения к серверу. При первом запуске создайте его из примера и укажите адрес сервера, SSH-пользователя, порт и при необходимости путь к SSH-ключу:

```sh
cp ansible/inventory/hosts.example.yaml ansible/inventory/hosts.yaml
```

Inventory исключён из Git и сохраняется после `git pull`. Для новой машины сначала укажите существующего пользователя с правом `sudo` (например, `root`). Роль bootstrap создаёт пользователя `deploy`; для последующих запусков переключите `ansible_user` на него, когда настроите ему SSH-доступ и `sudo`.

Установите зависимости из `ansible/pyproject.toml`, затем запускайте из каталога `ansible`:

```sh
cd ansible
ansible-playbook playbooks/bootstrap.yaml
ansible-playbook playbooks/k3s.yaml
```

После `git pull` запустите нужные playbook повторно. Если для `sudo` нужен пароль, добавьте `--ask-become-pass` к команде `ansible-playbook`.

Исходные секреты для первоначальной настройки и будущий закрытый ключ age храните в `local/` (`mkdir -m 700 local`); каталог исключён из Git.

Для первоначальной установки Flux создайте `local/github-token` с правами `0600`. Для fine-grained GitHub PAT владельца существующего репозитория `De333mond/infra-deploy` нужны `Administration: Read and write`, `Contents: Read and write`, `Metadata: Read-only`; классическому токену достаточно scope `repo`. Затем выполните из каталога `ansible`:

```sh
ansible-playbook playbooks/flux.yaml
```

Playbook устанавливает закреплённую версию Flux CLI на сервер, запускает `flux bootstrap github` для ветки `main` и пути `clusters/homelab`, а также проверяет контроллеры. Bootstrap создаёт коммит с манифестами Flux в GitHub; после первого запуска синхронизируйте локальный checkout с удалённой веткой. PAT не сохраняется в Kubernetes; там хранится SSH deploy key с доступом к репозиторию только на чтение. Сейчас устанавливаются только `source-controller` и `kustomize-controller`; остальные компоненты добавим вместе с соответствующими ресурсами.
