import ast
import re
from typing import List

from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH, MEDIUM


class CryptoDetector(SecurityDetector):
    """Detects weak cryptography, hardcoded secrets, and SSL bypass."""

    name = "crypto"
    description = (
        "Detects weak hashing, insecure randomness, hardcoded secrets, "
        "SSL bypass, weak ciphers, weak key sizes, ECB mode, and JWT weaknesses."
    )

    WEAK_HASHES = {'md5', 'sha1'}
    WEAK_CIPHERS = {'DES', 'Blowfish', 'RC4', 'ARC4', 'RC2', 'IDEA'}

    # RSA/DSA/EC minimum safe key sizes
    WEAK_KEY_SIZES = {
        'RSA': 2048,
        'DSA': 2048,
        'DH':  2048,
        'EC':  256,
    }

    HARDCODED_PATTERNS = [
        (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']', HIGH,
         "Hardcoded password detected. Use environment variables or secrets management."),
        (r'(?:api_key|apikey|api_secret)\s*=\s*["\'][^"\']{3,}["\']', HIGH,
         "Hardcoded API key detected. Use environment variables."),
        (r'(?:secret|secret_key)\s*=\s*["\'][^"\']{3,}["\']', HIGH,
         "Hardcoded secret detected. Use environment variables."),
        (r'(?:token|auth_token|access_token)\s*=\s*["\'][^"\']{8,}["\']', MEDIUM,
         "Potential hardcoded token detected. Rotate and use secure storage."),
        (r'(?:private_key|priv_key)\s*=\s*["\'][^"\']{10,}["\']', CRITICAL,
         "Hardcoded private key detected — critical security risk."),
    ]

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node))

        # Regex-based hardcoded secret detection
        for pattern, severity, message in self.HARDCODED_PATTERNS:
            for match in re.finditer(pattern, source_code, re.IGNORECASE):
                line = source_code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(severity, line, "hardcoded_secret", message))

        # Hardcoded AES key/IV (bytes literal with 16/24/32 bytes)
        issues.extend(self._detect_hardcoded_key(source_code))

        return issues

    # ──────────────────────────────────────────────
    # Call-level checks
    # ──────────────────────────────────────────────

    def _check_call(self, node: ast.Call) -> List[SecurityIssue]:
        results = []

        # ── hashlib.md5() / hashlib.sha1() ──
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            mod  = node.func.value.id
            func = node.func.attr

            if mod == 'hashlib' and func in self.WEAK_HASHES:
                results.extend(self._check_weak_hash_attr(node, func))

            # hashlib.new('md5', ...) / hashlib.new('sha1', ...)
            if mod == 'hashlib' and func == 'new':
                results.extend(self._check_hashlib_new(node))

            # SSL verify=False
            if mod == 'requests' and func in ('get', 'post', 'put', 'delete', 'patch', 'request', 'head'):
                for kw in node.keywords:
                    if kw.arg == 'verify' and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                        results.append(SecurityIssue(
                            HIGH, node.lineno, "ssl_bypass",
                            "'verify=False' disables SSL certificate verification — vulnerable to MITM attacks."
                        ))

            # Weak cipher: DES.new(), RC4.new(), etc.
            if func == 'new' and mod in self.WEAK_CIPHERS:
                results.append(SecurityIssue(
                    HIGH, node.lineno, "weak_cipher",
                    f"'{mod}' cipher is cryptographically broken. Use AES-256 or ChaCha20."
                ))

            # AES ECB mode: AES.new(key, AES.MODE_ECB)
            results.extend(self._check_ecb_mode(node, mod, func))

            # Insecure random
            if mod == 'random' and func in ('random', 'randint', 'choice', 'sample', 'uniform'):
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "insecure_random",
                    f"'random.{func}()' is not cryptographically secure. Use 'secrets' module."
                ))

            # urllib3 warning suppression
            if func == 'disable_warnings':
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "ssl_bypass",
                    "Disabling SSL warnings — likely hiding verify=False issues."
                ))

            # RSA/DSA/DH weak key size: RSA.generate(1024)
            results.extend(self._check_weak_key_size(node, mod, func))

        # JWT algorithms=["none"] — jwt.decode(token, algorithms=["none"])
        results.extend(self._check_jwt(node))

        return results

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _check_weak_hash_attr(self, node: ast.Call, func: str) -> List[SecurityIssue]:
        """hashlib.md5() or hashlib.sha1() without usedforsecurity=False."""
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
        """hashlib.new('md5') or hashlib.new('sha1') — string-based call."""
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
        """AES.new(key, AES.MODE_ECB) — ECB mode is deterministic and insecure."""
        if func != 'new':
            return []
        # Look for MODE_ECB in positional args or 'mode' keyword
        ecb_found = False
        for arg in node.args[1:]:  # second positional arg is mode
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
        """RSA.generate(1024) — flag keys below recommended size."""
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
        """jwt.decode(..., algorithms=['none']) — signature verification bypass."""
        if not isinstance(node.func, ast.Attribute):
            return []
        if node.func.attr != 'decode':
            return []

        for kw in node.keywords:
            if kw.arg != 'algorithms':
                continue
            # algorithms=["none"] or algorithms=["None"]
            if isinstance(kw.value, ast.List):
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant) and str(elt.value).lower() == 'none':
                        return [SecurityIssue(
                            CRITICAL, node.lineno, "jwt_none_algorithm",
                            "'algorithms=[\"none\"]' in jwt.decode() disables signature verification — "
                            "critical authentication bypass. Always specify a strong algorithm (e.g. HS256, RS256)."
                        )]
        return []

    def _detect_hardcoded_key(self, source_code: str) -> List[SecurityIssue]:
        """Detect hardcoded AES key/IV as bytes literals (16, 24, or 32 bytes)."""
        issues = []
        # Matches: key = b"exactly16bytesXX" or iv = b'someiv__'
        pattern = r'(?:key|iv|aes_key|secret_key)\s*=\s*b["\']([^"\']{10,})["\']'
        for match in re.finditer(pattern, source_code, re.IGNORECASE):
            value = match.group(1)
            if len(value) in (16, 24, 32):
                line = source_code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(
                    HIGH, line, "hardcoded_crypto_key",
                    f"Hardcoded cryptographic key/IV detected ({len(value)} bytes). "
                    "Use a secure key management system or environment variable."
                ))
        return issues