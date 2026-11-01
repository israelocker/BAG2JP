#!/usr/bin/env python3
"""Reporte de uso de tokens por sesión para el proyecto BAG2JP.

Este script ayuda a monitorear y optimizar el uso de tokens en sesiones de
agentes de IA, proporcionando métricas sobre el tamaño del contexto cargado,
archivos leídos y estimación de tokens consumidos.

Usage:
    py tools/workflow/token-report.py [--session <name>] [--export <format>]
    py tools/workflow/token-report.py --check-context
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]

# Tokens por carácter aproximado (varía por modelo, pero ~4 chars/token es estándar)
CHARS_PER_TOKEN = 4

logger = logging.getLogger("token-report")

# Archivos esenciales de inicio (protocolo de chat nuevo)
ESSENTIAL_FILES = [
    "AGENTS.md",
    "NOTES.md",
    "_work/current-state.json",
    "IMPORT_STANDARD.md",
]

# Directorios y archivos que no deben leerse completos
LARGE_FILE_THRESHOLD_KB = 10


def estimate_tokens(text: str) -> int:
    """Estima el número de tokens en un texto."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def file_size_kb(path: Path) -> float:
    """Retorna el tamaño del archivo en KB, o 0.0 si no existe."""
    if path.exists():
        return path.stat().st_size / 1024
    return 0.0


def read_file_safe(path: Path) -> Optional[str]:
    """Lee un archivo de forma segura, retornando None si falla."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def check_startup_context() -> dict:
    """Mide el tamaño del contexto de inicio mínimo."""
    results = {}
    total_kb = 0.0
    total_tokens = 0

    for f in ESSENTIAL_FILES:
        path = ROOT / f
        if path.exists():
            content = read_file_safe(path)
            size_kb = file_size_kb(path)
            tokens = estimate_tokens(content) if content else 0
            results[f] = {
                "exists": True,
                "size_kb": round(size_kb, 1),
                "estimated_tokens": tokens,
            }
            total_kb += size_kb
            total_tokens += tokens
        else:
            results[f] = {
                "exists": False,
                "size_kb": 0.0,
                "estimated_tokens": 0,
            }

    return {
        "files": results,
        "total_kb": round(total_kb, 1),
        "total_estimated_tokens": total_tokens,
        "under_8kb": total_kb < 8.0,
    }


def check_large_files() -> list[dict]:
    """Identifica archivos grandes que deberían tener un digest."""
    large_files = []
    notes_dir = ROOT / "notes"

    if notes_dir.exists():
        for f in sorted(notes_dir.rglob("*.md")):
            size_kb = file_size_kb(f)
            if size_kb > LARGE_FILE_THRESHOLD_KB:
                digest_path = ROOT / "notes" / "digests" / (f.stem + ".digest.md")
                large_files.append({
                    "file": str(f.relative_to(ROOT)),
                    "size_kb": round(size_kb, 1),
                    "has_digest": digest_path.exists(),
                })

    return sorted(large_files, key=lambda x: x["size_kb"], reverse=True)


def check_duplicates() -> list[dict]:
    """Busca posibles archivos duplicados o casi duplicados."""
    duplicates = []
    notes_dir = ROOT / "notes"

    if not notes_dir.exists():
        return duplicates

    md_files = list(notes_dir.glob("*.md"))
    seen_hashes: dict[str, str] = {}

    for f in md_files:
        content = read_file_safe(f)
        if content is None:
            continue
        # Hash simple basado en las primeras 2000 caracteres (estructura, no contenido exacto)
        content_hash = str(hash(content[:2000]))
        if content_hash in seen_hashes:
            duplicates.append({
                "file": str(f.relative_to(ROOT)),
                "possible_duplicate_of": seen_hashes[content_hash],
            })
        else:
            seen_hashes[content_hash] = str(f.relative_to(ROOT))

    return duplicates


def generate_report(session_name: Optional[str] = None) -> dict:
    """Genera un reporte completo de uso de tokens."""
    startup = check_startup_context()
    large_files = check_large_files()
    duplicates = check_duplicates()

    report = {
        "session": session_name or "default",
        "timestamp": datetime.now().isoformat(),
        "startup_context": startup,
        "large_files": large_files,
        "duplicate_candidates": duplicates,
        "summary": {
            "total_startup_kb": startup["total_kb"],
            "total_startup_tokens": startup["total_estimated_tokens"],
            "large_file_count": len(large_files),
            "files_without_digest": sum(1 for f in large_files if not f["has_digest"]),
            "duplicate_count": len(duplicates),
            "under_8kb_goal": startup["under_8kb"],
        },
    }

    return report


def print_report(report: dict) -> None:
    """Imprime el reporte de forma legible."""
    print("=" * 60)
    print("REPORTE DE USO DE TOKENS - BAG2JP")
    print("=" * 60)
    print(f"Sesión: {report['session']}")
    print(f"Fecha: {report['timestamp']}")
    print()

    # Contexto de inicio
    startup = report["startup_context"]
    print("--- Contexto de Inicio Mínimo ---")
    for fname, info in startup["files"].items():
        status = "[OK]" if info["exists"] else "[FALTANTE]"
        print(f"  {status} {fname}: {info['size_kb']:.1f} KB (~{info['estimated_tokens']} tokens)")
    print(f"  TOTAL: {startup['total_kb']:.1f} KB (~{startup['total_estimated_tokens']} tokens)")
    print(f"  Objetivo <8 KB: {'✅ CUMPLIDO' if startup['under_8kb'] else '⚠️  SUPERADO'}")
    print()

    # Archivos grandes
    print("--- Archivos Grandes (>10 KB) ---")
    if report["large_files"]:
        for f in report["large_files"]:
            digest_status = "[Tiene digest]" if f["has_digest"] else "[SIN digest]"
            print(f"  {digest_status} {f['file']}: {f['size_kb']:.1f} KB")
    else:
        print("  (ninguno)")
    print()

    # Duplicados
    print("--- Posibles Duplicados ---")
    if report["duplicate_candidates"]:
        for d in report["duplicate_candidates"]:
            print(f"  ⚠️  {d['file']} posible duplicado de {d['possible_duplicate_of']}")
    else:
        print("  (ninguno detectado)")
    print()

    # Resumen
    print("--- Resumen ---")
    s = report["summary"]
    print(f"  Contexto de inicio: {s['total_startup_kb']:.1f} KB (~{s['total_startup_tokens']} tokens)")
    print(f"  Archivos grandes: {s['large_file_count']}")
    print(f"  Sin digest: {s['files_without_digest']}")
    print(f"  Posibles duplicados: {s['duplicate_count']}")
    print(f"  Objetivo <8 KB: {'✅ CUMPLIDO' if s['under_8kb_goal'] else '⚠️  SUPERADO'}")
    print()
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reporte de uso de tokens para BAG2JP")
    parser.add_argument("--session", type=str, help="Nombre de la sesión")
    parser.add_argument(
        "--export", type=str, choices=["json"], help="Exportar reporte a JSON"
    )
    parser.add_argument(
        "--check-context", action="store_true", help="Solo verificar contexto de inicio"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    report = generate_report(session_name=args.session)

    if args.check_context:
        startup = report["startup_context"]
        if startup["under_8kb"]:
            logger.info("Contexto de inicio bajo 8 KB: OK")
            return 0
        else:
            logger.warning(f"Contexto de inicio supera 8 KB ({startup['total_kb']:.1f} KB)")
            return 1

    print_report(report)

    if args.export == "json":
        output_path = ROOT / f"token-report-{report['session']}.json"
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(f"Reporte exportado a: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())