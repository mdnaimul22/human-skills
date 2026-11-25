import ast
import re
from typing import List

from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH, MEDIUM


class CryptoDetector(SecurityDetector):
    name = "crypto"
    description = (
        "Detects weak hashing, insecure randomness, hardcoded secrets, "
        "SSL bypass, weak ciphers, weak key sizes, ECB mode, and JWT weaknesses."
    )

    WEAK_HASHES = {'md5', 'sha1'}
    WEAK_CIPHERS = {'DES', 'Blowfish', 'RC4', 'ARC4', 'RC2', 'IDEA'}

    WEAK_KEY_SIZES = {
        'RSA': 2048,
        'DSA': 2048,
        'DH': 2048,
        'EC': 256,
    }

    SECRET_VAR_RULES = (
        ({'private_key', 'priv_key'}, 10, CRITICAL, "Hardcoded private key detected — critical security risk."),
        ({'password', 'passwd', 'pwd', 'db_password', 'user_password', 'smtp_password'}, 3, HIGH,
         "Hardcoded password detected. Use environment variables or secrets management."),
        ({'api_key', 'apikey', 'api_secret', 'client_secret'}, 3, HIGH,
         "Hardcoded API key detected. Use environment variables."),
        ({'secret', 'secret_key', 'jwt_secret', 'app_secret', 'signing_secret'}, 3, HIGH,
         "Hardcoded secret detected. Use environment variables."),
        ({'token', 'auth_token', 'access_token', 'refresh_token', 'bearer_token'}, 8, MEDIUM,
         "Potential hardcoded token detected. Rotate and use secure storage."),
    )

    NON_SECRET_TOKEN_PREFIXES = (
        'eos_', 'bos_', 'pad_', 'unk_', 'sep_', 'cls_', 'mask_', 'stop_',
        'next_page_', 'page_', 'prev_page_', 'cursor_', 'csrf_',
    )

    CRYPTO_BYTES_KEY_NAMES = {
        'key', 'iv', 'aes_key', 'secret_key', 'hmac_key', 'encryption_key',
        'signing_key', 'cipher_key', 'master_key', 'enc_key', 'dec_key', 'fernet_key',
    }

    SECURITY_RANDOM_KEYWORDS = {
        'token', 'secret', 'password', 'passwd', 'pwd', 'key',
        'salt', 'nonce', 'otp', 'pin', 'csrf', 'session', 'iv', 'auth',
    }

    PLACEHOLDER_MARKERS = (
        'your_', 'your-', 'changeme', 'change_me', 'placeholder', 'example',
        'dummy', 'fake', 'sample', 'replace_me', 'todo', 'xxx', '***',
    )

    _ENV_VAR_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []
        self._walk_node(tree, issues, security_func=False)
        return issues

    def _is_security_name(self, name: str) -> bool:
        tokens = set(name.lower().split("_"))
        return bool(tokens & self.SECURITY_RANDOM_KEYWORDS)

    def _walk_node(self, node: ast.AST, issues: List[SecurityIssue], security_func: bool) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            in_sec = security_func or self._is_security_name(node.name)
            for child in ast.iter_child_nodes(node):
                self._walk_node(child, issues, in_sec)
            return

        if isinstance(node, ast.Assign):
            target_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            target_names += [t.attr for t in node.targets if isinstance(t, ast.Attribute)]
            in_sec = security_func or any(self._is_security_name(n) for n in target_names)
            for name in target_names:
                issues.extend(self._check_secret_assignment(name, node.value, node.lineno))
            for child in ast.iter_child_nodes(node):
                self._walk_node(child, issues, in_sec)
            return

        if isinstance(node, ast.AnnAssign):
            target_name = node.target.id if isinstance(node.target, ast.Name) else (
                node.target.attr if isinstance(node.target, ast.Attribute) else ""
            )
            in_sec = security_func or (bool(target_name) and self._is_security_name(target_name))
            if target_name and node.value is not None:
                issues.extend(self._check_secret_assignment(target_name, node.value, node.lineno))
            for child in ast.iter_child_nodes(node):
                self._walk_node(child, issues, in_sec)
            return

        if isinstance(node, ast.Call):
            issues.extend(self._check_call(node, security_func))
            for kw in node.keywords:
                if kw.arg:
                    issues.extend(self._check_secret_assignment(kw.arg, kw.value, node.lineno))

        for child in ast.iter_child_nodes(node):
            self._walk_node(child, issues, security_func)

    def _is_placeholder_or_non_secret(self, value: str) -> bool:
        stripped = value.strip()
        low = stripped.lower()
        if not stripped or " " in stripped:
            return True
        if stripped.startswith("<") and stripped.endswith(">"):
            return True
        if stripped.startswith("${") or stripped.startswith("$"):
            return True
        if self._ENV_VAR_RE.match(stripped):
            return True
        if low in {"string", "str", "none", "null", "true", "false", "empty", "default", "secret", "password", "token"}:
            return True
        if any(m in low for m in self.PLACEHOLDER_MARKERS):
            return True
        return False

    def _check_secret_assignment(self, var_name: str, value_node: ast.expr, lineno: int) -> List[SecurityIssue]:
        if not isinstance(value_node, ast.Constant):
            return []

        low = var_name.lower()

        if isinstance(value_node.value, bytes):
            if low in self.CRYPTO_BYTES_KEY_NAMES and len(value_node.value) in (16, 24, 32):
                return [SecurityIssue(
                    HIGH, lineno, "hardcoded_crypto_key",
                    f"Hardcoded cryptographic key/IV detected ({len(value_node.value)} bytes). "
                    "Use a secure key management system or environment variable."
                )]
            return []

        if not isinstance(value_node.value, str):
            return []

        if low.startswith(self.NON_SECRET_TOKEN_PREFIXES):
            return []

        if self._is_placeholder_or_non_secret(value_node.value):
            return []

        for names, min_len, severity, message in self.SECRET_VAR_RULES:
            if low in names and len(value_node.value) >= min_len:
                return [SecurityIssue(severity, lineno, "hardcoded_secret", message)]

        return []

    def _check_call(self, node: ast.Call, security_context: bool) -> List[SecurityIssue]:
        results = []

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            mod = node.func.value.id
            func = node.func.attr

            if mod == 'hashlib' and func in self.WEAK_HASHES:
                results.extend(self._check_weak_hash_attr(node, func))

            if mod == 'hashlib' and func == 'new':
                results.extend(self._check_hashlib_new(node))

            if mod == 'requests' and func in ('get', 'post', 'put', 'delete', 'patch', 'request', 'head'):
                for kw in node.keywords:
                    if kw.arg == 'verify' and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                        results.append(SecurityIssue(
                            HIGH, node.lineno, "ssl_bypass",
                            "'verify=False' disables SSL certificate verification — vulnerable to MITM attacks."
                        ))

            if func == 'new' and mod in self.WEAK_CIPHERS:
                results.append(SecurityIssue(
                    HIGH, node.lineno, "weak_cipher",
                    f"'{mod}' cipher is cryptographically broken. Use AES-256 or ChaCha20."
                ))

            results.extend(self._check_ecb_mode(node, mod, func))

            if security_context and mod == 'random' and func in ('random', 'randint', 'choice', 'sample', 'uniform'):
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "insecure_random",
                    f"'random.{func}()' is not cryptographically secure. Use 'secrets' module."
                ))

            if func == 'disable_warnings' and 'urllib3' in mod.lower():
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "ssl_bypass",
                    "Disabling SSL warnings — likely hiding verify=False issues."
                ))

            results.extend(self._check_weak_key_size(node, mod, func))

        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'disable_warnings':
            if 'urllib3' in ast.unparse(node.func.value).lower():
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "ssl_bypass",
                    "Disabling SSL warnings — likely hiding verify=False issues."
                ))

        results.extend(self._check_jwt(node))

        return results

    def _check_weak_hash_attr(self, node: ast.Call, func: str) -> List[SecurityIssue]:
        has_usedforsecurity_false = any(
            kw.arg == 'usedforsecurity'
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is False
            for kw in node.keywords
        )
        if not has_usedforsecurity_false:
            return [SecurityIssue(
                MEDIUM, node.lineno, "weak_hash",
                f"'hashlib.{func}()' is cryptographically weak. "
                "Use SHA-256+ for security, or pass usedforsecurity=False."
            )]
        return []

    def _check_hashlib_new(self, node: ast.Call) -> List[SecurityIssue]:
        if not node.args:
            return []
        first_arg = node.args[0]
        if not isinstance(first_arg, ast.Constant):
            return []
        algo = str(first_arg.value).lower().replace('-', '')
        if algo not in self.WEAK_HASHES:
            return []

        has_usedforsecurity_false = any(
            kw.arg == 'usedforsecurity'
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is False
            for kw in node.keywords
        )
        if has_usedforsecurity_false:
            return []

        return [SecurityIssue(
            MEDIUM, node.lineno, "weak_hash",
            f"'hashlib.new(\"{first_arg.value}\")' is cryptographically weak. "
            "Use SHA-256+ or pass usedforsecurity=False."
        )]

    def _check_ecb_mode(self, node: ast.Call, mod: str, func: str) -> List[SecurityIssue]:
        if func != 'new':
            return []
        ecb_found = False
        for arg in node.args[1:]:
            if isinstance(arg, ast.Attribute) and arg.attr == 'MODE_ECB':
                ecb_found = True
        for kw in node.keywords:
            if kw.arg == 'mode' and isinstance(kw.value, ast.Attribute) and kw.value.attr == 'MODE_ECB':
                ecb_found = True

        if ecb_found:
            return [SecurityIssue(
                HIGH, node.lineno, "weak_cipher_mode",
                f"'{mod}.new()' with ECB mode — ECB is deterministic and leaks plaintext patterns. "
                "Use AES-GCM or AES-CBC with a random IV."
            )]
        return []

    def _check_weak_key_size(self, node: ast.Call, mod: str, func: str) -> List[SecurityIssue]:
        if func != 'generate':
            return []
        min_size = self.WEAK_KEY_SIZES.get(mod)
        if min_size is None:
            return []
        if not node.args:
            return []
        first_arg = node.args[0]
        if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, int):
            return []
        key_size = first_arg.value
        if key_size < min_size:
            return [SecurityIssue(
                HIGH, node.lineno, "weak_key_size",
                f"'{mod}.generate({key_size})' — key size {key_size} is below recommended "
                f"minimum of {min_size} bits."
            )]
        return []

    def _check_jwt(self, node: ast.Call) -> List[SecurityIssue]:
        if not isinstance(node.func, ast.Attribute):
            return []
        if node.func.attr != 'decode':
            return []

        for kw in node.keywords:
            if kw.arg != 'algorithms':
                continue
            if isinstance(kw.value, ast.List):
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant) and str(elt.value).lower() == 'none':
                        return [SecurityIssue(
                            CRITICAL, node.lineno, "jwt_none_algorithm",
                            "'algorithms=[\"none\"]' in jwt.decode() disables signature verification — "
                            "critical authentication bypass. Always specify a strong algorithm (e.g. HS256, RS256)."
                        )]
        return []
