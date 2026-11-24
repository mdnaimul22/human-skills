# nginx.py DOX

> *`src/apps/nginx/` acts as the "Autonomous Ingress & Reverse Proxy Control Plane":*
> *It orchestrates host-level Nginx provisioning, dynamic configuration compilation, filesystem deployment, syntax verification, and service reloading.*
> *It ensures application routing (FastAPI backend and Next.js frontend), TLS/SSL certificates, ModSecurity WAF rules, and bot mitigations remain deterministic, secure, and self-healing.*

## Purpose

- Own the `src/apps/nginx` platform ingress substrate and orchestrator.
- Inspect host Nginx binary presence and provide automated package provisioning (`apt-get`) and system directory initialization when missing.
- Dynamically compile vhost configurations for backend (`api.example.com`) and frontend (`example.com`) with adaptive Let's Encrypt SSL, ModSecurity WAF integration, rate-limiting zones, and Google site verification blocks.
- Deploy generated server blocks to `/etc/nginx/sites-available/`, establish symlinks to `/etc/nginx/sites-enabled/`, and safely clean up obsolete configurations.
- Verify configuration syntax (`nginx -t`) and perform graceful service reload (`systemctl reload nginx`) with fallback restart capability.
- Manage state persistence (`data/apps/nginx/state.json`) with SHA-256 change detection to avoid unnecessary reloads during application restarts.
- Supervise backend health probes via background daemon threads.
- Keep this module-level DOX profile synchronized with `src/apps/nginx/` implementation files.

## Ownership

- `src/apps/nginx/manager.py` owns the public facade and lifecycle orchestrator (`NginxManager`).
- `src/apps/nginx/helpers/` owns the isolated sub-engine worker implementations ("internal machinery").
- `src/apps/nginx/schema/` owns all Pydantic v2 data contracts and TypeAdapters.
- `src/apps/nginx/__init__.py` owns PEP 562 lazy exports (`_LAZY_EXPORTS`, `__getattr__`).
- `nginx.py.mdx.md` owns durable notes about responsibilities, runtime contracts, side effects, key concepts, work guidance, and verification.
- **Classes:**
  - `NginxManager` (Public Facade / Orchestrator)
    - `get_config_hash() -> str`
    - `is_installed() -> bool`
    - `is_running() -> bool`
    - `get_status() -> NginxStatus`
    - `setup_and_reload() -> bool`
    - `reload() -> bool`
    - Backward-compatible aliases: `compile_configs`, `deploy_configs`, `test_and_reload`, `ensure_nginx_installed`, `ensure_system_directories`, `cleanup_old_configs`
  - `Installer` (`./helpers/installer.py`)
    - Host Nginx CLI detection, automated package installation, and system directory preparation.
    - `is_installed() -> bool`
    - `ensure_installed() -> bool`
    - `ensure_dirs() -> bool`
  - `Compiler` (`./helpers/compiler.py`)
    - Deterministic SHA-256 config hashing, SSL certificate detection, ModSecurity inspection, virtual host template generation, and zero-day HTTP/2 mitigation (`NGINX_ENABLE_HTTP2`).
    - `get_hash() -> str`
    - `has_modsec() -> bool`
    - `has_ssl(domain: str) -> bool`
    - `build_ssl_listen_part() -> str`
    - `build_backend_site(has_ssl: bool, has_modsec: bool) -> str`
    - `build_frontend_site(has_ssl: bool, has_modsec: bool) -> str`
    - `compile() -> bool`
  - `Deployer` (`./helpers/deployer.py`)
    - Filesystem sync from `data/apps/nginx/` to `/etc/nginx/`, symlink management, and obsolete domain purging.
    - `clean_old(old_backend: str, old_frontend: str) -> None`
    - `deploy() -> bool`
  - `Service` (`./helpers/service.py`)
    - Syntax validation (`nginx -t`), systemd reload/restart, service status check, and background health probes.
    - `test_syntax() -> bool`
    - `reload() -> bool`
    - `is_running() -> bool`
    - `test_and_reload() -> bool`
    - `probe_health(timeout: float = 30.0) -> bool`
    - `start_health_probe(timeout: float = 30.0) -> None`
- **Data Contracts (`src/apps/nginx/schema/models.py`):**
  - `NginxState` (Persistent state file contract for `data/apps/nginx/state.json`)
  - `NginxStatus` (Real-time operational status inspection model)
  - `VHostSpec` (Strongly-typed virtual host configuration specification)
  - `NGINX_STATE_ADAPTER` (Pydantic v2 TypeAdapter for state deserialization)
  - `NGINX_STATUS_ADAPTER` (Pydantic v2 TypeAdapter for status)
  - `VHOST_SPEC_ADAPTER` (Pydantic v2 TypeAdapter for vhost specs)
- **Top-level Functions:**
  - `get_nginx_manager() -> NginxManager`
- **Notable Constants/Configurations:**
  - `STATE_FILE = "data/apps/nginx/state.json"`
  - `BOT_BLOCK_TEMPLATE`: standard bot and exploit blocking location blocks.

## Runtime Contracts

- **Singleton Pattern:** External callers instantiate or retrieve `NginxManager` via `NginxManager()` or `get_nginx_manager()`.
- **Change Detection & Skip Logic:**
  - The orchestrator computes SHA-256 digest of configured domain names, ports, rate-limit settings, and Google verification codes.
  - If existing `state.json` matches the current hash AND all deployed system files exist in `/etc/nginx/`, deployment and reloads are safely skipped.
- **Fail-Fast Safety Gate:**
  - `test_syntax()` (`sudo nginx -t`) runs before any `systemctl reload` is triggered.
  - If syntax verification fails, reload is aborted immediately, preserving the live, functioning Nginx state without downtime.
- **Network Routing & Bind Resolution:**
  - The upstream backend and health probe dynamically resolve `target_host = "127.0.0.1" if Settings.API_HOST in ("0.0.0.0", "") else Settings.API_HOST`, avoiding non-routable bind address issues during HTTP client calls.

## Key Concepts

- **Sub-Engine Separation:**
  - `Installer` handles OS package management and folder scaffolding.
  - `Compiler` operates purely on string formatting and config validation without executing shell scripts.
  - `Deployer` isolates privileged filesystem mutations (`sudo cp`, `sudo ln -sf`).
  - `Service` isolates process supervisor operations (`systemctl`, `nginx -t`).
- **Zero Inline Comments Rule:** Implementation code contains no inline comments or docstrings; self-documenting type annotations and method names are strictly enforced.
- **Token Efficiency:** Minimal line breaks in signatures and strict type safety across all boundaries.

## Work Guidance & Troubleshooting

- **Configuration Changes:** Modify domain names or rate limits in `.env` / `src/config/settings.py`. Calling `NginxManager.setup_and_reload()` automatically detects the hash difference, prunes old files, and deploys the new vhost configurations.
- **SSL Certificate Provisioning:** When certbot generates certificates in `/etc/letsencrypt/live/<domain>/`, `Compiler.has_ssl()` returns `True`, switching the vhost template from bootstrap port 80 to port 443 SSL with automatic HTTPS redirection.
- **ModSecurity Integration:** When `/etc/nginx/modsecurity_includes.conf` is detected on the host, WAF rules are automatically attached to the server blocks.

## Verification & Tests

- **Unit Tests:** Located in `tests/apps/nginx/`:
  - `test_nginx_schema.py`: Validates Pydantic v2 adapters, defaults, and boundary constraints.
  - `test_nginx_installer.py`: Validates binary discovery, apt auto-install, and directory creation.
  - `test_nginx_compiler.py`: Validates deterministic hash generation, SSL/ModSec conditional blocks, and template compilation.
  - `test_nginx_deployer.py`: Validates filesystem deployment, symlinks, and legacy config cleanup.
  - `test_nginx_service.py`: Validates `nginx -t` syntax check, systemd reload fallback, and health probing.
  - `test_nginx_manager.py`: Validates singleton lifecycle, skip logic, end-to-end orchestration, and backward-compatible aliases.
- **Run Tests:**
  ```bash
  PYTHONPATH=. pytest tests/apps/nginx/ -v --durations=0
  ```
- **AST Architecture Lint:**
  ```bash
  human-skills '{"tool_name": "linter", "tool_args": {"scan_path": "src/apps/nginx"}}'
  ```

## Child DOX Index

- [Schema Models](./helpers/schema.py)
- [Installer Engine](./helpers/installer.py)
- [Compiler Engine](./helpers/compiler.py)
- [Deployer Engine](./helpers/deployer.py)
- [Service Engine](./helpers/service.py)
- [Manager Orchestrator](./manager.py)
