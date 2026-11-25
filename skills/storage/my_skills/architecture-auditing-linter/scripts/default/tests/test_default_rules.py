import ast
import sys
import types
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from default.base import FileContext
from default.code_complexity import CodeComplexityRule
from default.code_duplication import CodeDuplicationRule
from default.env_config import EnvConfigRule
from default.future_annotations import FutureAnnotationsRule
from default.helpers_usage import HelpersUsageRule
from default.import_hygiene import ImportHygieneRule
from default.kill_switch import KillSwitchRule
from default.logging_rule import LoggingRule
from default.manual_io import ManualIORule
from default.memory_efficiency import MemoryEfficiencyRule
from default.path_safety import PathSafetyRule
from default.pythonic_standards import PythonicStandardsRule
from default.section_comments import SectionCommentsRule
from default.security.crypto_risk import CryptoDetector
from default.security.deserialization_risk import DeserializationDetector
from default.security.info_disclosure_risk import InfoDisclosureDetector
from default.security.injections_risk import InjectionDetector
from default.security.network_risk import NetworkDetector
from default.security.resource_risks import ResourceDetector
from default.security_rule import SecurityRule
from default.silent_exceptions import SilentExceptionsRule
from default.type_safety import TypeSafetyRule
from default.unused_dependencies import UDBDMethodRule


def _run(rule_cls, code: str, fname: str = "src/services/app.py", root: str = "."):
    ctx = FileContext(Path(fname), Path(root), set(), code)
    return rule_cls(ctx).run(ast.parse(code))


def _sec(detector_cls, code: str):
    return detector_cls().detect(ast.parse(code), code)


def test_file_context_scoping():
    c_app_helper = FileContext(Path("src/apps/auth/helpers/guards.py"), Path("."), set(), "")
    assert not c_app_helper.is_helpers_file

    c_db_helper = FileContext(Path("src/db/helpers/query.py"), Path("."), set(), "")
    assert not c_db_helper.is_helpers_file

    c_global_helper = FileContext(Path("src/helpers/process_env.py"), Path("."), set(), "")
    assert c_global_helper.is_helpers_file

    c_reloader = FileContext(Path("src/config/reloader.py"), Path("."), set(), "")
    assert c_reloader.is_config_file

    c_test = FileContext(Path("src/e2e/test_login.py"), Path("."), set(), "")
    assert c_test.is_test_file


def test_path_safety_fp_and_tp():
    fp_code = '''
"""Never write to /tmp/ directly."""
from src.config import list_files

@router.get("/tmp/files")
def handler(redis, repo, resolver):
    p = "data/tmp/out.json"
    ok = redis.exists("k")
    has_user = repo.exists(1)
    ip = resolver.resolve("example.com")
    dirs = [e for e in list_files("data", "*") if e.is_dir()]
    create_bucket("logs", exist_ok=True)
    return p, ok, has_user, ip, dirs
'''
    v_fp, _ = _run(PathSafetyRule, fp_code)
    assert v_fp == []

    tp_code = '''
import os
from pathlib import Path
p = Path("/tmp/evil.txt")
p.exists()
os.path.exists("a")
os.makedirs("dir", exist_ok=True)
'''
    v_tp, _ = _run(PathSafetyRule, tp_code)
    assert any("pathlib" in v for v in v_tp)
    assert any("system '/tmp'" in v for v in v_tp)
    assert any("Direct '.exists()'" in v for v in v_tp)
    assert sum("os.path.exists" in v for v in v_tp) == 1
    assert any("exist_ok=True" in v for v in v_tp)


def test_code_complexity_fp_and_tp():
    fp_code = '''
def route(x, lock, session):
    with lock:
        with session:
            if x == 1:
                return 1
            elif x == 2:
                return 2
            elif x == 3:
                return 3
            elif x == 4:
                return 4
            elif x == 5:
                return 5
            elif x == 6:
                return 6
            return 0
'''
    v_fp, _ = _run(CodeComplexityRule, fp_code)
    assert v_fp == []

    tp_code = '''
def deep(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return 1
'''
    v_tp, _ = _run(CodeComplexityRule, tp_code)
    assert any("Deep nesting depth of 5" in v for v in v_tp)


def test_code_duplication_fp_and_tp():
    fp_code = '''
class UserService:
    def __init__(self, db, cache, mailer):
        self.db = db
        self.cache = cache
        self.mailer = mailer

class OrderProcessor:
    def __init__(self, repo, gateway, logger):
        self.repo = repo
        self.gateway = gateway
        self.logger = logger

async def get_user(uid, svc):
    logger.info(f"fetch {uid}")
    res = await svc.fetch_user(uid)
    return res

async def delete_invoice(iid, bill):
    logger.warning(f"delete {iid}")
    res = await bill.purge_invoice(iid)
    return res
'''
    v_fp, _ = _run(CodeDuplicationRule, fp_code)
    assert v_fp == []

    tp_code = '''
def validate_url_a(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValidationError("URL cannot be empty")
    return v

def validate_url_b(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValidationError("Empty url")
    return raw
'''
    v_tp, _ = _run(CodeDuplicationRule, tp_code)
    assert len(v_tp) == 1
    assert "DRY Violation" in v_tp[0]


def test_pythonic_standards_fp_and_tp():
    fp_code = '''
class LightHouse:
    pass
class Light_House:
    pass
class API_Client:
    pass
class GoogleTokenPayload:
    pass
class _InternalRepo:
    def list(self):
        return []
    @property
    def id(self):
        return 1
def get_governance_gateway():
    pass
def session_manager():
    pass
def _get_user_by_id():
    pass
'''
    v_fp, _ = _run(PythonicStandardsRule, fp_code)
    assert v_fp == []

    tp_code = '''
class Light_House_Extra:
    pass
class light_house_extra:
    pass
class lighthouseextra:
    pass
class GovernanceMCPGateway:
    pass
class VeryLongExcessiveClassName:
    pass
def list():
    return []
def Render_Server_Instructions():
    pass
def render_server_instructions_extra():
    pass
def a_b_c_d_e():
    pass
'''
    v_tp, _ = _run(PythonicStandardsRule, tp_code)
    assert any("Light_House_Extra" in v and "underscores" in v for v in v_tp)
    assert any("light_house_extra" in v and "underscores" in v for v in v_tp)
    assert any("lighthouseextra" in v and "PascalCase" in v for v in v_tp)
    assert any("GovernanceMCPGateway" in v and "consecutive uppercase" in v for v in v_tp)
    assert any("VeryLongExcessiveClassName" in v and "20-character limit" in v for v in v_tp)
    assert any("Function name 'list' shadows" in v for v in v_tp)
    assert any("Render_Server_Instructions" in v and "snake_case" in v for v in v_tp)
    assert any("render_server_instructions_extra" in v and "25-character limit" in v for v in v_tp)
    assert any("a_b_c_d_e" in v and "underscores" in v for v in v_tp)


def test_unused_dependencies_fp_and_tp():
    fp_code = '''
class UserSchema:
    @field_validator("email")
    @classmethod
    def _validate_email(cls, v):
        return v

    def run(self):
        def _cb(x):
            return x + 1
        return list(map(_cb, [1, 2]))
'''
    v_fp, _ = _run(UDBDMethodRule, fp_code)
    assert v_fp == []

    tp_code = '''
class Service:
    def _never_used(self):
        return 42
    def run(self):
        return 1
'''
    v_tp, _ = _run(UDBDMethodRule, tp_code)
    assert len(v_tp) == 1
    assert "_never_used" in v_tp[0]


def test_manual_io_fp_and_tp():
    fp_cfg, _ = _run(ManualIORule, 'with open("a") as f:\n    pass\n', fname="src/config/reloader.py")
    assert fp_cfg == []

    fp_pil, _ = _run(ManualIORule, 'from PIL.Image import open\nimg = open(buf)\n')
    assert fp_pil == []

    tp_with, _ = _run(ManualIORule, 'with open("a.txt") as f:\n    data = f.read()\n')
    assert len(tp_with) == 1


def test_memory_efficiency_fp_and_tp():
    fp_code = '''
s = ",".join([str(i) for i in range(5)])
val = np.sum([x for x in arr])
for item in items:
    lbl = item
    lbl += "!"
class ORMModel:
    pass
class User(ORMModel):
    def get(self, k):
        return k
out = model.model_dump(by_alias=True).get("userId")
'''
    v_fp, _ = _run(MemoryEfficiencyRule, fp_code)
    assert v_fp == []

    tp_code = '''
from pydantic import BaseModel
class User(BaseModel):
    def get(self, k):
        return k
total = sum([x for x in range(10)])
buf = ""
for x in range(10):
    buf += "a"
v = user.model_dump().get("id")
'''
    v_tp, _ = _run(MemoryEfficiencyRule, tp_code)
    assert len(v_tp) == 4


def test_helpers_usage_fp_and_tp():
    fp_code = '''
async def poll():
    while True:
        await asyncio.sleep(5)
'''
    v_fp, _ = _run(HelpersUsageRule, fp_code)
    assert v_fp == []

    tp_code = '''
from datetime import datetime
now = datetime.now()
for _ in range(3):
    try:
        call()
    except Exception:
        time.sleep(1)
'''
    v_tp, _ = _run(HelpersUsageRule, tp_code)
    assert len(v_tp) == 2
    assert "get_now_utc" in v_tp[0]


def test_silent_exceptions_fp_and_tp():
    fp_code = '''
class Profile:
    @model_validator(mode="after")
    def check(self):
        raise ValueError("bad")
    def __getitem__(self, k):
        raise KeyError(k)

def run():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
'''
    v_fp, _ = _run(SilentExceptionsRule, fp_code)
    assert v_fp == []

    tp_code = '''
def bad():
    try:
        do_work()
    except Exception:
        pass
    raise ValueError("oops")
'''
    v_tp, _ = _run(SilentExceptionsRule, tp_code)
    assert len(v_tp) == 2


def test_import_hygiene_fp_and_tp():
    v_fp, _ = _run(ImportHygieneRule, "from .parser import parse_html\nfrom .formatter import fmt\n")
    assert v_fp == []

    v_tp, _ = _run(ImportHygieneRule, "import imp\nfrom cgi import escape\nfrom foo import *\n")
    assert len(v_tp) == 3


def test_type_safety_fp_and_tp():
    fp_code = '''
from sqlalchemy import cast
from pydantic import field_validator, JsonValue

class Item:
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return NotImplemented
        return True

    @field_validator("t", mode="before")
    @classmethod
    def norm(cls, v: JsonValue) -> str | None:
        if isinstance(v, str):
            return v.strip() or None
        return None

def check(res):
    if isinstance(res, BaseException):
        raise res
    q = cast(object, col)
'''
    v_fp, _ = _run(TypeSafetyRule, fp_code)
    assert v_fp == []

    tp_code = '''
from typing import Any, cast
def bad(x: Any, y: object) -> None:
    if isinstance(x, dict):
        pass
    z = getattr(x, "a")
    w = cast(object, x)
'''
    v_tp, _ = _run(TypeSafetyRule, tp_code)
    assert len(v_tp) >= 5


def test_env_config_logging_kill_switch():
    v_env_fp, adv_fp = _run(
        EnvConfigRule,
        'class Settings:\n    API_PORT: int = Field(default=8000)\n    LOG_DIR: str = Field(default="logs")\n',
        fname="src/config/settings.py",
    )
    assert v_env_fp == []
    assert adv_fp == []

    v_env_h, _ = _run(EnvConfigRule, 'import os\nx = os.getenv("A", "b")\n', fname="src/helpers/env.py")
    assert v_env_h == []

    v_env_app_h, _ = _run(EnvConfigRule, 'import os\nx = os.getenv("A", "b")\n', fname="src/apps/auth/helpers/guards.py")
    assert len(v_env_app_h) == 2

    v_log_fp, _ = _run(LoggingRule, "from typing import TYPE_CHECKING\nfrom logging import Logger\nif TYPE_CHECKING:\n    import logging\n")
    assert v_log_fp == []

    v_ks_fp, _ = _run(KillSwitchRule, "helpers.kill_pid(8000)\nuvicorn.run(app)\n", fname="main.py")
    assert v_ks_fp == []

    v_ks_uds, _ = _run(KillSwitchRule, 'uvicorn.run(app, uds="/var/run/app.sock")\n', fname="main.py")
    assert v_ks_uds == []


def test_security_detectors_fp_and_tp():
    assert _sec(InjectionDetector, 'msg = f"Failed to create user {uid}"\nx = "Select a file " + name\n"{a}".format_map({"a": 1})\nfrom re import compile\ncompile("a")\nfrom xml.etree.ElementTree import Element, tostring\nre.sub(r"\\r\\n", "", header)\n') == []
    assert len(_sec(InjectionDetector, 'cursor.execute(f"SELECT * FROM users WHERE id = {uid}")\n')) == 1

    assert _sec(InfoDisclosureDetector, 'logging.info("Token refreshed")\nif token == None: pass\nif password == "": pass\nassert book.author\nasyncio.run(main(), debug=True)\nlogger.error(traceback.format_exc())\n') == []
    assert len(_sec(InfoDisclosureDetector, 'logging.info(f"pw={user.password}")\nif password == expected: pass\nassert user.is_admin\napp.run(debug=True)\n')) == 4

    assert _sec(CryptoDetector, 'eos_token = "<|endoftext|>"\ncache_key = b"session:user:001"\njitter = random.uniform(0.5, 1.5)\nvalidator.disable_warnings()\n# password = "hardcoded123"\n') == []
    assert len(_sec(CryptoDetector, 'password = "SuperSecret123!"\naes_key = b"0123456789abcdef"\ntoken = random.choice("abc")\nurllib3.disable_warnings()\n')) == 4

    assert _sec(NetworkDetector, 'requests.get(Settings.API_URL)\nrequests.get(f"{Settings.API_URL}/v1")\nsvg = "http://www.w3.org/2000/svg"\nollama = "http://ollama:11434"\nflask.redirect(url_for("home"))\n') == []
    assert len(_sec(NetworkDetector, 'requests.get(user_url)\nurl = "http://public.api.io/v1"\nflask.redirect(next_url)\n')) == 3

    assert _sec(DeserializationDetector, 'yaml.load(data, yaml.SafeLoader)\nyaml.load(data, Loader=yaml.FullLoader)\n') == []
    assert len(_sec(DeserializationDetector, 'yaml.load(data)\npickle.loads(raw)\n')) == 2

    assert _sec(ResourceDetector, 'analyzer.extract()\ncap.read()\nf.read(size=1024)\nre.compile(r"(foo|bar)+")\nre.compile(r"[0-9]+(?:\\.[0-9]+)*")\nre.compile(r"(union(\\s|%20)+select)")\n') == []
    assert len(_sec(ResourceDetector, 'with zipfile.ZipFile(p) as zf:\n    zf.extractall()\nwith open("a") as f:\n    f.read()\nre.compile(r"(a+)+")\nre.compile(r"(a|ab)+")\n')) == 4


def test_security_rule_loads_resource_detector():
    ctx = FileContext(Path("src/app.py"), Path("."), set(), "")
    rule = SecurityRule(ctx)
    names = {d.name for d in rule._detectors}
    assert "resource" in names
    assert len(names) == 6


def test_import_graph_ignores_docstrings(tmp_path):
    if "helpers" not in sys.modules:
        m_pkg = types.ModuleType("helpers")
        m_tool = types.ModuleType("helpers.tool")
        class Tool:
            def __init__(self, args=None):
                self.args = args or {}
        class Response:
            def __init__(self, message="", break_loop=False):
                self.message = message
                self.break_loop = break_loop
        m_tool.Tool = Tool
        m_tool.Response = Response
        sys.modules["helpers"] = m_pkg
        sys.modules["helpers.tool"] = m_tool

    from linter import Linter
    (tmp_path / "mod_a").mkdir()
    (tmp_path / "mod_b").mkdir()
    (tmp_path / "mod_a" / "a.py").write_text('import mod_b\n"""\nfrom mod_a import x\n"""\n')
    (tmp_path / "mod_b" / "b.py").write_text('"""\nfrom mod_a import something\n"""\nx = 1\n')
    report = Linter(args={})._analyze_import_graph(tmp_path, set())
    assert "No circular dependencies found" in report


def test_section_comments_init_and_settings():
    small_init = 'from .a import A\n__all__ = ["A"]\n'
    assert _run(SectionCommentsRule, small_init, fname="src/small/__init__.py")[0] == []

    good_lazy_init = '''
_LAZY_EXPORTS: dict[str, str] = {
    # exceptions.py
    "A": ".exceptions",
    "B": ".exceptions",
    "C": ".exceptions",
    "D": ".exceptions",

    # sanitizers.py
    "E": ".sanitizers",
    "F": ".sanitizers",
    "G": ".sanitizers",
}
'''
    assert _run(SectionCommentsRule, good_lazy_init, fname="src/helpers/__init__.py")[0] == []

    bad_lazy_init = '''
_LAZY_EXPORTS: dict[str, str] = {
    "A": ".exceptions",
    "B": ".exceptions",
    "C": ".exceptions",
    "D": ".exceptions",
    "E": ".sanitizers",
    "F": ".sanitizers",
    "G": ".sanitizers",
}
'''
    v_bad_lazy, _ = _run(SectionCommentsRule, bad_lazy_init, fname="src/helpers/__init__.py")
    assert len(v_bad_lazy) == 1
    assert ".exceptions" in v_bad_lazy[0] and ".sanitizers" in v_bad_lazy[0]

    good_all_init = '''
from .files import a, b, c, d
from .logger import e, f, g

__all__ = [
    # files.py
    "a", "b", "c", "d",
    # logger.py
    "e", "f", "g",
]
'''
    assert _run(SectionCommentsRule, good_all_init, fname="src/config/__init__.py")[0] == []

    bad_all_init = '''
from .files import a, b, c, d
from .logger import e, f, g

__all__ = [
    "a", "b", "c", "d",
    "e", "f", "g",
]
'''
    v_bad_all, _ = _run(SectionCommentsRule, bad_all_init, fname="src/config/__init__.py")
    assert len(v_bad_all) == 1

    good_settings = '''
class Settings(BaseSettings):
    # Core
    A: int = 1
    B: int = 2
    C: int = 3
    D: int = 4
    E: int = 5

    # Database
    F: int = 6
    G: int = 7
    H: int = 8
    I: int = 9
'''
    assert _run(SectionCommentsRule, good_settings, fname="src/config/settings.py")[0] == []

    bad_settings = '''
class Settings(BaseSettings):
    A: int = 1
    B: int = 2
    C: int = 3
    D: int = 4
    E: int = 5

    F: int = 6
    G: int = 7
    H: int = 8
    I: int = 9
'''
    v_bad_set, _ = _run(SectionCommentsRule, bad_settings, fname="src/config/settings.py")
    assert len(v_bad_set) == 1
    assert "no '#' section headers" in v_bad_set[0]


def test_future_annotations_fp_and_tp():
    fp_plain = 'def greet(name: str) -> str:\n    return name\n'
    assert _run(FutureAnnotationsRule, fp_plain)[0] == []

    fp_quoted = 'class Node:\n    def parent(self) -> "Node":\n        return self\n'
    assert _run(FutureAnnotationsRule, fp_quoted)[0] == []

    fp_present = 'from __future__ import annotations\nclass Node:\n    def parent(self) -> Node:\n        return self\n'
    assert _run(FutureAnnotationsRule, fp_present)[0] == []

    tp_tc = '''
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import User

def handle(u: User) -> None:
    pass
'''
    v_tc, _ = _run(FutureAnnotationsRule, tp_tc)
    assert len(v_tc) == 1
    assert "TYPE_CHECKING" in v_tc[0]

    tp_self = '''
class Node:
    def parent(self) -> Node:
        return self
'''
    v_self, _ = _run(FutureAnnotationsRule, tp_self)
    assert len(v_self) == 1
    assert "self-referenced" in v_self[0]


def test_linter_scans_config_init(tmp_path):
    if "helpers" not in sys.modules:
        m_pkg = types.ModuleType("helpers")
        m_tool = types.ModuleType("helpers.tool")
        class Tool:
            def __init__(self, args=None):
                self.args = args or {}
        class Response:
            def __init__(self, message="", break_loop=False):
                self.message = message
                self.break_loop = break_loop
        m_tool.Tool = Tool
        m_tool.Response = Response
        sys.modules["helpers"] = m_pkg
        sys.modules["helpers.tool"] = m_tool

    from linter import Linter
    cfg = tmp_path / "src" / "config"
    cfg.mkdir(parents=True)
    (cfg / "paths.py").write_text("from pathlib import Path\nROOT = Path('.')\n")
    (cfg / "__init__.py").write_text(
        'from .files import a, b, c, d\nfrom .logger import e, f, g\n__all__ = [\n    "a", "b", "c", "d",\n    "e", "f", "g",\n]\n'
    )
    results, _ = Linter(args={}).audit_project(tmp_path, set(), set())
    assert "src/config/paths.py" not in results
    assert "src/config/__init__.py" in results
    assert any("Readability Violation" in v for v in results["src/config/__init__.py"])
