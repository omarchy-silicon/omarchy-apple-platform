"""Closed payload shapes and pure F-02 cross-document admission."""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .canonical import payload_digest, domain_digest
from .constants import AUTHENTICATED_PAYLOAD_TYPES, SCHEMA_SET_DIGEST, TYPE_CONTEXT
from .errors import SchemaError

_DOCUMENT = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_ISSUER = _DOCUMENT
_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,3})?Z$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_BOARD = re.compile(r"^apple:[a-z0-9][a-z0-9-]{0,63}$")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_PREDICATE = re.compile(r"^[a-z0-9][a-z0-9._,:-]{0,127}$")
_OPERATION = {"inspect/v1", "write/v1", "replace/v1", "remove/v1", "rollback/v1"}
_COMPONENTS = {"linux-kernel", "dtb-set", "firmware-bundle", "mesa-stack", "boot-stack"}

ENVELOPE_FIELDS = ("format", "payload_type", "payload_version", "domain", "context", "schema_set_digest", "payload", "signatures")
PAYLOAD_FIELDS = ("schema", "schema_set_digest", "document_id", "issuer", "issued_at", "expires_at")


def _error(code: str, path: str, message: str, phase: str = "P1") -> SchemaError:
    return SchemaError(code, path, phase, message)


def _exact(value: Mapping[str, Any], fields: tuple[str, ...], path: str) -> None:
    unknown = sorted(set(value) - set(fields))
    if unknown:
        raise _error("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "unknown property")
    missing = [field for field in fields if field not in value]
    if missing:
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.{missing[0]}", "required property is missing")


def _string(value: Any, path: str, pattern: re.Pattern[str] | None = None) -> None:
    if not isinstance(value, str) or (pattern is not None and not pattern.fullmatch(value)):
        raise _error("PARSE_SCHEMA_FAILURE", path, "invalid string")


def _digest(value: Any, path: str) -> None:
    _string(value, path, _DIGEST)


def _array(value: Any, path: str, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        raise _error("PARSE_SCHEMA_FAILURE", path, "expected non-empty array")
    if len(value) > 1024:
        raise _error("RESOURCE_LIMIT", path, "array limit exceeded")
    return value


def _sorted_unique(values: list[Any], path: str, key) -> None:
    previous = None
    seen = set()
    for index, value in enumerate(values):
        semantic = key(value)
        if semantic in seen:
            raise _error("DUPLICATE_SEMANTIC_KEY", f"{path}[{index}]", "duplicate semantic key")
        if previous is not None and semantic < previous:
            raise _error("PARSE_SCHEMA_FAILURE", f"{path}[{index}]", "collection is not sorted")
        seen.add(semantic)
        previous = semantic


def _signature(value: Any, path: str, expected_role: str) -> tuple[str, str, str, str]:
    if not isinstance(value, dict):
        raise _error("PARSE_SCHEMA_FAILURE", path, "expected object")
    fields = ("key_id", "signer_role", "algorithm", "signature_format", "signature")
    _exact(value, fields, path)
    _string(value["key_id"], f"{path}.key_id", _ISSUER)
    _string(value["signer_role"], f"{path}.signer_role", _ISSUER)
    if value["signer_role"] != expected_role:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", f"{path}.signer_role", "signer role is not valid")
    if value["algorithm"] != "ed25519" or value["signature_format"] != "raw-ed25519/v1":
        raise _error("PARSE_SCHEMA_FAILURE", path, "unsupported signature encoding")
    _string(value["signature"], f"{path}.signature")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value["signature"]):
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature", "invalid base64url")
    try:
        decoded = base64.urlsafe_b64decode(value["signature"] + "=" * (-len(value["signature"]) % 4))
    except ValueError:
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature", "invalid base64url") from None
    encoded = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if len(decoded) != 64 or encoded != value["signature"]:
        raise _error("PARSE_SCHEMA_FAILURE", f"{path}.signature", "signature must be 64 unpadded bytes")
    return (value["key_id"], value["signer_role"], value["algorithm"], value["signature_format"])


def _common(payload: Any, payload_type: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise _error("PARSE_SCHEMA_FAILURE", "$.payload", "expected object")
    missing = [field for field in PAYLOAD_FIELDS if field not in payload]
    if missing:
        raise _error("PARSE_SCHEMA_FAILURE", f"$.payload.{missing[0]}", "required property is missing")
    if payload["schema"] != payload_type:
        raise _error("SIGNATURE_CONTEXT_MISMATCH", "$.payload.schema", "schema and payload type differ")
    if payload["schema_set_digest"] != SCHEMA_SET_DIGEST:
        raise _error("CROSS_DOCUMENT_MISMATCH", "$.payload.schema_set_digest", "schema-set digest differs")
    _string(payload["document_id"], "$.payload.document_id", _DOCUMENT)
    _string(payload["issuer"], "$.payload.issuer", _ISSUER)
    _string(payload["issued_at"], "$.payload.issued_at", _TIMESTAMP)
    _string(payload["expires_at"], "$.payload.expires_at", _TIMESTAMP)
    return payload


def _board(value: Any, path: str) -> None:
    _string(value, path, _BOARD)


def _type_shape(payload: dict[str, Any], payload_type: str) -> None:
    p = "$.payload"
    if payload_type == "board-registry/v1":
        _exact(payload, PAYLOAD_FIELDS + ("registry_revision", "boards", "capability_vocabulary"), p)
        _string(payload["registry_revision"], f"{p}.registry_revision", _ID)
        boards = _array(payload["boards"], f"{p}.boards", True)
        _sorted_unique(boards, f"{p}.boards", lambda x: x.get("board_id") if isinstance(x, dict) else str(x))
        for i, board in enumerate(boards):
            q = f"{p}.boards[{i}]"
            if not isinstance(board, dict): raise _error("PARSE_SCHEMA_FAILURE", q, "expected object")
            _exact(board, ("board_id", "identity_match", "soc_id", "physical_capabilities", "lifecycle"), q)
            _board(board["board_id"], f"{q}.board_id")
            if not isinstance(board["identity_match"], dict): raise _error("PARSE_SCHEMA_FAILURE", f"{q}.identity_match", "expected object")
            _exact(board["identity_match"], ("macos_compatible", "linux_compatible"), f"{q}.identity_match")
            for k in ("macos_compatible", "linux_compatible"): _string(board["identity_match"][k], f"{q}.identity_match.{k}", _PREDICATE)
            _string(board["soc_id"], f"{q}.soc_id", re.compile(r"^apple-soc:[a-z0-9][a-z0-9-]{0,63}$"))
            caps = _array(board["physical_capabilities"], f"{q}.physical_capabilities")
            for j, cap in enumerate(caps): _string(cap, f"{q}.physical_capabilities[{j}]", _ID)
            _sorted_unique(caps, f"{q}.physical_capabilities", lambda x: x)
            if board["lifecycle"] not in {"active", "deprecated", "withdrawn"}: raise _error("PARSE_SCHEMA_FAILURE", f"{q}.lifecycle", "invalid enum")
        vocab = _array(payload["capability_vocabulary"], f"{p}.capability_vocabulary", True)
        for i, item in enumerate(vocab): _string(item, f"{p}.capability_vocabulary[{i}]", _ID)
        _sorted_unique(vocab, f"{p}.capability_vocabulary", lambda x: x)
    elif payload_type == "platform-manifest/v1":
        fields = PAYLOAD_FIELDS + ("channel", "release_version", "board_registry_digest", "board_targets", "qualification_bindings", "components", "artifacts", "artifact_set_digest")
        _exact(payload, fields, p)
        if payload["channel"] not in {"edge", "rc", "stable"}: raise _error("PARSE_SCHEMA_FAILURE", f"{p}.channel", "invalid channel")
        _string(payload["release_version"], f"{p}.release_version", re.compile(r"^(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})$"))
        _digest(payload["board_registry_digest"], f"{p}.board_registry_digest")
        targets = _array(payload["board_targets"], f"{p}.board_targets", True)
        for i, item in enumerate(targets): _board(item, f"{p}.board_targets[{i}]")
        _sorted_unique(targets, f"{p}.board_targets", lambda x: x)
        bindings = _array(payload["qualification_bindings"], f"{p}.qualification_bindings", True)
        _sorted_unique(bindings, f"{p}.qualification_bindings", lambda x: x.get("board_id") if isinstance(x, dict) else str(x))
        for i, b in enumerate(bindings):
            q=f"{p}.qualification_bindings[{i}]"; _exact(b, ("board_id","qualification_record_id","required_outcome"), q); _board(b["board_id"], q+".board_id"); _string(b["qualification_record_id"], q+".qualification_record_id", _DOCUMENT)
            if b["required_outcome"] != "pass": raise _error("PARSE_SCHEMA_FAILURE", q+".required_outcome", "must be pass")
        comps = payload["components"]
        if not isinstance(comps, dict): raise _error("PARSE_SCHEMA_FAILURE", p+".components", "expected object")
        names = ("linux_kernel","dtb_set","firmware_bundle","mesa_stack","boot_stack"); _exact(comps, names, p+".components")
        for name in names:
            q=p+".components."+name; c=comps[name]
            _exact(c, ("component_id","source_digest","artifact_ids"), q)
            if c["component_id"] not in _COMPONENTS: raise _error("PARSE_SCHEMA_FAILURE", q+".component_id", "invalid component")
            _digest(c["source_digest"], q+".source_digest"); aids=_array(c["artifact_ids"], q+".artifact_ids", True)
            for j,a in enumerate(aids): _string(a, f"{q}.artifact_ids[{j}]", re.compile(r"^artifact:[a-z0-9][a-z0-9._:-]{0,127}$"))
            _sorted_unique(aids, q+".artifact_ids", lambda x:x)
        arts=_array(payload["artifacts"], p+".artifacts", True); _sorted_unique(arts,p+".artifacts",lambda x:x.get("artifact_id") if isinstance(x,dict) else str(x))
        for i,a in enumerate(arts):
            q=f"{p}.artifacts[{i}]"; _exact(a, ("artifact_id","component_id","content_digest","version"), q); _string(a["artifact_id"],q+".artifact_id",re.compile(r"^artifact:[a-z0-9][a-z0-9._:-]{0,127}$")); _digest(a["content_digest"],q+".content_digest"); _string(a["version"],q+".version",re.compile(r"^(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})$"))
        _digest(payload["artifact_set_digest"], p+".artifact_set_digest")
    elif payload_type == "installer-plan/v1":
        _exact(payload, PAYLOAD_FIELDS + ("selection","artifacts","mutations"), p)
        s=payload["selection"]; q=p+".selection"; _exact(s, ("board_id","board_registry_digest","manifest_id","manifest_digest","schema_set_digest"),q); _board(s["board_id"],q+".board_id"); _digest(s["board_registry_digest"],q+".board_registry_digest"); _string(s["manifest_id"],q+".manifest_id",_DOCUMENT); _digest(s["manifest_digest"],q+".manifest_digest"); _digest(s["schema_set_digest"],q+".schema_set_digest")
        arts=_array(payload["artifacts"],p+".artifacts",True); _sorted_unique(arts,p+".artifacts",lambda x:x.get("artifact_id") if isinstance(x,dict) else str(x))
        for i,a in enumerate(arts): q=f"{p}.artifacts[{i}]"; _exact(a,("artifact_id","content_digest"),q); _string(a["artifact_id"],q+".artifact_id",re.compile(r"^artifact:[a-z0-9][a-z0-9._:-]{0,127}$")); _digest(a["content_digest"],q+".content_digest")
        muts=_array(payload["mutations"],p+".mutations",True); _sorted_unique(muts,p+".mutations",lambda x:x.get("sequence") if isinstance(x,dict) else -1)
        for i,m in enumerate(muts): q=f"{p}.mutations[{i}]"; _exact(m,("sequence","operation","target_id","expected_digest"),q); _num(m["sequence"],q+".sequence",0,65535); _string(m["target_id"],q+".target_id",_ID); _digest(m["expected_digest"],q+".expected_digest"); _operation(m["operation"],q+".operation")
    elif payload_type == "qualification-record/v1":
        _exact(payload, PAYLOAD_FIELDS + ("board_id","manifest_id","manifest_digest","qualification_profile_id","checks","evidence","outcome"), p)
        _board(payload["board_id"],p+".board_id"); _string(payload["manifest_id"],p+".manifest_id",_DOCUMENT); _digest(payload["manifest_digest"],p+".manifest_digest"); _string(payload["qualification_profile_id"],p+".qualification_profile_id",re.compile(r"^profile:[a-z0-9][a-z0-9._:-]{0,127}$"))
        checks=_array(payload["checks"],p+".checks",True); _sorted_unique(checks,p+".checks",lambda x:x.get("check_id") if isinstance(x,dict) else str(x))
        for i,c in enumerate(checks): q=f"{p}.checks[{i}]"; _exact(c,("check_id","required","status","evidence_ids"),q); _string(c["check_id"],q+".check_id",re.compile(r"^check:[a-z0-9][a-z0-9._:-]{0,127}$"));
        for i,c in enumerate(checks):
            q=f"{p}.checks[{i}]";
            if not isinstance(c["required"],bool) or c["status"] not in {"pass","fail","not-run","blocked"}: raise _error("PARSE_SCHEMA_FAILURE",q,"invalid check")
            ids=_array(c["evidence_ids"],q+".evidence_ids",True)
            for j,e in enumerate(ids): _string(e,f"{q}.evidence_ids[{j}]",re.compile(r"^evidence:[a-z0-9][a-z0-9._:-]{0,127}$"))
            _sorted_unique(ids,q+".evidence_ids",lambda x:x)
        ev=_array(payload["evidence"],p+".evidence",True); _sorted_unique(ev,p+".evidence",lambda x:x.get("evidence_id") if isinstance(x,dict) else str(x))
        for i,e in enumerate(ev): q=f"{p}.evidence[{i}]"; _exact(e,("evidence_id","content_digest","physical","locator"),q); _string(e["evidence_id"],q+".evidence_id",re.compile(r"^evidence:[a-z0-9][a-z0-9._:-]{0,127}$")); _digest(e["content_digest"],q+".content_digest");
        for i,e in enumerate(ev):
            q=f"{p}.evidence[{i}]";
            if not isinstance(e["physical"],bool): raise _error("PARSE_SCHEMA_FAILURE",q+".physical","expected boolean")
            _string(e["locator"],q+".locator",re.compile(r"^[A-Za-z0-9._:-]{1,256}$"))
        if payload["outcome"] not in {"pass","fail","blocked"}: raise _error("PARSE_SCHEMA_FAILURE",p+".outcome","invalid outcome")
    elif payload_type == "boot-health/v1":
        _exact(payload, PAYLOAD_FIELDS + ("board_id","manifest_id","manifest_digest","profile_id","profile_digest","lineage_id","source_generation","slot","checks","checks_digest","success"), p)
        _board(payload["board_id"],p+".board_id"); _string(payload["manifest_id"],p+".manifest_id",_DOCUMENT); _digest(payload["manifest_digest"],p+".manifest_digest"); _string(payload["profile_id"],p+".profile_id",re.compile(r"^profile:[a-z0-9][a-z0-9._:-]{0,127}$")); _digest(payload["profile_digest"],p+".profile_digest"); _string(payload["lineage_id"],p+".lineage_id",_UUID); _num(payload["source_generation"],p+".source_generation",0,9007199254740991)
        s=payload["slot"]; q=p+".slot"; _exact(s,("slot_id","generation","boot_artifact_digest"),q); _enum(s["slot_id"],q+".slot_id",{"slot-a","slot-b","recovery"}); _num(s["generation"],q+".generation",0,9007199254740991); _digest(s["boot_artifact_digest"],q+".boot_artifact_digest")
        checks=_array(payload["checks"],p+".checks",True); _sorted_unique(checks,p+".checks",lambda x:x.get("check_id") if isinstance(x,dict) else str(x))
        for i,c in enumerate(checks): q=f"{p}.checks[{i}]"; _exact(c,("check_id","status"),q); _string(c["check_id"],q+".check_id",re.compile(r"^check:[a-z0-9][a-z0-9._:-]{0,127}$")); _enum(c["status"],q+".status",{"pass","fail","not-run","unknown"})
        _digest(payload["checks_digest"],p+".checks_digest")
        if not isinstance(payload["success"],bool): raise _error("PARSE_SCHEMA_FAILURE",p+".success","expected boolean")
    elif payload_type == "owner-approval/v1":
        _exact(payload, PAYLOAD_FIELDS + ("plan_id","plan_digest","scope","operation","approved"),p); _string(payload["plan_id"],p+".plan_id",_DOCUMENT); _digest(payload["plan_digest"],p+".plan_digest"); _enum(payload["scope"],p+".scope",{"installer-plan","installer-plan-execution"}); _operation(payload["operation"],p+".operation")
        if payload["approved"] is not True: raise _error("PARSE_SCHEMA_FAILURE",p+".approved","approval must be true")
    elif payload_type == "boot-success-mark/v1":
        _exact(payload, PAYLOAD_FIELDS + ("board_id","manifest_id","manifest_digest","slot_id","lineage_id","core_digest","marker_id"),p); _board(payload["board_id"],p+".board_id"); _string(payload["manifest_id"],p+".manifest_id",_DOCUMENT); _digest(payload["manifest_digest"],p+".manifest_digest"); _enum(payload["slot_id"],p+".slot_id",{"slot-a","slot-b","recovery"}); _string(payload["lineage_id"],p+".lineage_id",_UUID); _digest(payload["core_digest"],p+".core_digest"); _string(payload["marker_id"],p+".marker_id",re.compile(r"^marker:[a-z0-9][a-z0-9._:-]{0,127}$"))
    elif payload_type == "dtb-mutation-envelope/v1":
        _exact(payload, PAYLOAD_FIELDS + ("board_id","manifest_id","manifest_digest","source_digest","pre_mutation_digest","post_mutation_digest","operation"),p); _board(payload["board_id"],p+".board_id"); _string(payload["manifest_id"],p+".manifest_id",_DOCUMENT); _digest(payload["manifest_digest"],p+".manifest_digest")
        for key in ("source_digest","pre_mutation_digest","post_mutation_digest"): _digest(payload[key],p+"."+key)
        _operation(payload["operation"],p+".operation")


def _num(value: Any, path: str, minimum: int, maximum: int) -> None:
    if isinstance(value,bool) or not isinstance(value,int) or not minimum <= value <= maximum: raise _error("RESOURCE_LIMIT" if isinstance(value,int) else "PARSE_SCHEMA_FAILURE",path,"invalid bounded integer")


def _enum(value: Any,path: str,allowed:set[str]) -> None:
    if value not in allowed: raise _error("PARSE_SCHEMA_FAILURE",path,"invalid enum")


def _operation(value: Any,path: str) -> None: _enum(value,path,_OPERATION)


def validate_payload(payload: Any, payload_type: str) -> dict[str, Any]:
    if payload_type not in AUTHENTICATED_PAYLOAD_TYPES: raise _error("PARSE_SCHEMA_FAILURE","$.payload_type","unknown payload type")
    payload = _common(payload,payload_type); _type_shape(payload,payload_type); return payload


def validate_foundation_document(value: Any, payload_type: str) -> dict[str, Any]:
    if payload_type not in AUTHENTICATED_PAYLOAD_TYPES: raise _error("PARSE_SCHEMA_FAILURE","$.payload_type","unknown payload type")
    if not isinstance(value,dict): raise _error("PARSE_SCHEMA_FAILURE","$","document must be an object")
    if "format" not in value: return validate_payload(value,payload_type)
    _exact(value,ENVELOPE_FIELDS,"$")
    if value["format"] != "omarchy-signed/v1": raise _error("PARSE_SCHEMA_FAILURE","$.format","unsupported envelope format")
    if value["payload_type"] != payload_type: raise _error("SIGNATURE_CONTEXT_MISMATCH","$.payload_type","declared type differs")
    if value["payload_version"] != "v1": raise _error("PARSE_SCHEMA_FAILURE","$.payload_version","unsupported payload version")
    domain,context,role=TYPE_CONTEXT[payload_type]
    if value["domain"] != domain: raise _error("SIGNATURE_CONTEXT_MISMATCH","$.domain","wrong signing domain")
    if value["context"] != context: raise _error("SIGNATURE_CONTEXT_MISMATCH","$.context","wrong signing context")
    if value["schema_set_digest"] != SCHEMA_SET_DIGEST: raise _error("CROSS_DOCUMENT_MISMATCH","$.schema_set_digest","schema-set digest differs")
    validate_payload(value["payload"],payload_type)
    if value["payload"]["schema_set_digest"] != value["schema_set_digest"]: raise _error("SIGNATURE_CONTEXT_MISMATCH","$.payload.schema_set_digest","envelope and payload differ")
    if not isinstance(value["signatures"],list) or len(value["signatures"]) != 1: raise _error("PARSE_SCHEMA_FAILURE","$.signatures","exactly one signature is required")
    previous=None; seen=set()
    for index,signature in enumerate(value["signatures"]):
        key=_signature(signature,f"$.signatures[{index}]",role)
        if key in seen: raise _error("DUPLICATE_SEMANTIC_KEY",f"$.signatures[{index}]","duplicate signature tuple")
        if previous is not None and key < previous: raise _error("PARSE_SCHEMA_FAILURE",f"$.signatures[{index}]","signatures are not sorted")
        previous=key; seen.add(key)
    return value


def payload_from_document(value: Mapping[str, Any], payload_type: str) -> dict[str, Any]:
    return validate_foundation_document(value,payload_type).get("payload", value)


@dataclass(frozen=True)
class ConformanceResult:
    conformant: bool
    trusted: bool = False
    code: str = "ACCEPT"
    path: str = "$"
    message: str = "all unsigned documents conform"


def _mismatch(path: str, message: str) -> ConformanceResult:
    return ConformanceResult(False, False, "CROSS_DOCUMENT_MISMATCH", path, message)


def admit_bundle(documents: Mapping[str, Any]) -> ConformanceResult:
    expected = set(AUTHENTICATED_PAYLOAD_TYPES)
    if set(documents) != expected:
        missing=sorted(expected-set(documents)); extra=sorted(set(documents)-expected)
        name=missing[0] if missing else extra[0]
        return ConformanceResult(False,False,"PARSE_SCHEMA_FAILURE","$.inputs."+name,"exactly eight named inputs are required")
    payloads={}
    try:
        for kind in AUTHENTICATED_PAYLOAD_TYPES:
            payloads[kind]=payload_from_document(documents[kind],kind)
    except SchemaError as error:
        return ConformanceResult(False,False,error.code,error.path,error.message)
    reg=payloads["board-registry/v1"]; man=payloads["platform-manifest/v1"]; plan=payloads["installer-plan/v1"]; qual=payloads["qualification-record/v1"]; boot=payloads["boot-health/v1"]; owner=payloads["owner-approval/v1"]; mark=payloads["boot-success-mark/v1"]; dtb=payloads["dtb-mutation-envelope/v1"]
    reg_digest=payload_digest(reg); man_digest=payload_digest(man); plan_digest=payload_digest(plan); boot_digest=payload_digest(boot)
    boards=reg["boards"]; board=boards[0]["board_id"]
    if any(item["board_id"] != board for item in boards): return _mismatch("$.payload.boards","registry board collection is inconsistent")
    if man["board_registry_digest"] != reg_digest: return _mismatch("$.payload.board_registry_digest","manifest registry digest mismatch")
    if board not in man["board_targets"]: return _mismatch("$.payload.board_targets","manifest does not target registry board")
    binding=next((x for x in man["qualification_bindings"] if x["board_id"]==board),None)
    if binding is None or binding["qualification_record_id"] != qual["document_id"]: return _mismatch("$.payload.qualification_bindings","qualification binding mismatch")
    if qual["board_id"] != board or qual["manifest_id"] != man["document_id"] or qual["manifest_digest"] != man_digest or qual["outcome"] != "pass": return _mismatch("$.payload.manifest_digest","qualification binding mismatch")
    evidence={x["evidence_id"]:x for x in qual["evidence"]}
    for check in qual["checks"]:
        if check["required"] and (check["status"] != "pass" or any(e not in evidence or not evidence[e]["physical"] for e in check["evidence_ids"])): return ConformanceResult(False,False,"CROSS_DOCUMENT_MISMATCH","$.payload.checks","required qualification check is incomplete")
    selection=plan["selection"]
    for key,val in (("board_id",board),("board_registry_digest",reg_digest),("manifest_id",man["document_id"]),("manifest_digest",man_digest),("schema_set_digest",SCHEMA_SET_DIGEST)):
        if selection[key] != val: return _mismatch(f"$.payload.selection.{key}","installer selection mismatch")
    manifest_artifacts={x["artifact_id"]:x for x in man["artifacts"]}
    plan_artifacts={x["artifact_id"]:x for x in plan["artifacts"]}
    if set(manifest_artifacts) != set(plan_artifacts) or any(manifest_artifacts[k]["content_digest"] != plan_artifacts[k]["content_digest"] for k in manifest_artifacts): return _mismatch("$.payload.artifacts","installer artifact set mismatch")
    for key,val in (("plan_id",plan["document_id"]),("plan_digest",plan_digest)):
        if owner[key] != val: return _mismatch(f"$.payload.{key}","owner approval binding mismatch")
    if owner["operation"] != plan["mutations"][0]["operation"]: return _mismatch("$.payload.operation","approval operation mismatch")
    for key,val in (("board_id",board),("manifest_id",man["document_id"]),("manifest_digest",man_digest)):
        if boot[key] != val: return _mismatch(f"$.payload.{key}","boot health binding mismatch")
    if any(c["status"] != "pass" for c in boot["checks"]): return ConformanceResult(False,False,"CROSS_DOCUMENT_MISMATCH","$.payload.checks","required boot check failed")
    if mark["board_id"] != board or mark["manifest_id"] != man["document_id"] or mark["manifest_digest"] != man_digest or mark["slot_id"] != boot["slot"]["slot_id"] or mark["lineage_id"] != boot["lineage_id"] or mark["core_digest"] != boot_digest: return _mismatch("$.payload.core_digest","success marker/core binding mismatch")
    for key,val in (("board_id",board),("manifest_id",man["document_id"]),("manifest_digest",man_digest)):
        if dtb[key] != val: return _mismatch(f"$.payload.{key}","DTB binding mismatch")
    dtb_artifact = next((a for a in man["artifacts"] if a["component_id"] == "dtb-set"), None)
    if dtb_artifact is None or dtb["source_digest"] != dtb_artifact["content_digest"]: return _mismatch("$.payload.source_digest","DTB source is not the manifest DTB artifact")
    if dtb["pre_mutation_digest"] == dtb["post_mutation_digest"]: return _mismatch("$.payload.post_mutation_digest","DTB pre/post digests must differ")
    return ConformanceResult(True,False)


__all__=["ConformanceResult","admit_bundle","validate_foundation_document","validate_payload","payload_from_document"]
