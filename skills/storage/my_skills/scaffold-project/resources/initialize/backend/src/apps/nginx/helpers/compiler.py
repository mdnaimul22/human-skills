from __future__ import annotations

import hashlib
import socket
from src.config import Settings, ensure_dir, exists, setup_logger, write_text

logger = setup_logger(Settings.LOG_DIR / "nginx.log", name="apps.nginx.compiler")

BOT_BLOCK_TEMPLATE = """location ~ \\.(php|aspx|jsp|cgi|env|git)$ {
    deny all;
    access_log off;
    log_not_found off;
}
location ~* /(admin|wp-admin|phpinfo|MyAdmin|phpmyadmin|sql|mysql|sdk|_ignition) {
    deny all;
    access_log off;
    log_not_found off;
}
"""


class Compiler:
    @classmethod
    def get_hash(cls) -> str:
        content = (
            cls.build_backend_site(cls.has_ssl(Settings.BACKEND_DOMAIN), cls.has_modsec())
            + cls.build_frontend_site(cls.has_ssl(Settings.FRONTEND_DOMAIN), cls.has_modsec())
            + BOT_BLOCK_TEMPLATE
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def has_modsec(cls) -> bool:
        return exists("/etc/nginx/modsecurity_includes.conf")

    @classmethod
    def get_ssl_dir(cls, domain: str) -> str | None:
        direct = f"/etc/letsencrypt/live/{domain}"
        if exists(f"{direct}/fullchain.pem") and exists(f"{direct}/privkey.pem"):
            return direct
        primary = f"/etc/letsencrypt/live/{Settings.FRONTEND_DOMAIN}"
        if exists(f"{primary}/fullchain.pem") and exists(f"{primary}/privkey.pem"):
            return primary
        return None

    @classmethod
    def has_ssl(cls, domain: str) -> bool:
        return cls.get_ssl_dir(domain) is not None

    @classmethod
    def resolve_listen_ips(cls) -> list[str]:
        ips = ["127.0.0.1"]
        try:
            pub_ip = socket.gethostbyname(Settings.FRONTEND_DOMAIN)
            if pub_ip and pub_ip != "127.0.0.1" and pub_ip not in ips:
                ips.insert(0, pub_ip)
        except Exception as e:
            logger.debug(f"Could not resolve listen ip for {Settings.FRONTEND_DOMAIN}: {e}")
        return ips

    @classmethod
    def build_ssl_listen_part(cls) -> str:
        ips = cls.resolve_listen_ips()
        h2 = " http2" if Settings.NGINX_ENABLE_HTTP2 else ""
        return "\n    ".join(f"listen {ip}:443 ssl{h2};" for ip in ips)

    @classmethod
    def build_backend_site(cls, has_ssl: bool, has_modsec: bool) -> str:
        target_host = "127.0.0.1" if Settings.API_HOST in ("0.0.0.0", "") else Settings.API_HOST
        modsec_block = (
            "modsecurity on;\n    modsecurity_rules_file /etc/nginx/modsecurity_includes.conf;"
            if has_modsec else ""
        )
        if has_ssl:
            cert_dir = cls.get_ssl_dir(Settings.BACKEND_DOMAIN) or f"/etc/letsencrypt/live/{Settings.BACKEND_DOMAIN}"
            ssl_part = (
                f"{cls.build_ssl_listen_part()}\n"
                f"    ssl_certificate {cert_dir}/fullchain.pem;\n"
                f"    ssl_certificate_key {cert_dir}/privkey.pem;\n"
                "    include /etc/letsencrypt/options-ssl-nginx.conf;\n"
                "    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;"
            )
            redirect_part = (
                f"server {{\n"
                f"    if ($host = {Settings.BACKEND_DOMAIN}) {{\n"
                f"        return 301 https://$host$request_uri;\n"
                f"    }}\n"
                f"    listen 80;\n"
                f"    server_name {Settings.BACKEND_DOMAIN};\n"
                f"    include snippets/bot_block.conf;\n"
                f"    return 404;\n"
                f"}}"
            )
        else:
            ssl_part = "listen 80;"
            redirect_part = ""

        return (
            f"upstream backend_servers {{\n"
            f"    server {target_host}:{Settings.API_PORT};\n"
            f"    keepalive 64;\n"
            f"}}\n\n"
            f"limit_req_zone $binary_remote_addr zone=api_limit_zone:{Settings.NGINX_RATE_LIMIT_ZONE_SIZE} rate={Settings.NGINX_RATE_LIMIT_RATE};\n\n"
            f"server {{\n"
            f"    server_name {Settings.BACKEND_DOMAIN};\n"
            f"    include snippets/bot_block.conf;\n\n"
            f"    {modsec_block}\n\n"
            f"    location /health {{\n"
            f"        proxy_http_version 1.1;\n"
            f"        proxy_set_header Connection \"\";\n"
            f"        proxy_pass http://backend_servers/health;\n"
            f"        proxy_set_header Host $host;\n"
            f"        proxy_set_header X-Real-IP $remote_addr;\n"
            f"    }}\n\n"
            f"    location / {{\n"
            f"        limit_req zone=api_limit_zone burst={Settings.NGINX_RATE_LIMIT_BURST} nodelay;\n\n"
            f"        proxy_http_version 1.1;\n"
            f"        proxy_set_header Connection \"\";\n"
            f"        proxy_pass http://backend_servers;\n"
            f"        proxy_set_header Host $host;\n"
            f"        proxy_set_header X-Real-IP $remote_addr;\n"
            f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            f"        proxy_set_header X-Forwarded-Proto $scheme;\n"
            f"    }}\n\n"
            f"    {ssl_part}\n"
            f"}}\n\n"
            f"{redirect_part}\n"
        )

    @classmethod
    def build_frontend_site(cls, has_ssl: bool, has_modsec: bool) -> str:
        google_block = ""
        if Settings.GOOGLE_VERIFICATION_CODE:
            google_block = (
                f"location = /google{Settings.GOOGLE_VERIFICATION_CODE}.html {{\n"
                f'        return 200 "google-site-verification: google{Settings.GOOGLE_VERIFICATION_CODE}.html";\n'
                f"        default_type text/html;\n"
                f"    }}"
            )
        modsec_block = (
            "modsecurity on;\n    modsecurity_rules_file /etc/nginx/modsecurity_includes.conf;"
            if has_modsec else ""
        )
        if has_ssl:
            cert_dir = cls.get_ssl_dir(Settings.FRONTEND_DOMAIN) or f"/etc/letsencrypt/live/{Settings.FRONTEND_DOMAIN}"
            ssl_part = (
                f"{cls.build_ssl_listen_part()}\n"
                f"    ssl_certificate {cert_dir}/fullchain.pem;\n"
                f"    ssl_certificate_key {cert_dir}/privkey.pem;\n"
                "    include /etc/letsencrypt/options-ssl-nginx.conf;\n"
                "    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;"
            )
            redirect_part = (
                f"server {{\n"
                f"    if ($host = www.{Settings.FRONTEND_DOMAIN}) {{\n"
                f"        return 301 https://$host$request_uri;\n"
                f"    }}\n"
                f"    if ($host = {Settings.FRONTEND_DOMAIN}) {{\n"
                f"        return 301 https://$host$request_uri;\n"
                f"    }}\n"
                f"    listen 80;\n"
                f"    server_name {Settings.FRONTEND_DOMAIN} www.{Settings.FRONTEND_DOMAIN};\n"
                f"    include snippets/bot_block.conf;\n"
                f"    return 404;\n"
                f"}}"
            )
        else:
            ssl_part = "listen 80;"
            redirect_part = ""

        return (
            f"server {{\n"
            f"    server_name {Settings.FRONTEND_DOMAIN} www.{Settings.FRONTEND_DOMAIN};\n"
            f"    include snippets/bot_block.conf;\n\n"
            f"    {modsec_block}\n\n"
            f"    {google_block}\n\n"
            f"    location / {{\n"
            f"        proxy_http_version 1.1;\n"
            f"        proxy_set_header Connection \"\";\n"
            f"        proxy_pass http://127.0.0.1:3000;\n"
            f"        proxy_set_header Host $host;\n"
            f"        proxy_set_header X-Real-IP $remote_addr;\n"
            f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            f"        proxy_set_header X-Forwarded-Proto $scheme;\n"
            f"    }}\n\n"
            f"    {ssl_part}\n"
            f"}}\n\n"
            f"{redirect_part}\n"
        )

    @classmethod
    def compile(cls) -> bool:
        logger.info("Compiling dynamic Nginx configuration templates...")
        ensure_dir("data/apps/nginx")
        has_ssl_backend = cls.has_ssl(Settings.BACKEND_DOMAIN)
        has_ssl_frontend = cls.has_ssl(Settings.FRONTEND_DOMAIN)
        modsec = cls.has_modsec()
        backend_site = cls.build_backend_site(has_ssl_backend, modsec)
        frontend_site = cls.build_frontend_site(has_ssl_frontend, modsec)
        try:
            write_text(f"data/apps/nginx/{Settings.BACKEND_DOMAIN}", backend_site)
            logger.info(f"Compiled backend Nginx config to data/apps/nginx/{Settings.BACKEND_DOMAIN}")
            write_text(f"data/apps/nginx/{Settings.FRONTEND_DOMAIN}", frontend_site)
            logger.info(f"Compiled frontend Nginx config to data/apps/nginx/{Settings.FRONTEND_DOMAIN}")
            write_text("data/apps/nginx/bot_block.conf", BOT_BLOCK_TEMPLATE)
            logger.info("Created bot_block.conf in data/apps/nginx/")
            return True
        except Exception as e:
            logger.error(f"Error compiling Nginx templates: {e}")
            return False
