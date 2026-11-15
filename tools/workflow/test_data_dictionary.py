"""Keep docs/data-dictionary.md mechanically consistent with the field registry."""

from pathlib import Path
import re
import tomllib
import unittest

from tools.workflow import project_config as config


REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs/data-dictionary.md"
FIELDS_HEADING = "## Campos de configuración"
NATIVE_HEADING = "## Datos nativos y compartidos"
TYPE_LABELS = {"integer": "entero", "number": "número", "path": "ruta", "revision": "revisión", "string": "cadena"}
IMPLEMENTED_CONSUMERS = {"project_config.py", "check_payload_manifest.py",
                       "bag2_workflow.py", "bag2_report.py",
                         "versus_session.py", "strike_acceptance_batch.py", "view_config.py",
                          "bag2_record.py", "recording_config.py", "character_workflow.py"}
MACHINE_PATH = r"(?<![\w:/])[A-Za-z]:[\\/]"


def _flatten(data: dict, prefix: str = "") -> list[tuple[str, object]]:
    rows = []
    for key, value in data.items():
        dotted = f"{prefix}{key}"
        if isinstance(value, dict):
            rows.extend(_flatten(value, dotted + "."))
        else:
            rows.append((dotted, value))
    return rows


def rows_under(text: str, heading: str) -> list[dict[str, str]]:
    """Return the first markdown table under heading, keyed by its header cells."""
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        raise AssertionError(f"missing section {heading!r}") from None
    table = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.lstrip().startswith("|"):
            table.append(line.strip())
        elif table:
            break
    if len(table) < 3:
        raise AssertionError(f"section {heading!r} has no table with data rows")
    header = [cell.strip() for cell in table[0].strip("|").split("|")]
    result = []
    for line in table[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header):
            raise AssertionError(f"row has {len(cells)} cells, expected {len(header)}: {line}")
        result.append(dict(zip(header, cells)))
    return result


class DictionaryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DOC.is_file(), f"missing data dictionary: {DOC}")
        self.text = DOC.read_text(encoding="utf-8")

    def field_rows(self):
        rows = rows_under(self.text, FIELDS_HEADING)
        by_key: dict[str, dict[str, str]] = {}
        for row in rows:
            key = row["Clave"].strip("`")
            self.assertNotIn(key, by_key, f"duplicate row for {key}")
            by_key[key] = row
        return by_key

    def test_every_registered_field_is_documented_once(self):
        documented = set(self.field_rows())
        self.assertEqual(sorted(documented - set(config.FIELDS)), [],
                         "documented keys that are not in FIELDS")
        self.assertEqual(sorted(set(config.FIELDS) - documented), [],
                         "registered keys without a dictionary row")

    def test_types_units_and_origins_match_registry(self):
        for key, row in self.field_rows().items():
            spec = config.FIELDS[key]
            with self.subTest(key=key):
                self.assertEqual(row["Tipo"], TYPE_LABELS[spec.kind])
                self.assertEqual(row["Unidad"], spec.unit)
                if spec.kind in ("integer", "number") and spec.expected is not None:
                    self.assertIn(f"exactamente {spec.expected}", row["Validación"])
                if spec.role == "derived":
                    self.assertEqual(row["Origen"], "derivado")
                else:
                    self.assertEqual(row["Origen"], "común/local" if spec.local_override else "común")
                self.assertEqual(row["Fuente local"], "sí" if spec.local_override else "no")
                self.assertTrue(row["Significado"] and row["Validación"],
                                "meaning and validation are required")

    def test_status_and_consumers_do_not_claim_unimplemented_migrations(self):
        for key, row in self.field_rows().items():
            spec = config.FIELDS[key]
            with self.subTest(key=key):
                self.assertIn(row["Estado"], {"base"},
                              "only the resolver foundation is implemented")
                expected_operations = ", ".join(spec.operations) if spec.operations else "—"
                self.assertEqual(row["Operaciones"], expected_operations)
                tokens = [token.strip().strip("`") for token in re.split(r"[;,]", row["Consumidor"]) if token.strip()]
                self.assertIn("project_config.py", tokens)
                for token in tokens:
                    if token in IMPLEMENTED_CONSUMERS:
                        continue
                    self.assertRegex(token, r"\(pendiente\)$",
                                     f"{key}: {token!r} is not implemented and must end with (pendiente)")

    def test_dictionary_has_no_machine_absolute_paths(self):
        self.assertEqual(re.findall(MACHINE_PATH, self.text), [],
                         "machine paths belong in the ignored local config")
        self.assertNotIn("\\\\", self.text)

    def test_shipped_common_config_has_no_machine_paths_and_registered_keys(self):
        text = (REPO / "config/project.toml").read_text(encoding="utf-8")
        self.assertEqual(re.findall(MACHINE_PATH, text), [])
        data = tomllib.loads(text)
        keys = {key for key, _value in _flatten(data)}
        self.assertEqual(sorted(keys - set(config.FIELDS)), [])

    def test_native_references_exist_and_are_not_editable(self):
        rows = rows_under(self.text, NATIVE_HEADING)
        self.assertGreaterEqual(len(rows), 5, "native/shared data needs documented references")
        for row in rows:
            reference = row["Referencia"].strip("`")
            with self.subTest(reference=reference):
                self.assertEqual(row["Editable en TOML"], "no")
                self.assertIn(row["Estado"], {"verificado", "pendiente"})
                self.assertTrue((REPO / reference).exists(), f"missing native reference {reference}")

    def test_template_only_mentions_registered_sections(self):
        text = (REPO / "config/project.local.example.toml").read_text(encoding="utf-8")
        template = tomllib.loads(text)
        # Only the shared schema line is live; every location stays commented out.
        self.assertEqual(sorted(_flatten(template)), [("schema_version", 1)])
        allowed = {key.split(".")[0] for key, spec in config.FIELDS.items()
                   if "." in key and spec.local_override}
        sections = set(re.findall(r"^\[([a-z_]+)\]", text, re.M)) - allowed
        self.assertEqual(sorted(sections), [])


if __name__ == "__main__":
    unittest.main()
