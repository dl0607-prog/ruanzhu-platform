# GitHub 自动测试配置

当前授权不包含 workflow 权限，因此 GitHub 拒绝更新 `.github/workflows/ci.yml`。推荐配置已保存在 `docs/ci-recommended.yml`，包含管理员测试密码、单元测试、启动检查和 Docker 镜像检查。

仓库维护者可在 GitHub 网页把推荐内容替换到 `.github/workflows/ci.yml`，或为用于推送的授权增加 workflow 权限。现有旧启动检查没有 ADMIN_PASSWORD，新认证配置会拒绝空密码启动，因此旧启动检查预计失败；本地40项测试已通过。不要通过恢复默认密码或关闭认证来迁就旧测试。
