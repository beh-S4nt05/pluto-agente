"""`pluto update` — atualiza o projeto a partir do GitHub (v3.10).

Fluxo: consulta a última tag no repositório oficial → compara com a
versão instalada → baixa o zip da tag → aplica sobre a instalação atual
(preservando data/, .venv e .git). Stdlib pura (urllib/zipfile/shutil).

  pluto update --check   # só verifica se há versão nova
  pluto update           # verifica, confirma e aplica
  pluto update -y        # aplica sem perguntar (scripts)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import tempfile
import urllib.request
import subprocess
import zipfile
from pathlib import Path

from .config import VERSION

REPO = "beh-S4nt05/pluto-agente"
TAGS_API = f"https://api.github.com/repos/{REPO}/tags?per_page=30"
ZIP_URL = f"https://github.com/{REPO}/archive/refs/tags/{{tag}}.zip"

# o que NUNCA é tocado ao aplicar uma atualização
_PULA_DIRETORIOS = {"data", ".venv", ".git", ".github", "__pycache__",
                    "pluto-agente.egg-info", "node_modules"}
_PULA_ARQUIVOS = {".gitignore"}


def _parse_version(tag: str) -> tuple[int, ...]:
    """'v3.10.0' → (3,10,0); tags malformadas ficam (0,).

    P8.3: sufixos (-dev/-rc/-beta) são DESCARTADOS por parte —
    '9.0.0-dev' → (9,0,0). Antes virava (0,) e quebrava a recusa de
    downgrade (qualquer tag antiga parecia 'mais nova' que um dev
    instalado — pego pelo T81 ao versionar 9.0.0-dev)."""
    parts: list[int] = []
    for x in str(tag).lstrip("v").strip().split("."):
        x = x.split("-")[0].split("+")[0]      # '0-dev' → '0'
        if not x.isdigit():
            return (0,)
        parts.append(int(x))
    if len(parts) != 3:
        return (0,)
    return tuple(parts)


def _estavel(tag: str) -> bool:
    """Tag ESTÁVEL: estritamente vX.Y.Z, SEM sufixo (-beta/-rc/-dev).

    P8.3: antes o filtro de estabilidade era implícito (sufixo fazia
    _parse_version devolver (0,)); com o parser dev-aware isso precisou
    virar regra EXPLÍCITA aqui — o update só oferece versão estável,
    mas compara a INSTALADA (que pode ser 9.0.0-dev) pela base
    numérica."""
    return re.fullmatch(r"v?\d+\.\d+\.\d+", str(tag).strip()) is not None


def latest_tag(fetch=None) -> str | None:
    """Última tag do repositório (None se não conseguir consultar).
    `fetch(url) -> str` injetável para testes offline."""
    getter = fetch or (lambda url: urllib.request.urlopen(url, timeout=15)
                       .read().decode())
    try:
        tags = [t.get("name", "") for t in json.loads(getter(TAGS_API))]
        validas = [t for t in tags if _estavel(t)]
        return max(validas, key=_parse_version) if validas else None
    except Exception:  # noqa: BLE001
        return None


def _project_root() -> Path:
    """Raiz da instalação (pasta que contém pluto/ e pyproject.toml)."""
    return Path(__file__).resolve().parent.parent


def _assert_zip_seguro(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    """v3.14.2: defesa zip-slip — nenhum membro do zip pode escapar do
    diretório de destino (caminho absoluto ou com '..' é recusado)."""
    base = dest_dir.resolve()
    seen = set()
    total_size = 0
    for info in zf.infolist():
        nome = info.filename
        if nome in seen:
            raise RuntimeError(f"zip com entrada duplicada: {nome!r}")
        seen.add(nome)
        if (dest_dir / nome).resolve() != base / nome.lstrip("/"):
            raise RuntimeError(f"zip com caminho inválido: {nome!r}")
        # Symlinks inside a release archive can redirect extraction or copying.
        if (info.create_system == 3
                and ((info.external_attr >> 16) & 0o170000) == 0o120000):
            raise RuntimeError(f"zip com link simbólico: {nome!r}")
        total_size += info.file_size
        if info.file_size > 100 * 1024 * 1024 or total_size > 500 * 1024 * 1024:
            raise RuntimeError("zip excede o limite de tamanho descompactado")


def _verify_sha256(path: Path, expected: str) -> None:
    """Verify a SHA-256 digest obtained independently of the archive."""
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise RuntimeError("SHA-256 esperado inválido (64 caracteres hexadecimais)")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if not hmac.compare_digest(digest.hexdigest(), expected.lower()):
        raise RuntimeError("SHA-256 da atualização não corresponde ao esperado")


def _trusted_checksum(tag: str, root: Path) -> str | None:
    """Resolve a digest from a locally provisioned trust manifest.

    The manifest must be installed through an independent trusted channel;
    downloading a checksum beside the archive would not authenticate it.
    """
    direct = os.environ.get("PLUTO_UPDATE_SHA256")
    if direct is not None:
        return direct
    manifest = root / "data" / "update-checksums.json"
    if not manifest.is_file() or manifest.is_symlink():
        return None
    try:
        if manifest.stat().st_size > 64 * 1024:
            return None
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        entry = payload.get(tag)
        if isinstance(entry, str) and re.fullmatch(r"[0-9a-fA-F]{64}", entry):
            return entry
    except (OSError, ValueError, UnicodeError):
        return None
    return None


_MAX_UPDATE_ZIP_BYTES = 200 * 1024 * 1024


def _copy_bounded(stream, target: Path, limit: int = _MAX_UPDATE_ZIP_BYTES) -> None:
    """Download at most limit bytes, rejecting oversized bodies regardless of headers."""
    count = 0
    try:
        with target.open("wb") as output:
            while True:
                chunk = stream.read(min(1024 * 1024, limit - count + 1))
                if not chunk:
                    break
                count += len(chunk)
                if count > limit:
                    raise RuntimeError("arquivo ZIP da atualização excede 200 MiB")
                output.write(chunk)
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def download(tag: str, dest_dir: Path, expected_sha256: str | None = None) -> Path:
    """Download and verify a stable release ZIP before extraction (fail closed)."""
    if not isinstance(tag, str) or not _estavel(tag):
        raise RuntimeError("tag de atualização inválida: esperado vX.Y.Z")
    if expected_sha256 is None:
        raise RuntimeError("atualização bloqueada: forneça PLUTO_UPDATE_SHA256 ou data/update-checksums.json confiável")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise RuntimeError("SHA-256 esperado inválido (64 caracteres hexadecimais)")
    url = ZIP_URL.format(tag=tag)
    zpath = dest_dir / f"{tag}.zip"
    with urllib.request.urlopen(url, timeout=120) as response:
        _copy_bounded(response, zpath)
    _verify_sha256(zpath, expected_sha256)
    with zipfile.ZipFile(zpath) as zf:
        _assert_zip_seguro(zf, dest_dir)
        zf.extractall(dest_dir)
    raiz = dest_dir / f"{REPO.split('/')[-1]}-{tag}"
    if not raiz.is_dir():
        # GitHub pode usar "personal-hermes-agent-behsantos-<sem v>"
        alt = dest_dir / f"{REPO.split('/')[-1]}-{tag.lstrip('v')}"
        if alt.is_dir():
            raiz = alt
        else:
            raise RuntimeError("zip extraído sem a pasta esperada do projeto")
    return raiz


def _copy_file_atomic(source: Path, target: Path) -> None:
    """Stage in destination directory and atomically replace a single file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, staging = tempfile.mkstemp(prefix=".pluto-update-", dir=str(target.parent))
    os.close(fd)
    try:
        shutil.copy2(source, staging)
        os.replace(staging, target)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def apply_update(src_root: Path, dest_root: Path,
                 log=print) -> list[str]:
    """Copia a nova versão sobre a instalação — preserva data/, .venv e
    .git. Devolve a lista de itens atualizados."""
    atualizados: list[str] = []
    # Preflight the complete update before writing anything. A pre-existing
    # symlink in the destination must never redirect copytree/copy2 outside.
    for item in sorted(src_root.rglob("*")):
        if item.is_symlink():
            raise RuntimeError(f"atualização contém link simbólico: {item}")
    for item in sorted(src_root.iterdir()):
        nome = item.name
        if nome in _PULA_DIRETORIOS or nome in _PULA_ARQUIVOS:
            continue
        relative_paths = [Path(nome)]
        if item.is_dir():
            relative_paths.extend(p.relative_to(src_root) for p in item.rglob("*"))
        for relative in relative_paths:
            target = dest_root / relative
            for ancestor in (target, *target.parents):
                if ancestor == dest_root.parent:
                    break
                if ancestor.is_symlink():
                    raise RuntimeError(f"destino da atualização contém link simbólico: {ancestor}")
    # Snapshot every file that may be replaced before writing the first one.
    files: list[tuple[Path, Path]] = []
    dirs: list[Path] = []
    for item in sorted(src_root.iterdir()):
        nome = item.name
        if nome in _PULA_DIRETORIOS or nome in _PULA_ARQUIVOS:
            continue
        if item.is_dir():
            for child in sorted(item.rglob("*")):
                rel = child.relative_to(src_root)
                if any(part in {"__pycache__", ".venv"} for part in rel.parts) or child.suffix == ".pyc":
                    continue
                if child.is_dir():
                    dirs.append(dest_root / rel)
                elif child.is_file():
                    files.append((child, dest_root / rel))
        else:
            files.append((item, dest_root / nome))
        atualizados.append(nome)
    with tempfile.TemporaryDirectory(prefix="pluto-rollback-") as backup_dir:
        backup = Path(backup_dir)
        existing: dict[Path, Path | None] = {}
        for index, (_, target) in enumerate(files):
            if target.exists():
                if not target.is_file():
                    raise RuntimeError(f"destino não é arquivo regular: {target}")
                saved = backup / str(index)
                shutil.copy2(target, saved)
                existing[target] = saved
            else:
                existing[target] = None
        created_dirs: list[Path] = []
        written: list[Path] = []
        try:
            for directory in sorted(set(dirs + [t.parent for _, t in files]), key=lambda p: len(p.parts)):
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(directory)
            for source, target in files:
                _copy_file_atomic(source, target)
                written.append(target)
        except Exception:
            rollback_errors = []
            for target in reversed(written):
                try:
                    saved = existing[target]
                    if saved is None:
                        target.unlink(missing_ok=True)
                    else:
                        _copy_file_atomic(saved, target)
                except OSError as exc:
                    rollback_errors.append(f"{target}: {exc}")
            for directory in reversed(created_dirs):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            if rollback_errors:
                raise RuntimeError("rollback incompleto: " + "; ".join(rollback_errors))
            raise
    log(f"  ✔ {len(atualizados)} itens atualizados: "
        + ", ".join(atualizados[:8]) + ("…" if len(atualizados) > 8 else ""))
    return atualizados


def _venv_python(root: Path) -> Path | None:
    """Python do venv DO PROJETO (bin/ no Unix, Scripts/ no Windows)."""
    from .plataforma import so
    p = (root / ".venv" / "Scripts" / "python.exe" if so() == "windows"
         else root / ".venv" / "bin" / "python")
    return p if p.exists() else None


def garantir_entry_points(root: Path, log=print) -> bool:
    """v6.0.1: autocura dos COMANDOS `pluto` (+ alias `hermes`).

    Entry points são gerados NA INSTALAÇÃO (pip); o update troca os
    arquivos PRESERVANDO o .venv — então quem instalou antes da v4.1.0
    ficou só com `hermes` no venv (achado real do operador em teste).
    Regenera com `pip install -e . --no-deps` (offline-safe) e, se não
    der, escreve o launcher na mão. Roda também quando JÁ está na
    versão mais recente (é autocura, não só pós-update).
    """
    from .plataforma import so
    py = _venv_python(root)
    if py is None:
        log("  ℹ sem .venv no projeto — se a instalação for global/pipx,")
        log("    rode: pip install -e .   (ou reinstale com pipx)")
        return False
    win = so() == "windows"
    bindir = root / ".venv" / ("Scripts" if win else "bin")
    alvo = bindir / ("pluto.exe" if win else "pluto")
    # P0.1 (lote 5): no Windows o fallback manual cria pluto.bat (não
    # pluto.exe) — sem checá-lo a autocura rodava o pip a CADA chamada
    # (quebrava a idempotência prometida)
    if alvo.exists() or (win and (bindir / "pluto.bat").exists()):
        return True                       # já registrado nada a fazer
    # 1) regeneração oficial (não toca nas deps — offline-safe)
    tentativa = [str(py), "-m", "pip", "install", "-e", ".", "-q",
                 "--no-deps"]

    def _tentar() -> bool:
        try:
            r = subprocess.run(tentativa, cwd=str(root),
                               capture_output=True, timeout=300)
            return bool(r.returncode == 0
                        and (alvo.exists()
                             or (bindir / "pluto-script.py").exists()))
        except Exception:  # noqa: BLE001
            return False

    if _tentar():
        log("  🧷 comando `pluto` registrado no venv "
        "(+ aliases betterme e hermes)")
        return True
    # v6.0.2 (2º bug de campo): setuptools < 64 não tem o hook
    # build_editable (PEP 660) — "pip install -e ." falha. Atualiza as
    # FERRAMENTAS DE BUILD do próprio venv e tenta de novo antes de
    # recorrer ao launcher manual.
    try:
        subprocess.run([str(py), "-m", "pip", "install", "-q", "-U",
                        "pip", "setuptools"], cwd=str(root),
                       capture_output=True, timeout=300)
    except Exception:  # noqa: BLE001
        pass
    if _tentar():
        log("  🧷 comando `pluto` registrado (após atualizar pip/"
            "setuptools do venv — PEP 660 ✔)")
        return True
    # 2) fallback: launcher manual (funciona offline)
    try:
        if win:
            (bindir / "pluto.bat").write_text(
                '@"%~dp0python.exe" -m pluto %*\r\n', encoding="utf-8")
        else:
            launcher = bindir / "pluto"
            launcher.write_text(
                "#!" + str(py) + "\n"
                "import sys\n"
                "from pluto.cli import main\n"
                "sys.exit(main())\n", encoding="utf-8")
            launcher.chmod(0o755)
        log("  🧷 comando `pluto` recriado (launcher manual) — rode "
            "`./.venv/bin/pip install -e .` quando puder p/ oficializar")
        return True
    except OSError as exc:
        log(f"  ✖ não consegui criar o comando `pluto`: {exc} — rode: "
            "./.venv/bin/pip install -e .")
        return False


def run(check_only: bool = False, assume_yes: bool = False,
        print_fn=print) -> int:
    """Executa o update; devolve código de saída (0 = ok/atualizado)."""
    print_fn(f"⬇ pluto update · versão instalada: v{VERSION}")
    tag = latest_tag()
    if not tag:
        print_fn("✖ não consegui consultar o GitHub (sem internet?) — "
                 "tente: pluto update --check")
        return 1
    print_fn(f"  última versão no GitHub: {tag}")
    if _parse_version(tag) <= _parse_version(VERSION):
        print_fn("✔ você já está na versão mais recente.")
        garantir_entry_points(_project_root(), log=print_fn)
        return 0
    if check_only:
        print_fn(f"ℹ há atualização: v{VERSION} → {tag} — rode: pluto update")
        return 0
    if not assume_yes:
        try:
            resp = input(f"  aplicar v{VERSION} → {tag}? [s/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            resp = ""
        if resp not in ("s", "sim", "y", "yes"):
            print_fn("  cancelado.")
            return 1
    root = _project_root()
    with tempfile.TemporaryDirectory(prefix="pluto-update-") as tmp:
        try:
            src = download(tag, Path(tmp), _trusted_checksum(tag, root))
        except (RuntimeError, OSError, zipfile.BadZipFile) as exc:
            print_fn(f"✖ atualização não aplicada: {exc}")
            return 1
        print_fn(f"  baixado e extraído: {tag}")
        apply_update(src, root, log=print_fn)
    garantir_entry_points(root, log=print_fn)
    print_fn("\n  ✔ atualização aplicada. Se o `pluto server` estiver rodando,")
    print_fn("    reinicie-o (GUI: ⏹ Desligar → ▶ Ligar) para valer.")
    print_fn("    Dependências novas (se houver): ./.venv/bin/pip install -e . -q")
    return 0
