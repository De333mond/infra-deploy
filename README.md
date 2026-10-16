# Infrastructure deployment

Принятые решения и открытые вопросы: [docs/decisions.md](docs/decisions.md). Задачи по Flux CD: [docs/flux-todo.md](docs/flux-todo.md). Настройка локального registry и зеркала K3s: [docs/registry-mirror.md](docs/registry-mirror.md).

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

Создайте `local/github-token` с правами `0600`. Один fine-grained PAT для текущих задач должен иметь доступ к репозиторию `De333mond/infra-deploy` и такие разрешения:

| Разрешение репозитория | Доступ | Для чего нужно |
| --- | --- | --- |
| Administration | Read and write | Flux bootstrap создаёт deploy key; ARC регистрирует и управляет runner |
| Contents | Read and write | Flux bootstrap записывает свои манифесты в репозиторий |
| Metadata | Read-only | Базовый доступ к метаданным репозитория, требуется GitHub API |

Для classic PAT нужен scope `repo`. Затем выполните из каталога `ansible`:

```sh
ansible-playbook playbooks/flux.yaml
```

Playbook устанавливает закреплённую версию Flux CLI на сервер и запускает `flux bootstrap github` для ветки `main` и пути `clusters/homelab`. Bootstrap также обновляет манифесты и компоненты Flux в GitHub. PAT остаётся локальным; в Kubernetes хранится SSH deploy key. После запуска синхронизируйте локальный checkout с удалённой веткой.

Image Automation отслеживает digest тегов приложений и коммитит обновлённые ссылки на образы в `main` только при их изменении. Для этого Flux использует deploy key с правом записи. Настройка этого цикла описана в [docs/flux-todo.md](docs/flux-todo.md); привязки к конкретным приложениям добавляются вместе с их манифестами.
