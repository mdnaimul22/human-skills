from __future__ import annotations

import subprocess
from src.config import Settings, delete, exists, get_abs_path, get_rel_path, setup_logger

logger = setup_logger(Settings.LOG_DIR / "nginx.log", name="apps.nginx.deployer")


class Deployer:
    @classmethod
    def clean_old(cls, old_backend: str, old_frontend: str) -> None:
        logger.info(f"Cleaning up legacy Nginx configurations: {old_backend}, {old_frontend}")
        paths_to_delete = [
            f"/etc/nginx/sites-enabled/{old_backend}", f"/etc/nginx/sites-available/{old_backend}",
            f"/etc/nginx/sites-enabled/{old_frontend}", f"/etc/nginx/sites-available/{old_frontend}",
            f"data/apps/nginx/{old_backend}", f"data/apps/nginx/{old_frontend}",
        ]
        for path in paths_to_delete:
            try:
                if path.startswith("/etc/"):
                    subprocess.run(["sudo", "rm", "-f", path], capture_output=True, text=True, timeout=5)
                elif exists(path):
                    delete(path)
                logger.info(f"Cleaned up path: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup old path {path}: {e}")

    @classmethod
    def deploy(cls) -> bool:
        logger.info("Deploying dynamic Nginx configurations to system paths...")
        api_conf_src = get_abs_path(f"data/apps/nginx/{Settings.BACKEND_DOMAIN}")
        frontend_conf_src = get_abs_path(f"data/apps/nginx/{Settings.FRONTEND_DOMAIN}")
        bot_block_src = get_abs_path("data/apps/nginx/bot_block.conf")

        deployments = [
            (api_conf_src, f"/etc/nginx/sites-available/{Settings.BACKEND_DOMAIN}"),
            (frontend_conf_src, f"/etc/nginx/sites-available/{Settings.FRONTEND_DOMAIN}"),
            (bot_block_src, "/etc/nginx/snippets/bot_block.conf"),
        ]

        try:
            for src, dest in deployments:
                src_rel = get_rel_path(src)
                if not exists(src_rel):
                    logger.error(f"Source file for deployment does not exist: {src_rel}")
                    return False
                logger.info(f"Copying {src_rel} to {dest}...")
                res = subprocess.run(["sudo", "cp", src, dest], capture_output=True, text=True, timeout=10)
                if res.returncode != 0:
                    logger.error(f"Failed to copy {src_rel} to {dest}: {res.stderr}")
                    return False

            symlinks = [
                (f"/etc/nginx/sites-available/{Settings.BACKEND_DOMAIN}", f"/etc/nginx/sites-enabled/{Settings.BACKEND_DOMAIN}"),
                (f"/etc/nginx/sites-available/{Settings.FRONTEND_DOMAIN}", f"/etc/nginx/sites-enabled/{Settings.FRONTEND_DOMAIN}"),
            ]

            for target, link in symlinks:
                logger.info(f"Linking {link} -> {target}...")
                res = subprocess.run(["sudo", "ln", "-sf", target, link], capture_output=True, text=True, timeout=10)
                if res.returncode != 0:
                    logger.error(f"Failed to link for {link}: {res.stderr}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error deploying Nginx configurations: {e}")
            return False
