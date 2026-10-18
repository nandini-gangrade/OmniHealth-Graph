"""FalkorDB service: the graph is the context, reasoning and memory layer.

Three graph families live in one FalkorDB instance:

* ``clinical_rules``   - Track 01. Symptom -> Diagnosis -> Procedure necessity, NCCI-style bundling,
                         drug-class contraindications.
* ``patient_<id>``     - Track 02. One isolated subgraph per patient (multi-tenant memory):
                         encounters, conditions and active medications across sessions.
* ``hospital_brain``   - Track 03. Departments, supervising physicians, frequently billed CPTs and
                         historical denial reasons.

Every decision method returns a deterministic ``trace_path`` built from ``nodes(path)``.
Includes a comprehensive zero-latency in-memory graph fallback engine so that if FalkorDB
(Docker or Cloud) is unreachable or times out, all clinical provenance trace pills,
red contraindication alerts, NCCI unbundling warnings, and locked approval gates
function flawlessly at 0ms connection latency.

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

# ----------------------------------------------------------------------
# Seeded knowledge graph structures (used both for FalkorDB seeding & fallback)
# ----------------------------------------------------------------------
_IN_MEM_DIAGNOSES = [
    ("I20.9", "Angina pectoris, unspecified"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("I10", "Essential (primary) hypertension"),
    ("R07.9", "Chest pain, unspecified"),
]

_IN_MEM_PROCEDURES = [
    ("93000", "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report"),
    ("93005", "Electrocardiogram, tracing only, without interpretation and report"),
    ("93010", "Electrocardiogram, interpretation and report only"),
    ("99214", "Office/outpatient visit, established patient, moderate medical decision making"),
    ("82947", "Glucose; quantitative, blood (except reagent strip)"),
]

_IN_MEM_SYMPTOMS = [
    ("chest pain", ["chest pain", "pain in my chest", "pain in the chest"]),
    ("chest tightness", [
        "chest tight", "tight chest", "chest feels heavy", "chest heaviness",
        "chest pressure", "tightness in my chest", "chest tightness", "tightness",
    ]),
    ("exertional chest pain", [
        "chest pain on exertion", "chest pain when i walk", "pain when climbing stairs",
        "chest pain with exertion", "exertional chest", "climb stairs", "climbing stairs",
    ]),
    ("polyuria", ["polyuria", "urinating a lot", "frequent urination"]),
    ("polydipsia", ["polydipsia", "very thirsty", "excessive thirst"]),
    ("elevated blood pressure", ["high blood pressure", "elevated blood pressure", "hypertension"]),
]

_IN_MEM_INDICATES = [
    ("chest pain", "R07.9"),
    ("chest tightness", "R07.9"),
    ("chest tightness", "I20.9"),
    ("exertional chest pain", "I20.9"),
    ("exertional chest pain", "R07.9"),
    ("polyuria", "E11.9"),
    ("polydipsia", "E11.9"),
    ("elevated blood pressure", "I10"),
]

_IN_MEM_NECESSITY = [
    ("R07.9", "93000"),
    ("I20.9", "93000"),
    ("E11.9", "82947"),
    ("E11.9", "99214"),
    ("I10", "99214"),
]

_IN_MEM_BUNDLING = [
    ("93000", "93005"),
    ("93000", "93010"),
]

_IN_MEM_DRUGS = [
    ("nitroglycerin", "Nitrate", ["nitroglycerin", "nitrostat", "glyceryl trinitrate", "gtn"]),
    ("sildenafil", "PDE5 Inhibitor", ["sildenafil", "viagra", "revatio"]),
    ("lisinopril", "ACE Inhibitor", ["lisinopril", "zestril", "prinivil"]),
    ("spironolactone", "Potassium-Sparing Diuretic", ["spironolactone", "aldactone"]),
    ("amlodipine", "Calcium Channel Blocker", ["amlodipine", "norvasc"]),
    ("albuterol", "Beta-2 Agonist", ["albuterol", "salbutamol", "ventolin", "proair"]),
]

_IN_MEM_CONTRAINDICATIONS = [
    ("Nitrate", "PDE5 Inhibitor", "CONTRAINDICATED", "Fatal refractory hypotension"),
    ("ACE Inhibitor", "Potassium-Sparing Diuretic", "MAJOR", "Severe hyperkalemia risk"),
]

_IN_MEM_DEPTS = {
    "Cardiology": "Dr. Meera Iyer",
    "Endocrinology": "Dr. Rohan Kapoor",
    "Primary Care": "Dr. Sarah Elizabeth",
}

_IN_MEM_CPT_NAMES = {
    "93000": "12-lead ECG with interpretation",
    "99214": "Office visit, moderate complexity",
    "82947": "Quantitative blood glucose",
}

_IN_MEM_REASON_NAMES = {
    "CO-50": "Not deemed a medical necessity",
    "CO-97": "Payment included in allowance for another service (bundling)",
    "CO-16": "Claim lacks information needed for adjudication",
}

_IN_MEM_BILLS = [
    ("Cardiology", "93000", 412),
    ("Cardiology", "99214", 655),
    ("Endocrinology", "82947", 538),
    ("Endocrinology", "99214", 470),
    ("Primary Care", "99214", 901),
    ("Primary Care", "93000", 90),
]

_IN_MEM_DENIALS = [
    ("93000", "CO-50", 38),
    ("93000", "CO-97", 21),
    ("99214", "CO-16", 44),
    ("82947", "CO-50", 12),
]


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
        self.available: bool = True  # Always available (either live FalkorDB or zero-latency in-memory fallback)
        self.is_real_db: bool = False
        self.last_error: Optional[str] = None
        self._connect_attempted: bool = False

        # Multi-tenant in-memory patient memory store
        self._mem_patient_encounters: Dict[str, List[Dict[str, Any]]] = {}
        self._mem_patient_active_meds: Dict[str, List[str]] = {}
        self._mem_patient_names: Dict[str, str] = {}
        self._init_in_memory_state()

    def _init_in_memory_state(self) -> None:
        """Seed initial patient P-9801 (Robert Vance) into memory store."""
        if "P-9801" not in self._mem_patient_encounters:
            self._mem_patient_names["P-9801"] = "Robert Vance"
            self._mem_patient_encounters["P-9801"] = [
                {
                    "id": "ENC-01",
                    "date": "2026-03-14",
                    "conditions": ["Erectile dysfunction (N52.9)"],
                    "medications": ["Sildenafil 50 mg"],
                }
            ]
            self._mem_patient_active_meds["P-9801"] = ["Sildenafil 50 mg"]

    # ------------------------------------------------------------------ connection
    def connect(self, force: bool = False):
        if self._db is not None and not force:
            return self._db
        if self._connect_attempted and not force:
            return self._db  # returns None if offline, avoiding repetitive network timeouts

        self._connect_attempted = True

        host = settings.FALKORDB_HOST or "localhost"
        port = int(settings.FALKORDB_PORT or 6379)
        password = (settings.FALKORDB_PASSWORD or "").strip() or None
        username = (getattr(settings, "FALKORDB_USERNAME", None) or "").strip() or None
        ssl_enabled = bool(
            getattr(settings, "FALKORDB_SSL", False)
            or (host != "localhost" and (host.endswith(".falkordb.cloud") or port == 6380))
        )

        try:
            from falkordb import FalkorDB

            logger.info("Connecting to FalkorDB at %s:%s (ssl=%s, auth=%s)...",
                        host, port, ssl_enabled, bool(password))
            db = FalkorDB(
                host=host,
                port=port,
                password=password,
                username=username,
                ssl=ssl_enabled,
                socket_connect_timeout=2.0,
                socket_timeout=2.5,
            )
            db.list_graphs()  # round trip test
            self._db = db
            self.available = True
            self.is_real_db = True
            self.last_error = None
            logger.info("Connected successfully to live FalkorDB instance at %s:%s", host, port)
        except Exception as e:
            # If standard connection failed on a cloud host without SSL, try SSL once
            if not ssl_enabled and host != "localhost":
                try:
                    from falkordb import FalkorDB

                    logger.info("Retrying FalkorDB cloud connection at %s:%s with SSL enabled...", host, port)
                    db = FalkorDB(
                        host=host,
                        port=port,
                        password=password,
                        username=username,
                        ssl=True,
                        socket_connect_timeout=2.0,
                        socket_timeout=2.5,
                    )
                    db.list_graphs()
                    self._db = db
                    self.available = True
                    self.is_real_db = True
                    self.last_error = None
                    logger.info("Connected successfully to live FalkorDB instance at %s:%s (ssl=True)", host, port)
                    return self._db
                except Exception as e2:
                    e = e2

            self.available = True  # Available via instant in-memory graph fallback
            self.is_real_db = False
            self.last_error = str(e)
            self._db = None
            logger.warning(
                "FalkorDB unreachable at %s:%s (%s). Zero-latency in-memory graph fallback active.",
                host, port, e,
            )
        return self._db

    def _graph(self, name: str):
        if not self.is_real_db:
            return None
        db = self.connect()
        return db.select_graph(name) if db is not None else None

    def _q(self, graph_name: str, query: str, params: Optional[dict] = None) -> List[list]:
        g = self._graph(graph_name)
        if g is None:
            raise RuntimeError(f"FalkorDB unavailable: {self.last_error}")
        return g.query(query, params or {}).result_set

    def status(self) -> Dict[str, Any]:
        if not self._connect_attempted:
            self.connect()

        graphs: List[str] = ["clinical_rules", "hospital_brain", "patient_P-9801"]
        for pid in self._mem_patient_encounters:
            gname = f"patient_{pid}"
            if gname not in graphs:
                graphs.append(gname)

        if self.is_real_db and self._db is not None:
            try:
                graphs = sorted(list(set(graphs) | set(self._db.list_graphs())))
            except Exception:
                pass

        return {
            "engine": "falkordb",
            "available": True,
            "connected_to_falkordb": self.is_real_db,
            "fallback_mode": not self.is_real_db,
            "graphs": sorted(graphs),
            "error": self.last_error if not self.is_real_db else None,
        }

    # ------------------------------------------------------------------ seeding
    def init_databases(self) -> Dict[str, Any]:
        """Idempotent: every write uses MERGE so restarts never duplicate the seed."""
        self._init_in_memory_state()
        db = self.connect()
        if db is not None:
            try:
                self._seed_clinical_rules()
                self._seed_hospital_brain()
                self._seed_patient_p9801()
                logger.info("Live FalkorDB seeded: clinical_rules, hospital_brain, patient_P-9801")
            except Exception as e:
                logger.warning("FalkorDB live seeding failed (%s). Continuing with in-memory graph.", e)
        else:
            logger.info("FalkorDB in-memory fallback active: clinical_rules, hospital_brain, patient_P-9801 ready.")
        return {"seeded": True, "engine": "falkordb" if self.is_real_db else "in-memory-fallback", "graphs": self.status()["graphs"]}

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

        # ICD-10-CM diagnoses
        for code, name in _IN_MEM_DIAGNOSES:
            self._q(g, "MERGE (d:Diagnosis {code:$c}) SET d.description=$n", {"c": code, "n": name})

        # CPT procedures
        for code, name in _IN_MEM_PROCEDURES:
            self._q(g, "MERGE (p:Procedure {code:$c}) SET p.description=$n", {"c": code, "n": name})

        # Symptoms
        for name, aliases in _IN_MEM_SYMPTOMS:
            self._q(g, "MERGE (s:Symptom {name:$n}) SET s.aliases=$a", {"n": name, "a": aliases})

        # Indicates edges
        for s, d in _IN_MEM_INDICATES:
            self._q(g, "MATCH (s:Symptom {name:$s}),(d:Diagnosis {code:$d}) MERGE (s)-[:INDICATES]->(d)", {"s": s, "d": d})

        # Medical necessity edges
        for d, p in _IN_MEM_NECESSITY:
            self._q(g, "MATCH (d:Diagnosis {code:$d}),(p:Procedure {code:$p}) MERGE (d)-[:SUPPORTS_NECESSITY]->(p)", {"d": d, "p": p})

        # Bundling edges
        for comp in ("93005", "93010"):
            self._q(g, "MATCH (a:Procedure {code:'93000'}),(b:Procedure {code:$b}) MERGE (a)-[:INCLUDES]->(b)", {"b": comp})

        # Drugs and classes
        for name, cls, aliases in _IN_MEM_DRUGS:
            self._q(g, "MERGE (c:DrugClass {name:$c}) MERGE (d:Drug {name:$n}) SET d.aliases=$a MERGE (d)-[:IN_CLASS]->(c)",
                    {"n": name, "c": cls, "a": aliases})

        # Contraindication edges
        for a, b, sev, eff in _IN_MEM_CONTRAINDICATIONS:
            self._q(g, "MATCH (a:DrugClass {name:$a}),(b:DrugClass {name:$b}) "
                       "MERGE (a)-[r:CONTRAINDICATED_WITH]->(b) SET r.severity=$s, r.effect=$e",
                    {"a": a, "b": b, "s": sev, "e": eff})

    def _seed_hospital_brain(self) -> None:
        g = BRAIN_GRAPH
        for d, ph in _IN_MEM_DEPTS.items():
            self._q(g, "MERGE (d:Department {name:$d}) MERGE (p:Physician {name:$p}) MERGE (d)-[:SUPERVISED_BY]->(p)", {"d": d, "p": ph})
        for c, n in _IN_MEM_CPT_NAMES.items():
            self._q(g, "MERGE (c:CPT {code:$c}) SET c.name=$n", {"c": c, "n": n})
        for c, t in _IN_MEM_REASON_NAMES.items():
            self._q(g, "MERGE (r:DenialReason {code:$c}) SET r.name=$t", {"c": c, "t": t})
        for d, c, n in _IN_MEM_BILLS:
            self._q(g, "MATCH (d:Department {name:$d}),(c:CPT {code:$c}) MERGE (d)-[b:FREQUENTLY_BILLS]->(c) SET b.count=$n",
                    {"d": d, "c": c, "n": n})
        for c, r, n in _IN_MEM_DENIALS:
            self._q(g, "MATCH (c:CPT {code:$c}),(r:DenialReason {code:$r}) MERGE (c)-[x:DENIED_FOR]->(r) SET x.count=$n",
                    {"c": c, "r": r, "n": n})

    def _seed_patient_p9801(self) -> None:
        try:
            rows = self._q("patient_P-9801", "MATCH (p:Patient {id:'P-9801'}) RETURN count(p)")
            if rows and rows[0][0]:
                return
        except Exception:
            pass
        self.record_encounter(
            "P-9801", "ENC-01", "Erectile dysfunction (N52.9)", ["Sildenafil 50 mg"],
            patient_name="Robert Vance", encounter_date="2026-03-14",
        )

    # ------------------------------------------------------------------ Track 01
    def extract_symptoms(self, text: str) -> List[str]:
        """Graph-driven extraction: match Symptom names/aliases from the rules graph against free text."""
        low = (text or "").lower()
        if self.is_real_db:
            try:
                rows = self._q(RULES_GRAPH, "MATCH (s:Symptom) RETURN s.name, s.aliases")
                found = [name for name, aliases in rows if any(a in low for a in (aliases or [name]))]
                if found:
                    return found
            except Exception as e:
                logger.warning("extract_symptoms error from live FalkorDB: %s. Using in-memory fallback.", e)

        # In-memory graph traversal
        found = [
            name for name, aliases in _IN_MEM_SYMPTOMS
            if any(a.lower() in low for a in aliases)
        ]
        return found

    def verify_medical_necessity(self, symptoms: List[str], procedure_code: str) -> Dict[str, Any]:
        """Multi-hop proof: Symptom -> Diagnosis -> Procedure. Returns verified flag + trace_path."""
        base = {"procedure_code": procedure_code, "symptoms": symptoms, "engine": "falkordb"}
        if self.is_real_db:
            try:
                rows = self._q(RULES_GRAPH, TRACE_QUERY,
                               {"symptoms": [s.lower() for s in symptoms], "code": procedure_code})
                if rows:
                    trace, icd, cpt = rows[0]
                    return {**base, "verified": True, "trace_path": trace, "icd": icd, "cpt": cpt}
                return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code}
            except Exception as e:
                logger.warning("verify_medical_necessity error on live FalkorDB: %s. Using in-memory fallback.", e)

        # In-memory multi-hop traversal: (Symptom)-[:INDICATES]->(Diagnosis)-[:SUPPORTS_NECESSITY]->(Procedure)
        sym_lower = {s.lower() for s in symptoms}
        matches = []
        for s_name, d_code in _IN_MEM_INDICATES:
            if s_name.lower() in sym_lower:
                for diag, proc in _IN_MEM_NECESSITY:
                    if diag == d_code and proc == procedure_code:
                        matches.append((s_name, d_code, proc))

        if matches:
            matches.sort(key=lambda m: m[1])  # stable order by diagnosis code
            s_name, d_code, proc = matches[0]
            return {**base, "verified": True, "trace_path": [s_name, d_code, proc], "icd": d_code, "cpt": proc}

        return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code}

    def verify_necessity_from_diagnoses(self, icd_codes: List[str], procedure_code: str) -> Dict[str, Any]:
        """Fallback proof when no symptom is documented: Diagnosis -> Procedure (2-node trace)."""
        base = {"procedure_code": procedure_code, "symptoms": [], "engine": "falkordb", "basis": "diagnosis"}
        if self.is_real_db:
            try:
                rows = self._q(
                    RULES_GRAPH,
                    "MATCH path = (d:Diagnosis)-[:SUPPORTS_NECESSITY]->(p:Procedure {code: $code}) WHERE d.code IN $icd "
                    "RETURN [n IN nodes(path) | coalesce(n.name, n.code)] AS trace_path, d.code AS icd, p.code AS cpt "
                    "ORDER BY d.code LIMIT 1",
                    {"icd": icd_codes, "code": procedure_code},
                )
                if rows:
                    trace, icd, cpt = rows[0]
                    return {**base, "verified": True, "trace_path": trace, "icd": icd, "cpt": cpt}
                return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code}
            except Exception as e:
                logger.warning("verify_necessity_from_diagnoses error on live FalkorDB: %s. Using in-memory fallback.", e)

        # In-memory proof: (Diagnosis)-[:SUPPORTS_NECESSITY]->(Procedure)
        icd_set = set(icd_codes)
        matches = [d for d, p in _IN_MEM_NECESSITY if d in icd_set and p == procedure_code]
        if matches:
            matches.sort()
            d_code = matches[0]
            return {**base, "verified": True, "trace_path": [d_code, procedure_code], "icd": d_code, "cpt": procedure_code}

        return {**base, "verified": False, "trace_path": [], "icd": None, "cpt": procedure_code}

    def infer_department(self, cpt_codes: List[str]) -> Optional[str]:
        if self.is_real_db:
            try:
                rows = self._q(BRAIN_GRAPH,
                               "MATCH (d:Department)-[b:FREQUENTLY_BILLS]->(c:CPT) WHERE c.code IN $c "
                               "RETURN d.name, sum(b.count) AS n ORDER BY n DESC LIMIT 1", {"c": cpt_codes})
                if rows:
                    return rows[0][0]
            except Exception as e:
                logger.warning("infer_department error on live FalkorDB: %s. Using in-memory fallback.", e)

        # In-memory inference
        dept_counts: Dict[str, int] = {}
        cpt_set = set(cpt_codes)
        for dept, cpt, count in _IN_MEM_BILLS:
            if cpt in cpt_set:
                dept_counts[dept] = dept_counts.get(dept, 0) + count

        if dept_counts:
            return max(dept_counts.items(), key=lambda x: x[1])[0]
        return "Cardiology" if "93000" in cpt_set else None

    def check_unbundling(self, cpt_codes: List[str]) -> List[Dict[str, Any]]:
        """Flags component codes billed together with their comprehensive code (e.g. 93000 + 93010)."""
        if len(cpt_codes) < 2:
            return []
        if self.is_real_db:
            try:
                rows = self._q(
                    RULES_GRAPH,
                    "MATCH path=(a:Procedure)-[:INCLUDES]->(b:Procedure) WHERE a.code IN $c AND b.code IN $c "
                    "RETURN a.code, b.code, [n IN nodes(path) | n.code] AS trace_path",
                    {"c": cpt_codes},
                )
                if rows:
                    return [{"comprehensive": a, "component": b, "trace_path": t,
                             "message": f"CPT {b} is already included in {a}; billing both is unbundling (CARC CO-97)."}
                            for a, b, t in rows]
            except Exception as e:
                logger.warning("check_unbundling error on live FalkorDB: %s. Using in-memory fallback.", e)

        # In-memory bundling rules
        cpt_set = set(cpt_codes)
        out = []
        for comp_a, comp_b in _IN_MEM_BUNDLING:
            if comp_a in cpt_set and comp_b in cpt_set:
                out.append({
                    "comprehensive": comp_a,
                    "component": comp_b,
                    "trace_path": [comp_a, comp_b],
                    "message": f"CPT {comp_b} is already included in {comp_a}; billing both is unbundling (CARC CO-97)."
                })
        return out

    # ------------------------------------------------------------------ Track 02
    def _resolve_drug(self, med_text: str) -> Optional[str]:
        low = (med_text or "").lower()
        if self.is_real_db:
            try:
                rows = self._q(
                    RULES_GRAPH,
                    "MATCH (d:Drug) WHERE any(a IN d.aliases WHERE $m CONTAINS a) RETURN d.name LIMIT 1",
                    {"m": low},
                )
                if rows:
                    return rows[0][0]
            except Exception:
                pass

        # In-memory drug catalog resolution
        for drug_name, _cls, aliases in _IN_MEM_DRUGS:
            if any(a.lower() in low for a in aliases):
                return drug_name
        return None

    def check_cross_session_contraindications(self, patient_id: str, new_medication: str) -> List[Dict[str, Any]]:
        """Active meds in patient_<id> (from past encounters) vs contraindication edges in clinical_rules."""
        pid = safe_patient_id(patient_id)
        new_drug = self._resolve_drug(new_medication)
        if not new_drug:
            return []

        # Try live FalkorDB if available
        if self.is_real_db:
            try:
                active = self._q(
                    f"patient_{pid}",
                    "MATCH (p:Patient {id:$pid})-[:HAS_ACTIVE_MED]->(m:Medication)<-[:PRESCRIBED]-(e:Encounter) "
                    "RETURN m.name, e.id, e.date",
                    {"pid": pid},
                )
                by_drug: Dict[str, Any] = {}
                for med_name, enc_id, enc_date in active:
                    drug = self._resolve_drug(med_name)
                    if drug:
                        by_drug[drug] = (med_name, enc_id, enc_date)
                if by_drug:
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
                    if out:
                        return out
            except Exception as e:
                logger.warning("Live FalkorDB contraindication check error: %s. Using in-memory fallback.", e)

        # In-memory graph traversal for cross-session contraindications
        drug_to_class = {d[0]: d[1] for d in _IN_MEM_DRUGS}
        new_class = drug_to_class.get(new_drug)
        if not new_class:
            return []

        encounters = self._mem_patient_encounters.get(pid, [])
        active_meds = self._mem_patient_active_meds.get(pid, [])

        by_drug_mem: Dict[str, Any] = {}
        for enc in encounters:
            for m in enc.get("medications", []):
                resolved = self._resolve_drug(m)
                if resolved:
                    by_drug_mem[resolved] = (m, enc.get("id", "ENC-01"), enc.get("date", "2026-03-14"))

        for m in active_meds:
            resolved = self._resolve_drug(m)
            if resolved and resolved not in by_drug_mem:
                by_drug_mem[resolved] = (m, "ENC-01", "2026-03-14")

        out = []
        for active_drug, (med_name, enc_id, enc_date) in by_drug_mem.items():
            active_class = drug_to_class.get(active_drug)
            if not active_class:
                continue
            for class_a, class_b, sev, eff in _IN_MEM_CONTRAINDICATIONS:
                if (new_class == class_a and active_class == class_b) or (new_class == class_b and active_class == class_a):
                    trace_path = [new_drug, new_class, active_class, active_drug]
                    out.append({
                        "patient_id": pid,
                        "new_medication": new_medication,
                        "conflicting_medication": med_name,
                        "from_encounter": enc_id,
                        "encounter_date": enc_date,
                        "severity": sev,
                        "effect": eff,
                        "trace_path": trace_path,
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

        # Update in-memory patient graph state
        if pid not in self._mem_patient_encounters:
            self._mem_patient_encounters[pid] = []
        if pid not in self._mem_patient_active_meds:
            self._mem_patient_active_meds[pid] = []
        if patient_name:
            self._mem_patient_names[pid] = patient_name

        cond_list = [c.strip() for c in (condition or "").split(";") if c.strip()]
        existing = [e for e in self._mem_patient_encounters[pid] if e.get("id") == encounter_id]
        if not existing:
            self._mem_patient_encounters[pid].append({
                "id": encounter_id,
                "date": edate,
                "conditions": cond_list,
                "medications": list(new_meds or []),
            })
        else:
            existing[0]["conditions"] = list(set(existing[0]["conditions"] + cond_list))
            existing[0]["medications"] = list(set(existing[0]["medications"] + (new_meds or [])))

        for m in (new_meds or []):
            if m not in self._mem_patient_active_meds[pid]:
                self._mem_patient_active_meds[pid].append(m)

        # If live FalkorDB instance is reachable, write MERGE nodes
        if self.is_real_db:
            try:
                self._q(gname, "MERGE (p:Patient {id:$pid}) SET p.name = coalesce($name, p.name)",
                        {"pid": pid, "name": patient_name or None})
                self._q(gname, "MATCH (p:Patient {id:$pid}) MERGE (p)-[:HAD_ENCOUNTER]->(e:Encounter {id:$eid}) SET e.date=$d",
                        {"pid": pid, "eid": encounter_id, "d": edate})
                for cond in cond_list:
                    self._q(gname, "MATCH (e:Encounter {id:$eid}) MERGE (c:Condition {name:$c}) MERGE (e)-[:DIAGNOSED]->(c)",
                            {"eid": encounter_id, "c": cond})
                for med in new_meds or []:
                    self._q(gname,
                            "MATCH (p:Patient {id:$pid}),(e:Encounter {id:$eid}) MERGE (m:Medication {name:$m}) "
                            "MERGE (e)-[:PRESCRIBED]->(m) MERGE (p)-[:HAS_ACTIVE_MED]->(m)",
                            {"pid": pid, "eid": encounter_id, "m": med})
            except Exception as e:
                logger.warning("Live FalkorDB record_encounter error: %s. Encounter stored in memory.", e)

        return {"patient_graph": gname, "encounter_id": encounter_id, "medications": new_meds or []}

    def get_patient_memory(self, patient_id: str) -> Dict[str, Any]:
        pid = safe_patient_id(patient_id)
        gname = f"patient_{pid}"
        if self.is_real_db:
            try:
                enc = self._q(gname, "MATCH (p:Patient {id:$pid})-[:HAD_ENCOUNTER]->(e:Encounter) "
                                     "OPTIONAL MATCH (e)-[:DIAGNOSED]->(c:Condition) OPTIONAL MATCH (e)-[:PRESCRIBED]->(m:Medication) "
                                     "RETURN e.id, e.date, collect(DISTINCT c.name), collect(DISTINCT m.name) ORDER BY e.date",
                              {"pid": pid})
                active = self._q(gname, "MATCH (:Patient {id:$pid})-[:HAS_ACTIVE_MED]->(m:Medication) RETURN m.name", {"pid": pid})
                if enc or active:
                    return {
                        "patient_id": pid, "graph": gname,
                        "encounters": [{"id": i, "date": d, "conditions": c, "medications": m} for i, d, c, m in enc],
                        "active_medications": [r[0] for r in active]
                    }
            except Exception as e:
                logger.warning("Live FalkorDB get_patient_memory error: %s. Using in-memory fallback.", e)

        # In-memory retrieval
        encounters = self._mem_patient_encounters.get(pid, [])
        active_meds = self._mem_patient_active_meds.get(pid, [])
        return {
            "patient_id": pid,
            "graph": gname,
            "encounters": encounters,
            "active_medications": active_meds,
        }

    # ------------------------------------------------------------------ Track 03
    def get_department_compliance(self, dept_name: str) -> List[Dict[str, Any]]:
        """Institutional brain traversal: Department -> CPT -> DenialReason (+ supervising physician)."""
        if self.is_real_db:
            try:
                sup = self._q(BRAIN_GRAPH, "MATCH (:Department {name:$d})-[:SUPERVISED_BY]->(p:Physician) RETURN p.name", {"d": dept_name})
                rows = self._q(
                    BRAIN_GRAPH,
                    "MATCH path=(d:Department {name:$d})-[b:FREQUENTLY_BILLS]->(c:CPT)-[x:DENIED_FOR]->(r:DenialReason) "
                    "RETURN c.code, c.name, b.count, r.code, r.name, x.count, [n IN nodes(path) | coalesce(n.name, n.code)] "
                    "ORDER BY x.count DESC",
                    {"d": dept_name},
                )
                if rows:
                    physician = sup[0][0] if sup else None
                    return [{
                        "department": dept_name, "supervising_physician": physician, "cpt": c, "cpt_name": cn,
                        "billed_count": bc, "denial_code": rc, "denial_reason": rn, "denial_count": xc,
                        "denial_rate_pct": round(100.0 * xc / bc, 1) if bc else 0.0, "trace_path": t,
                    } for c, cn, bc, rc, rn, xc, t in rows]
            except Exception as e:
                logger.warning("Live FalkorDB get_department_compliance error: %s. Using in-memory fallback.", e)

        # In-memory institutional brain traversal
        physician = _IN_MEM_DEPTS.get(dept_name, "Dr. Sarah Elizabeth")
        cpt_billed = {cpt: count for d, cpt, count in _IN_MEM_BILLS if d == dept_name}
        rows = []
        for cpt, bc in cpt_billed.items():
            cn = _IN_MEM_CPT_NAMES.get(cpt, cpt)
            for dcpt, rcode, xc in _IN_MEM_DENIALS:
                if dcpt == cpt:
                    rname = _IN_MEM_REASON_NAMES.get(rcode, rcode)
                    trace = [dept_name, cpt, rcode]
                    pct = round(100.0 * xc / bc, 1) if bc else 0.0
                    rows.append({
                        "department": dept_name,
                        "supervising_physician": physician,
                        "cpt": cpt,
                        "cpt_name": cn,
                        "billed_count": bc,
                        "denial_code": rcode,
                        "denial_reason": rname,
                        "denial_count": xc,
                        "denial_rate_pct": pct,
                        "trace_path": trace,
                    })

        rows.sort(key=lambda r: r["denial_count"], reverse=True)
        return rows


falkor_service = FalkorHealthService()
