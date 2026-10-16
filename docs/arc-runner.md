# GitHub Actions runner

ARC установлен через Flux: controller в `arc-systems`, runner scale set в `arc-runners`. Scale set привязан к `De333mond/infra-deploy`; его имя для `runs-on` — `homelab-runners`. В простое runner pod не запущен (`minRunners: 0`), одновременно запускается максимум один (`maxRunners: 1`). Listener и controller работают постоянно.

Перед публикацией манифестов подготовьте Secret с текущим PAT и ConfigMap с CA registry. Из каталога `ansible`:

```sh
uv run ansible-playbook playbooks/arc-secrets.yaml --ask-become-pass
```

Playbook читает игнорируемые Git файлы `local/github-token` и `local/registry/ca.crt`. PAT должен иметь для репозитория разрешение `Administration: Read and write`. Секрет `arc-github-auth` создаётся в `arc-runners` с ключом `github_token`; CA используется Docker daemon внутри runner pod для адреса `registry.registry.svc.cluster.local:5000`. Для публикации образов workflow также должен выполнить `docker login` с учётными данными registry.

После публикации манифестов проверьте:

```sh
sudo kubectl -n arc-systems get helmrelease,pods
sudo kubectl -n arc-runners get helmrelease,autoscalingrunnersets,autoscalinglisteners,pods
```

В GitHub проверьте **Settings → Actions → Runners**. Для тестового workflow укажите `runs-on: homelab-runners`.

После переноса репозитория в организацию смените `githubConfigUrl` в `clusters/homelab/infrastructure/arc/runners.yaml` и обновите PAT с правами управления runners организации. Текущий runner scale set привязан только к этому репозиторию.
