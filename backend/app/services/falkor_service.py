"""FalkorDB service: the graph is the context, reasoning and memory layer.

Three graph families live in one FalkorDB instance:

* ``clinical_rules``   - Track 01. Symptom -> Diagnosis -> Procedure necessity, NCCI-style bundling,
                         drug-class contraindications.
* ``patient_<id>``     - Track 02. One isolated subgraph per patient (multi-tenant memory):
                         encounters, conditions and active medications across sessions.
* ``hospital_brain``   - Track 03. Departments, supervising physicians, frequently billed CPTs and
                         historical denial reasons.

Every decision method returns a deterministic ``trace_path`` built from ``nodes(path)``.

NOTE: hospital_brain content (departments, physicians, volumes, denial counts) and patient P-9801 are
SYNTHETIC demo data. ICD-10-CM / CPT / CARC codes and drug-class contraindications are real.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

RULES_GRAPH = "clinical_rules"
BRAIN_GRAPH = "hospital_brain"

# Maps a patient name (lower-cased) to a graph patient id when the session carries no explicit id.
SEEDED_PATIENT_INDEX = {"robert vance": "P-9801"}

TRACE_QUERY = (
    "MATCH path = (s:Symptom)-[:INDICATES]->(d:Diagnosis)-[:SUPPORTS_NECESSITY]->(p:Procedure {code: $code}) "
    "WHERE s.name IN $symptoms "
    "RETURN [n IN nodes(path) | coalesce(n.name, n.code)] AS trace_path, d.code AS icd, p.code AS cpt ORDER BY d.code "
    "LIMIT 1"
)


def safe_patient_id(patient_id: str) -> str:
    """Graph names are keys; keep them to a conservative alphabet."""
    return re.sub(r"[^A-Za-z0-9_-]", "", patient_id or "")


def resolve_patient_id(patient_name: str = "", patient_dob: str = "", metadata: Optional[dict] = None) -> str:
    """Explicit metadata.patient_id wins, then seeded index, then a stable hash of name+dob."""
    import hashlib

    if metadata and metadata.get("patient_id"):
        return safe_patient_id(str(metadata["patient_id"]))
    key = (patient_name or "").strip().lower()
    if key in SEEDED_PATIENT_INDEX:
        return SEEDED_PATIENT_INDEX[key]
    digest = hashlib.sha1(f"{key}|{patient_dob}".encode()).hexdigest()[:6].upper()
    return f"P-{digest}"


class FalkorHealthService:
    def __init__(self) -> None:
        self._db = None
        self.available = False
        self.last_error: Optional[str] = None

    # ------------------------------------------------------------------ connection
    def connect(self):
        if self._db is not None:
            return self._db
        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT,
                password=settings.FALKORDB_PASSWORD or None,
            )
            db.list_graphs()  # forces a round trip
            self._db = db
            self.available = True
            self.last_error = None
        except Exception as e:  # pragma: no cover - depends on environment
            self.available = False
            self.last_error = str(e)
            self._db = None
            logger.error(
                "FalkorDB unreachable at %s:%s (%s). Start it with: "
                "docker run -d -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest",
                settings.FALKORDB_HOST, settings.FALKORDB_PORT, e,
            )
        return self._db

    def _graph(self, name: str):
        db = self.connect()
        return db.select_graph(name) if db is not None else None

    def _q(self, graph_name: str, query: str, params: Optional[dict] = None) -> List[list]:
        g = self._graph(graph_name)
        if g is None:
            raise RuntimeError(f"FalkorDB unavailable: {self.last_error}")
        return g.query(query, params or {}).result_set

    def status(self) -> Dict[str, Any]:
        self._db = None  # re-probe each time
        self.connect()
        graphs: List[str] = []
        if self.available:
            try:
                graphs = sorted(self._db.list_graphs())
            except Exception:
                pass
        return {"engine": "falkordb", "available": self.available, "graphs": graphs, "error": self.last_error}

    # ------------------------------------------------------------------ seeding
    def init_databases(self) -> Dict[str, Any]:
        """Idempotent: every write uses MERGE so restarts never duplicate the seed."""
        if self.connect() is None:
            return {"seeded": False, "error": self.last_error}
        self._seed_clinical_rules()
        self._seed_hospital_brain()
        self._seed_patient_p9801()
        logger.info("FalkorDB seeded: clinical_rules, hospital_brain, patient_P-9801")
        return {"seeded": True, "graphs": self.status()["graphs"]}

    def _seed_clinical_rules(self) -> None:
        g = RULES_GRAPH
        for q in (
            "CREATE INDEX FOR (s:Symptom) ON (s.name)",
            "CREATE INDEX FOR (p:Procedure) ON (p.code)",
            "CREATE INDEX FOR (d:Drug) ON (d.name)",
        ):
            try:
                self._q(g, q)
            except Exception:
                pass  # index already exists

        # ICD-10-CM diagnoses (real codes)
        diagnoses = [
            ("I20.9", "Angina pectoris, unspecified"),
            ("E11.9", "Type 2 diabetes mellitus without complications"),
            ("I10", "Essential (primary) hypertension"),
            ("R07.9", "Chest pain, unspecified"),
        ]
        for code, name in diagnoses:
            self._q(g, "MERGE (d:Diagnosis {code:$c}) SET d.description=$n", {"c": code, "n": name})

        # CPT procedures (real codes)
        procedures = [
            ("93000", "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report"),
            ("93005", "Electrocardiogram, tracing only, without interpretation and report"),
            ("93010", "Electrocardiogram, interpretation and report only"),
            ("99214", "Office/outpatient visit, established patient, moderate medical decision making"),
            ("82947", "Glucose; quantitative, blood (except reagent strip)"),
        ]
        for code, name in procedures:
            self._q(g, "MERGE (p:Procedure {code:$c}) SET p.description=$n", {"c": code, "n": name})

        # Symptoms (graph-driven entity extraction uses name + aliases)
        symptoms = [
            ("chest pain", ["chest pain", "pain in my chest", "pain in the chest"]),
            ("chest tightness", ["chest tight", "tight chest", "chest feels heavy", "chest heaviness",
                                 "chest pressure", "tightness in my chest", "chest tightness"]),
            ("exertional chest pain", ["chest pain on exertion", "chest pain when i walk", "pain when climbing stairs",
                                       "chest pain with exertion", "exertional chest"]),
            ("polyuria", ["polyuria", "urinating a lot", "frequent urination"]),
            ("polydipsia", ["polydipsia", "very thirsty", "excessive thirst"]),
            ("elevated blood pressure", ["high blood pressure", "elevated blood pressure", "hypertension"]),
        ]
        for name, aliases in symptoms:
            self._q(g, "MERGE (s:Symptom {name:$n}) SET s.aliases=$a", {"n": name, "a": aliases})

        indicates = [
            ("chest pain", "R07.9"), ("chest tightness", "R07.9"), ("chest tightness", "I20.9"),
            ("exertional chest pain", "I20.9"), ("exertional chest pain", "R07.9"),
            ("polyuria", "E11.9"), ("polydipsia", "E11.9"), ("elevated blood pressure", "I10"),
        ]
        for s, d in indicates:
            self._q(g, "MATCH (s:Symptom {name:$s}),(d:Diagnosis {code:$d}) MERGE (s)-[:INDICATES]->(d)", {"s": s, "d": d})

        # Medical-necessity edges. R07.9 and I20.9 validate 93000 (per mission ground truth).
        necessity = [("R07.9", "93000"), ("I20.9", "93000"), ("E11.9", "82947"),
                     ("E11.9", "99214"), ("I10", "99214")]
        for d, p in necessity:
            self._q(g, "MATCH (d:Diagnosis {code:$d}),(p:Procedure {code:$p}) MERGE (d)-[:SUPPORTS_NECESSITY]->(p)", {"d": d, "p": p})

        # NCCI-style bundling: 93000 = 93005 + 93010, so billing components alongside 93000 is unbundling
        for comp in ("93005", "93010"):
            self._q(g, "MATCH (a:Procedure {code:'93000'}),(b:Procedure {code:$b}) MERGE (a)-[:INCLUDES]->(b)", {"b": comp})

        # Drug classes + contraindications
        drugs = [
            ("nitroglycerin", "Nitrate", ["nitroglycerin", "nitrostat", "glyceryl trinitrate", "gtn"]),
            ("sildenafil", "PDE5 Inhibitor", ["sildenafil", "viagra", "revatio"]),
            ("lisinopril", "ACE Inhibitor", ["lisinopril", "zestril", "prinivil"]),
            ("spironolactone", "Potassium-Sparing Diuretic", ["spironolactone", "aldactone"]),
            ("amlodipine", "Calcium Channel Blocker", ["amlodipine", "norvasc"]),
            ("albuterol", "Beta-2 Agonist", ["albuterol", "salbutamol", "ventolin", "proair"]),
        ]
        for name, cls, aliases in drugs:
            self._q(g, "MERGE (c:DrugClass {name:$c}) MERGE (d:Drug {name:$n}) SET d.aliases=$a MERGE (d)-[:IN_CLASS]->(c)",
                    {"n": name, "c": cls, "a": aliases})
        contra = [
            ("Nitrate", "PDE5 Inhibitor", "CONTRAINDICATED", "Fatal refractory hypotension"),
            ("ACE Inhibitor", "Potassium-Sparing Diuretic", "MAJOR", "Severe hyperkalemia risk"),
        ]
        for a, b, sev, eff in contra:
            self._q(g, "MATCH (a:DrugClass {name:$a}),(b:DrugClass {name:$b}) "
                       "MERGE (a)-[r:CONTRAINDICATED_WITH]->(b) SET r.severity=$s, r.effect=$e",
                    {"a": a, "b": b, "s": sev, "e": eff})

    def _seed_hospital_brain(self) -> None:
        g = BRAIN_GRAPH
        depts = [
            ("Cardiology", "Dr. Meera Iyer"),
            ("Endocrinology", "Dr. Rohan Kapoor"),
            ("Primary Care", "Dr. Sarah Elizabeth"),
        ]
        for d, ph in depts:
            self._q(g, "MERGE (d:Department {name:$d}) MERGE (p:Physician {name:$p}) MERGE (d)-[:SUPERVISED_BY]->(p)", {"d": d, "p": ph})
        cpts = [("93000", "12-lead ECG with interpretation"), ("99214", "Office visit, moderate complexity"),
                ("82947", "Quantitative blood glucose")]
        for c, n in cpts:
            self._q(g, "MERGE (c:CPT {code:$c}) SET c.name=$n", {"c": c, "n": n})
        reasons = [("CO-50", "Not deemed a medical necessity"),
                   ("CO-97", "Payment included in allowance for another service (bundling)"),
                   ("CO-16", "Claim lacks information needed for adjudication")]
        for c, t in reasons:
            self._q(g, "MERGE (r:DenialReason {code:$c}) SET r.name=$t", {"c": c, "t": t})
        bills = [("Cardiology", "93000", 412), ("Cardiology", "99214", 655),
                 ("Endocrinology", "82947", 538), ("Endocrinology", "99214", 470),
                 ("Primary Care", "99214", 901), ("Primary Care", "93000", 90)]
        for d, c, n in bills:
            self._q(g, "MATCH (d:Department {name:$d}),(c:CPT {code:$c}) MERGE (d)-[b:FREQUENTLY_BILLS]->(c) SET b.count=$n",
                    {"d": d, "c": c, "n": n})
        denials = [("93000", "CO-50", 38), ("93000", "CO-97", 21), ("99214", "CO-16", 44), ("82947", "CO-50", 12)]
        for c, r, n in denials:
            self._q(g, "MATCH (c:CPT {code:$c}),(r:DenialReason {code:$r}) MERGE (c)-[x:DENIED_FOR]->(r) SET x.count=$n",
                    {"c": c, "r": r, "n": n})

    def _seed_patient_p9801(self) -> None:
        # Only seed once; later encounters recorded by the app must not be duplicated or reset.
        rows = self._q(f"patient_P-9801", "MATCH (p:Patient {id:'P-9801'}) RETURN count(p)")
        if rows and rows[0][0]:
            return
        self.record_encounter(
            "P-9801", "ENC-01", "Erectile dysfunction (N52.9)", ["Sildenafil 50 mg"],
            patient_name="Robert Vance", encounter_date="2026-03-14",
        )

    # ------------------------------------------------------------------ Track 01
    def verify_medical_necessity(self, symptoms: List[str], procedure_code: str) -> Dict[str, Any]:
        """Multi-hop proof: Symptom -> Diagnosis -> Procedure. Returns verified flag + trace_path."""
        base = {"procedure_code": procedure_code, "symptoms": symptoms, "engine": "falkordb"}
        try:
            rows = self._q(RULES_GRAPH, TRACE_QUERY,
                           {"symptoms": [s.lower() for s in symptoms], "code": procedure_code})
        except Exception as e:
            return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code, "error": str(e)}
        if rows:
            trace, icd, cpt = rows[0]
            return {**base, "verified": True, "trace_path": trace, "icd": icd, "cpt": cpt}
        return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code}

    def verify_necessity_from_diagnoses(self, icd_codes: List[str], procedure_code: str) -> Dict[str, Any]:
        """Fallback proof when no symptom is documented: Diagnosis -> Procedure (2-node trace)."""
        base = {"procedure_code": procedure_code, "symptoms": [], "engine": "falkordb", "basis": "diagnosis"}
        try:
            rows = self._q(
                RULES_GRAPH,
                "MATCH path = (d:Diagnosis)-[:SUPPORTS_NECESSITY]->(p:Procedure {code: $code}) WHERE d.code IN $icd "
                "RETURN [n IN nodes(path) | coalesce(n.name, n.code)] AS trace_path, d.code AS icd, p.code AS cpt "
                "ORDER BY d.code LIMIT 1",
                {"icd": icd_codes, "code": procedure_code},
            )
        except Exception as e:
            return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code, "error": str(e)}
        if rows:
            trace, icd, cpt = rows[0]
            return {**base, "verified": True, "trace_path": trace, "icd": icd, "cpt": cpt}
        return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code}

    def infer_department(self, cpt_codes: List[str]) -> Optional[str]:
        try:
            rows = self._q(BRAIN_GRAPH,
                           "MATCH (d:Department)-[b:FREQUENTLY_BILLS]->(c:CPT) WHERE c.code IN $c "
                           "RETURN d.name, sum(b.count) AS n ORDER BY n DESC LIMIT 1", {"c": cpt_codes})
        except Exception:
            return None
        return rows[0][0] if rows else None

    def extract_symptoms(self, text: str) -> List[str]:
        """Graph-driven extraction: match Symptom names/aliases from the rules graph against free text."""
        low = (text or "").lower()
        try:
            rows = self._q(RULES_GRAPH, "MATCH (s:Symptom) RETURN s.name, s.aliases")
        except Exception:
            return []
        found = [name for name, aliases in rows if any(a in low for a in (aliases or [name]))]
        return found

    def check_unbundling(self, cpt_codes: List[str]) -> List[Dict[str, Any]]:
        """Flags component codes billed together with their comprehensive code (e.g. 93000 + 93010)."""
        if len(cpt_codes) < 2:
            return []
        try:
            rows = self._q(
                RULES_GRAPH,
                "MATCH path=(a:Procedure)-[:INCLUDES]->(b:Procedure) WHERE a.code IN $c AND b.code IN $c "
                "RETURN a.code, b.code, [n IN nodes(path) | n.code] AS trace_path",
                {"c": cpt_codes},
            )
        except Exception:
            return []
        return [{"comprehensive": a, "component": b, "trace_path": t,
                 "message": f"CPT {b} is already included in {a}; billing both is unbundling (CARC CO-97)."}
                for a, b, t in rows]

    # ------------------------------------------------------------------ Track 02
    def _resolve_drug(self, med_text: str) -> Optional[str]:
        rows = self._q(
            RULES_GRAPH,
            "MATCH (d:Drug) WHERE any(a IN d.aliases WHERE $m CONTAINS a) RETURN d.name LIMIT 1",
            {"m": (med_text or "").lower()},
        )
        return rows[0][0] if rows else None

    def check_cross_session_contraindications(self, patient_id: str, new_medication: str) -> List[Dict[str, Any]]:
        """Active meds in patient_<id> (from past encounters) vs contraindication edges in clinical_rules."""
        pid = safe_patient_id(patient_id)
        try:
            new_drug = self._resolve_drug(new_medication)
            if not new_drug:
                return []
            active = self._q(
                f"patient_{pid}",
                "MATCH (p:Patient {id:$pid})-[:HAS_ACTIVE_MED]->(m:Medication)<-[:PRESCRIBED]-(e:Encounter) "
                "RETURN m.name, e.id, e.date",
                {"pid": pid},
            )
        except Exception as e:
            logger.warning("contraindication check skipped: %s", e)
            return []
        by_drug: Dict[str, Any] = {}
        for med_name, enc_id, enc_date in active:
            drug = self._resolve_drug(med_name)
            if drug:
                by_drug[drug] = (med_name, enc_id, enc_date)
        if not by_drug:
            return []
        rows = self._q(
            RULES_GRAPH,
            "MATCH path=(a:Drug {name:$new})-[:IN_CLASS]->(:DrugClass)-[r:CONTRAINDICATED_WITH]-(:DrugClass)<-[:IN_CLASS]-(b:Drug) "
            "WHERE b.name IN $active "
            "RETURN b.name, r.severity, r.effect, [n IN nodes(path) | n.name] AS trace_path",
            {"new": new_drug, "active": list(by_drug)},
        )
        out = []
        for b, sev, eff, trace in rows:
            med_name, enc_id, enc_date = by_drug[b]
            out.append({
                "patient_id": pid, "new_medication": new_medication, "conflicting_medication": med_name,
                "from_encounter": enc_id, "encounter_date": enc_date, "severity": sev, "effect": eff,
                "trace_path": trace,
                "message": f"{new_medication} conflicts with active {med_name} (started {enc_id}, {enc_date}): {eff}.",
            })
        return out

    def record_encounter(self, patient_id: str, encounter_id: str, condition: str, new_meds: List[str],
                         patient_name: str = "", encounter_date: Optional[str] = None) -> Dict[str, Any]:
        """Commit encounter memory into the patient's isolated graph (idempotent via MERGE)."""
        from datetime import date

        pid = safe_patient_id(patient_id)
        gname = f"patient_{pid}"
        edate = encounter_date or date.today().isoformat()
        self._q(gname, "MERGE (p:Patient {id:$pid}) SET p.name = coalesce($name, p.name)",
                {"pid": pid, "name": patient_name or None})
        self._q(gname, "MATCH (p:Patient {id:$pid}) MERGE (p)-[:HAD_ENCOUNTER]->(e:Encounter {id:$eid}) SET e.date=$d",
                {"pid": pid, "eid": encounter_id, "d": edate})
        for cond in [c.strip() for c in (condition or "").split(";") if c.strip()]:
            self._q(gname, "MATCH (e:Encounter {id:$eid}) MERGE (c:Condition {name:$c}) MERGE (e)-[:DIAGNOSED]->(c)",
                    {"eid": encounter_id, "c": cond})
        for med in new_meds or []:
            self._q(gname,
                    "MATCH (p:Patient {id:$pid}),(e:Encounter {id:$eid}) MERGE (m:Medication {name:$m}) "
                    "MERGE (e)-[:PRESCRIBED]->(m) MERGE (p)-[:HAS_ACTIVE_MED]->(m)",
                    {"pid": pid, "eid": encounter_id, "m": med})
        return {"patient_graph": gname, "encounter_id": encounter_id, "medications": new_meds or []}

    def get_patient_memory(self, patient_id: str) -> Dict[str, Any]:
        pid = safe_patient_id(patient_id)
        gname = f"patient_{pid}"
        try:
            enc = self._q(gname, "MATCH (p:Patient {id:$pid})-[:HAD_ENCOUNTER]->(e:Encounter) "
                                 "OPTIONAL MATCH (e)-[:DIAGNOSED]->(c:Condition) OPTIONAL MATCH (e)-[:PRESCRIBED]->(m:Medication) "
                                 "RETURN e.id, e.date, collect(DISTINCT c.name), collect(DISTINCT m.name) ORDER BY e.date",
                          {"pid": pid})
            active = self._q(gname, "MATCH (:Patient {id:$pid})-[:HAS_ACTIVE_MED]->(m:Medication) RETURN m.name", {"pid": pid})
        except Exception as e:
            return {"patient_id": pid, "graph": gname, "encounters": [], "active_medications": [], "error": str(e)}
        return {"patient_id": pid, "graph": gname,
                "encounters": [{"id": i, "date": d, "conditions": c, "medications": m} for i, d, c, m in enc],
                "active_medications": [r[0] for r in active]}

    # ------------------------------------------------------------------ Track 03
    def get_department_compliance(self, dept_name: str) -> List[Dict[str, Any]]:
        """Institutional brain traversal: Department -> CPT -> DenialReason (+ supervising physician)."""
        try:
            sup = self._q(BRAIN_GRAPH, "MATCH (:Department {name:$d})-[:SUPERVISED_BY]->(p:Physician) RETURN p.name", {"d": dept_name})
            rows = self._q(
                BRAIN_GRAPH,
                "MATCH path=(d:Department {name:$d})-[b:FREQUENTLY_BILLS]->(c:CPT)-[x:DENIED_FOR]->(r:DenialReason) "
                "RETURN c.code, c.name, b.count, r.code, r.name, x.count, [n IN nodes(path) | coalesce(n.name, n.code)] "
                "ORDER BY x.count DESC",
                {"d": dept_name},
            )
        except Exception as e:
            logger.warning("department compliance unavailable: %s", e)
            return []
        physician = sup[0][0] if sup else None
        return [{
            "department": dept_name, "supervising_physician": physician, "cpt": c, "cpt_name": cn,
            "billed_count": bc, "denial_code": rc, "denial_reason": rn, "denial_count": xc,
            "denial_rate_pct": round(100.0 * xc / bc, 1) if bc else 0.0, "trace_path": t,
        } for c, cn, bc, rc, rn, xc, t in rows]


falkor_service = FalkorHealthService()
