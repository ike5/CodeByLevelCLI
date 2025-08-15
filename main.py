# cbl.py
import os
import sys
import sqlite3
import hashlib
import zlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from collections import OrderedDict

import typer
from rich.console import Console
from rich.table import Table
from packaging.version import Version

app = typer.Typer()
console = Console()

BASE_DIR = Path(".codebylevel")
CONFIG_FILE = BASE_DIR / "config"
OBJECTS_DIR = BASE_DIR / "objects"
DB_FILE = BASE_DIR / "index.sqlite"


# ----------------------
# Config handling
# ----------------------
def load_config():
    import configparser
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)
    return config


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        config.write(f)


# ----------------------
# DB Setup
# ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
              CREATE TABLE IF NOT EXISTS project
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY,
                  name
                  TEXT
                  UNIQUE,
                  description
                  TEXT
              )
              """)
    c.execute("""
              CREATE TABLE IF NOT EXISTS object
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY,
                  project_id
                  INTEGER,
                  name
                  TEXT,
                  version
                  TEXT,
                  section
                  TEXT,
                  audience
                  TEXT,
                  hash
                  TEXT,
                  created_at
                  TEXT,
                  FOREIGN
                  KEY
              (
                  project_id
              ) REFERENCES project
              (
                  id
              )
                  )
              """)
    conn.commit()
    return conn


def get_conn():
    return sqlite3.connect(DB_FILE)


# ----------------------
# Object Store
# ----------------------
def store_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode() + data
    oid = hashlib.sha1(header).hexdigest()
    obj_path = OBJECTS_DIR / oid[:2] / oid[2:]
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    if not obj_path.exists():
        compressed = zlib.compress(header)
        obj_path.write_bytes(compressed)
    return oid


def read_blob(oid: str) -> bytes:
    obj_path = OBJECTS_DIR / oid[:2] / oid[2:]
    if not obj_path.exists():
        raise FileNotFoundError(f"Object {oid} not found")
    compressed = obj_path.read_bytes()
    header_data = zlib.decompress(compressed)
    _, _, body = header_data.partition(b"\0")
    return body


# ----------------------
# Commands
# ----------------------
@app.command()
def init(name: str, description: str = "", sections: Optional[str] = None):
    """Initialize a new CodeByLevel project."""
    BASE_DIR.mkdir(exist_ok=True)
    OBJECTS_DIR.mkdir(exist_ok=True)
    conn = init_db()
    c = conn.cursor()
    c.execute("INSERT INTO project (name, description) VALUES (?, ?)", (name, description))
    conn.commit()

    config = load_config()
    if "display" not in config:
        config["display"] = {}
    if sections:
        config["display"]["sections"] = sections
    save_config(config)

    console.print(f"[green]Initialized project '{name}'[/green]")


@app.command()
def add(
        name: str,
        version: Optional[str] = typer.Option(None),
        section: Optional[str] = typer.Option(None),
        audience: Optional[str] = typer.Option(None),
        project: Optional[str] = typer.Option(None),
):
    """Add or update an object version."""
    config = load_config()
    if not version:
        if config.has_section("defaults"):
            version = config.get("defaults", "version", fallback=None)
        else:
            version = None
    if not project:
        # If only one project exists, default to it
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT name FROM project")
        rows = c.fetchall()
        if len(rows) == 1:
            project = rows[0][0]
        else:
            console.print("[red]Multiple projects exist; specify --project[/red]")
            raise typer.Exit()

    editor = (
        os.environ.get("EDITOR")
        or (config.get("defaults", "editor", fallback=None) if config.has_section("defaults") else None)
        or "vi"
    )
    temp_file = Path(".cbl_temp.md")
    temp_file.write_text(f"# Documentation for {name}\n\n")
    subprocess.call([editor, str(temp_file)])
    content = temp_file.read_text()
    temp_file.unlink()

    blob_hash = store_blob(content.encode())

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM project WHERE name = ?", (project,))
    proj_row = c.fetchone()
    if not proj_row:
        console.print(f"[red]Project {project} not found[/red]")
        raise typer.Exit()
    project_id = proj_row[0]

    c.execute("""
              INSERT INTO object (project_id, name, version, section, audience, hash, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?)
              """, (project_id, name, version, section, audience, blob_hash, datetime.utcnow().isoformat()))
    conn.commit()

    console.print(f"[green]Added object '{name}' version {version} to project '{project}'[/green]")


@app.command()
def list(project: str):
    """List all objects in a project."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
              SELECT object.name, object.version, object.section, object.audience, object.created_at
              FROM object
              JOIN project ON object.project_id = project.id
              WHERE project.name = ?
              ORDER BY object.name, object.version
              """, (project,))
    rows = c.fetchall()

    table = Table(title=f"Objects in {project}")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Section")
    table.add_column("Audience")
    table.add_column("Created")

    for r in rows:
        table.add_row(*[str(x) if x is not None else "" for x in r])

    console.print(table)


@app.command()
def show(project: str, version: str, level: Optional[str] = None):
    """Show visible objects for a project & version."""
    config = load_config()
    if level is None and config.has_section("defaults") and config.has_option("defaults", "level"):
        level = config.get("defaults", "level")
    section_order = []
    if config.has_section("display") and config.has_option("display", "sections"):
        section_order = [s.strip() for s in config.get("display", "sections").split(",")]

    conn = get_conn()
    c = conn.cursor()
    params = [project]
    level_filter = ""
    if level:
        level_filter = "AND audience = ?"
        params.append(level)

    c.execute(f"""
    SELECT object.name, object.version, object.section, object.hash
    FROM object
    JOIN project ON object.project_id = project.id
    WHERE project.name = ?
    {level_filter}
    """, tuple(params))
    rows = c.fetchall()

    # Resolve latest ≤ requested
    latest = {}
    target = Version(version)
    for name, ver, section, hsh in rows:
        if Version(ver) <= target:
            if name not in latest or Version(ver) > Version(latest[name][0]):
                latest[name] = (ver, section, hsh)

    # Group by section with ordering
    grouped = OrderedDict()
    # Initialize keys in order
    for sec in section_order:
        grouped[sec] = []
    # Add items to groups; those not in section_order go to a special key
    other_key = None
    for name, (ver, section, hsh) in latest.items():
        key = section if section in grouped else None
        if key is None:
            if other_key is None:
                other_key = "__other__"
                grouped[other_key] = []
            key = other_key
        grouped[key].append((name, ver, section, hsh))

    table = Table(title=f"Visible objects for {project} @ {version} (level={level or 'all'})")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Section")
    table.add_column("Preview")

    first_section = True
    for sec, items in grouped.items():
        if not items:
            continue
        if not first_section:
            table.add_row("", "", "", "")
        first_section = False
        for name, ver, section, hsh in sorted(items):
            content = read_blob(hsh).decode().strip().splitlines()[0]
            table.add_row(name, ver, section or "", content[:50] + ("..." if len(content) > 50 else ""))

    console.print(table)

@app.command()
def build(project: str, version: str, level: Optional[str] = None, out: Optional[str] = None):
    """Assemble and export documentation for a project & version."""
    import configparser
    from rich.markdown import Markdown

    config = load_config()
    if level is None and config.has_section("defaults") and config.has_option("defaults", "level"):
        level = config.get("defaults", "level")
    section_order = []
    if config.has_section("display") and config.has_option("display", "sections"):
        section_order = [s.strip() for s in config.get("display", "sections").split(",")]

    conn = get_conn()
    c = conn.cursor()
    params = [project]
    level_filter = ""
    if level:
        level_filter = "AND audience = ?"
        params.append(level)

    c.execute(f"""
    SELECT object.name, object.version, object.section, object.hash
    FROM object
    JOIN project ON object.project_id = project.id
    WHERE project.name = ?
    {level_filter}
    """, tuple(params))
    rows = c.fetchall()

    latest = {}
    target = Version(version)
    for name, ver, section, hsh in rows:
        if Version(ver) <= target:
            if name not in latest or Version(ver) > Version(latest[name][0]):
                latest[name] = (ver, section, hsh)

    grouped = OrderedDict()
    for sec in section_order:
        grouped[sec] = []
    other_key = None
    for name, (ver, section, hsh) in latest.items():
        key = section if section in grouped else None
        if key is None:
            if other_key is None:
                other_key = "__other__"
                grouped[other_key] = []
            key = other_key
        grouped[key].append((name, ver, section, hsh))

    md_lines = []
    for sec in grouped:
        items = grouped[sec]
        if not items:
            continue
        md_lines.append(f"# {sec if sec != '__other__' else 'Other'}")
        for name, ver, section, hsh in sorted(items):
            content = read_blob(hsh).decode().strip()
            md_lines.append(content)
        md_lines.append("")

    md_text = "\n".join(md_lines).rstrip()

    if out:
        out_path = Path(out)
        out_path.write_text(md_text)
    else:
        console.print(Markdown(md_text))


if __name__ == "__main__":
    app()
