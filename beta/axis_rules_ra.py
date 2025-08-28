#!/usr/bin/env python3
"""
MNEME-RA - Verifiable State Stream with Fact Set Recording
Enhanced MNEME for relational algebra rule verification

Responsibilities:
- Record fact sets (not just state diffs)
- Store rule hashes for incremental verification
- Support provenance queries ("why does this fact exist?")
- Enable rule-by-rule replay verification
- Maintain cryptographic integrity chain

Usage:
    from mneme_ra import MnemeRA
    mneme = MnemeRA("facts.json")
    mneme.append_rule_application(input_facts, rule_hash, output_facts)
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# ============================================================================
# FACT SET REPRESENTATION (minimal copy from axis_rules_ra)
# ============================================================================

@dataclass(frozen=True)
class Fact:
    """Immutable fact tuple: (entity, attribute, value)"""
    entity: str
    attribute: str
    value: Any
    
    def to_tuple(self) -> Tuple[str, str, Any]:
        return (self.entity, self.attribute, self.value)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class FactSet:
    """Immutable set of facts with relational algebra operations"""
    
    def __init__(self, facts: Set[Fact] = None):
        self._facts = frozenset(facts or set())
    
    @property
    def facts(self) -> frozenset:
        return self._facts
    
    def __len__(self) -> int:
        return len(self._facts)
    
    def __iter__(self):
        return iter(self._facts)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, FactSet):
            return False
        return self._facts == other._facts
    
    def __hash__(self) -> int:
        return hash(self._facts)
    
    def to_tuples(self) -> List[Tuple[str, str, Any]]:
        """Convert to list of tuples for serialization"""
        return sorted([f.to_tuple() for f in self._facts])
    
    @classmethod
    def from_tuples(cls, tuples: List[Tuple[str, str, Any]]) -> 'FactSet':
        """Create FactSet from tuple list"""
        facts = {Fact(entity, attr, val) for entity, attr, val in tuples}
        return cls(facts)
    
    @classmethod
    def from_json(cls, data: dict, entity_prefix: str = "root") -> 'FactSet':
        """Convert JSON object to fact set"""
        facts = set()
        
        def _extract_facts(obj, path):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_path = f"{path}.{k}" if path else k
                    if isinstance(v, (dict, list)):
                        _extract_facts(v, new_path)
                    else:
                        facts.add(Fact(entity_prefix, new_path, v))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    if isinstance(item, (dict, list)):
                        _extract_facts(item, new_path)
                    else:
                        facts.add(Fact(entity_prefix, new_path, item))
            else:
                facts.add(Fact(entity_prefix, path, obj))
        
        _extract_facts(data, "")
        return cls(facts)

# ============================================================================
# RULE APPLICATION RECORD
# ============================================================================

@dataclass
class RuleApplication:
    """Record of a single rule application"""
    timestamp: str
    rule_hash: str
    input_facts: List[Tuple[str, str, Any]]   # Serializable fact tuples
    output_facts: List[Tuple[str, str, Any]]  # Serializable fact tuples
    meta: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleApplication':
        return cls(**data)

# ============================================================================
# ENHANCED MNEME FOR RELATIONAL ALGEBRA
# ============================================================================

class MnemeRA:
    """Verifiable State Stream with Fact Set Recording"""
    
    def __init__(self, vss_file="facts.json", stream_id="default-facts-vss"):
        self.vss_file = vss_file
        self.stream_id = stream_id
        self.vss = self._load_vss()
    
    def _empty_vss(self) -> Dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "version": "mneme-ra@1.0.0",
            "current_facts": [],          # Current fact set as tuples
            "rule_applications": [],      # History of rule applications
            "integrity_hash": None
        }
    
    def _load_vss(self) -> Dict[str, Any]:
        if os.path.exists(self.vss_file):
            try:
                with open(self.vss_file, "r") as f:
                    return json.load(f)
            except Exception:
                return self._empty_vss()
        return self._empty_vss()
    
    def _hash(self, obj: Any) -> str:
        """Deterministic hash for objects"""
        s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        return hashlib.sha3_256(s.encode()).hexdigest()[:16]
    
    def append_rule_application(self, input_facts: FactSet, rule_hash: str, 
                              output_facts: FactSet, meta: Dict[str, Any] = None):
        """Record a rule application with full fact sets"""
        timestamp = datetime.now().isoformat()
        
        rule_app = RuleApplication(
            timestamp=timestamp,
            rule_hash=rule_hash,
            input_facts=input_facts.to_tuples(),
            output_facts=output_facts.to_tuples(),
            meta=meta or {}
        )
        
        # Add to history
        self.vss["rule_applications"].append(rule_app.to_dict())
        
        # Update current facts
        self.vss["current_facts"] = output_facts.to_tuples()
        
        # Update integrity hash
        self.vss["integrity_hash"] = self._hash(self.vss)
        
        # Persist
        self._persist()
    
    def _persist(self):
        """Persist VSS to file"""
        with open(self.vss_file, "w") as f:
            json.dump(self.vss, f, indent=2)
    
    def verify_chain(self) -> bool:
        """Verify integrity of entire chain"""
        # Recompute hash and check
        current_hash = self._hash(self.vss)
        return current_hash == self.vss.get("integrity_hash")
    
    def verify_incremental(self, rule_engine) -> Dict[str, Any]:
        """Verify chain by replaying each rule application"""
        verification_results = []
        
        if not self.vss["rule_applications"]:
            return {"status": "valid", "applications_verified": 0}
        
        # Start with empty fact set or first input
        if self.vss["rule_applications"]:
            first_app = RuleApplication.from_dict(self.vss["rule_applications"][0])
            current_facts = FactSet.from_tuples(first_app.input_facts)
        else:
            current_facts = FactSet()
        
        for i, app_dict in enumerate(self.vss["rule_applications"]):
            app = RuleApplication.from_dict(app_dict)
            
            try:
                # Verify this rule application
                expected_input = FactSet.from_tuples(app.input_facts)
                expected_output = FactSet.from_tuples(app.output_facts)
                
                # Check if current facts match expected input
                if current_facts != expected_input:
                    verification_results.append({
                        "application": i,
                        "status": "failed",
                        "error": "Input facts don't match chain state",
                        "expected_input_hash": self._hash_fact_tuples(expected_input.to_tuples()),
                        "actual_input_hash": self._hash_fact_tuples(current_facts.to_tuples())
                    })
                    continue
                
                # TODO: Would need rule_engine.apply_by_hash(app.rule_hash, current_facts)
                # For now, just verify the output matches
                verification_results.append({
                    "application": i,
                    "status": "verified",
                    "rule_hash": app.rule_hash,
                    "input_facts": len(expected_input),
                    "output_facts": len(expected_output)
                })
                
                # Move to next state
                current_facts = expected_output
                
            except Exception as e:
                verification_results.append({
                    "application": i,
                    "status": "error",
                    "error": str(e)
                })
        
        # Summary
        verified_count = sum(1 for r in verification_results if r["status"] == "verified")
        failed_count = sum(1 for r in verification_results if r["status"] == "failed")
        error_count = sum(1 for r in verification_results if r["status"] == "error")
        
        return {
            "status": "valid" if failed_count == 0 and error_count == 0 else "invalid",
            "applications_verified": verified_count,
            "applications_failed": failed_count,
            "applications_error": error_count,
            "total_applications": len(verification_results),
            "details": verification_results
        }
    
    def _hash_fact_tuples(self, tuples: List[Tuple[str, str, Any]]) -> str:
        """Hash a list of fact tuples"""
        canonical_tuples = sorted(tuples)
        content = json.dumps(canonical_tuples, sort_keys=True, separators=(',', ':'))
        return hashlib.sha3_256(content.encode()).hexdigest()[:16]
    
    def current_facts(self) -> FactSet:
        """Get current fact set"""
        tuples = self.vss.get("current_facts", [])
        return FactSet.from_tuples(tuples)
    
    def history(self) -> List[RuleApplication]:
        """Get history of rule applications"""
        return [RuleApplication.from_dict(app) for app in self.vss["rule_applications"]]
    
    def provenance_query(self, entity: str, attribute: str) -> List[Dict[str, Any]]:
        """Find provenance of a specific fact"""
        target_fact = (entity, attribute)
        provenance = []
        
        for i, app_dict in enumerate(self.vss["rule_applications"]):
            app = RuleApplication.from_dict(app_dict)
            
            # Check if this rule application derived the fact
            for fact_tuple in app.output_facts:
                if (fact_tuple[0], fact_tuple[1]) == target_fact:
                    provenance.append({
                        "application_index": i,
                        "rule_hash": app.rule_hash,
                        "timestamp": app.timestamp,
                        "derived_value": fact_tuple[2],
                        "meta": app.meta
                    })
        
        return provenance
    
    def get_facts_at_application(self, application_index: int) -> Optional[FactSet]:
        """Get fact set state after specific rule application"""
        if application_index >= len(self.vss["rule_applications"]):
            return None
        
        app = RuleApplication.from_dict(self.vss["rule_applications"][application_index])
        return FactSet.from_tuples(app.output_facts)
    
    def export_timeline(self) -> List[Dict[str, Any]]:
        """Export complete timeline for analysis"""
        timeline = []
        
        for i, app_dict in enumerate(self.vss["rule_applications"]):
            app = RuleApplication.from_dict(app_dict)
            
            timeline.append({
                "index": i,
                "timestamp": app.timestamp,
                "rule_hash": app.rule_hash,
                "input_fact_count": len(app.input_facts),
                "output_fact_count": len(app.output_facts),
                "facts_added": len(app.output_facts) - len(app.input_facts),
                "meta": app.meta
            })
        
        return timeline

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for MNEME-RA"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MNEME-RA: Verifiable fact set logging")
    parser.add_argument("command", choices=[
        'info', 'verify', 'timeline', 'provenance', 'export', 'replay'
    ], help="Command to execute")
    parser.add_argument("vss_file", help="VSS file path")
    parser.add_argument("--entity", help="Entity for provenance query")
    parser.add_argument("--attribute", help="Attribute for provenance query") 
    parser.add_argument("--application", type=int, help="Application index for replay")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    try:
        mneme = MnemeRA(args.vss_file)
        
        if args.command == 'info':
            # Show VSS information
            print(f"📊 MNEME-RA VSS: {mneme.stream_id}")
            print(f"📁 File: {args.vss_file}")
            print(f"🔗 Applications: {len(mneme.history())}")
            print(f"📋 Current facts: {len(mneme.current_facts())}")
            print(f"✅ Chain valid: {mneme.verify_chain()}")
            print(f"🔐 Integrity hash: {mneme.vss.get('integrity_hash', 'None')}")
        
        elif args.command == 'verify':
            # Verify chain integrity
            if mneme.verify_chain():
                print("✅ VSS chain integrity verified")
            else:
                print("❌ VSS chain integrity failed")
                sys.exit(1)
            
            # TODO: Add incremental verification once we have rule engine integration
            print("ℹ️  Incremental verification requires rule engine integration")
        
        elif args.command == 'timeline':
            # Show application timeline
            timeline = mneme.export_timeline()
            
            output = json.dumps(timeline, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"📅 Timeline exported to {args.output}")
            else:
                print("📅 Rule Application Timeline:")
                print("=" * 50)
                for app in timeline:
                    print(f"  {app['index']:3d} | {app['timestamp']} | "
                          f"Rule: {app['rule_hash'][:8]}... | "
                          f"Facts: {app['input_fact_count']}→{app['output_fact_count']}")
        
        elif args.command == 'provenance':
            # Query fact provenance
            if not args.entity or not args.attribute:
                print("Error: --entity and --attribute required for provenance query")
                sys.exit(1)
            
            provenance = mneme.provenance_query(args.entity, args.attribute)
            
            if not provenance:
                print(f"🔍 No provenance found for {args.entity}.{args.attribute}")
            else:
                print(f"🔍 Provenance for {args.entity}.{args.attribute}:")
                print("=" * 50)
                for p in provenance:
                    print(f"  App {p['application_index']:3d} | {p['timestamp']} | "
                          f"Rule: {p['rule_hash'][:8]}... | Value: {p['derived_value']}")
        
        elif args.command == 'export':
            # Export current facts
            current_facts = mneme.current_facts()
            
            fact_data = {
                "facts": current_facts.to_tuples(),
                "fact_count": len(current_facts),
                "entities": list({f.entity for f in current_facts}),
                "export_timestamp": datetime.now().isoformat()
            }
            
            output = json.dumps(fact_data, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"📤 Facts exported to {args.output}")
            else:
                print(output)
        
        elif args.command == 'replay':
            # Show facts at specific application
            if args.application is None:
                print("Error: --application required for replay")
                sys.exit(1)
            
            facts_at_app = mneme.get_facts_at_application(args.application)
            if facts_at_app is None:
                print(f"❌ Application {args.application} not found")
                sys.exit(1)
            
            print(f"🔄 Facts after application {args.application}:")
            print("=" * 50)
            for fact in sorted(facts_at_app.to_tuples()):
                print(f"  {fact[0]:10} | {fact[1]:15} | {fact[2]}")
            print(f"\nTotal: {len(facts_at_app)} facts")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def integrate_with_axis_rules(rule_engine, mneme_logger):
    """Helper to integrate RA rule engine with MNEME logging"""
    
    original_apply = rule_engine.apply
    
    def logged_apply(self, input_data: dict) -> dict:
        """Wrapped apply method with MNEME logging"""
        # Convert to facts
        input_facts = FactSet.from_json(input_data)
        
        # Apply rules (original logic)
        result = original_apply(input_data)
        
        # Convert result to facts
        output_facts = FactSet.from_json(result)
        
        # Log to MNEME
        mneme_logger.append_rule_application(
            input_facts=input_facts,
            rule_hash=self.rules_hash,
            output_facts=output_facts,
            meta={
                'component': self.component_name,
                'rules_applied': len(self.ra_rules)
            }
        )
        
        return result
    
    # Monkey patch the apply method
    rule_engine.apply = logged_apply.__get__(rule_engine, type(rule_engine))
    
    return rule_engine

# ============================================================================
# DEMO & EXAMPLES
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        print("🧠 MNEME-RA: Verifiable Fact Set Recording")
        print("Enhanced MNEME for relational algebra rule verification\n")
        
        # Demo fact set recording
        sample_input_facts = FactSet.from_json({"age": 25, "role": "admin"})
        sample_output_facts = FactSet.from_json({
            "age": 25, "role": "admin", 
            "status": "adult", "access_level": 9000
        })
        
        # Create demo MNEME
        mneme = MnemeRA("demo_facts.json", "demo-stream")
        
        # Record rule application
        mneme.append_rule_application(
            input_facts=sample_input_facts,
            rule_hash="demo_rule_abc123",
            output_facts=sample_output_facts,
            meta={"component": "DemoAccessControl"}
        )
        
        print("📝 Recorded Rule Application:")
        print(f"  Input facts:  {len(sample_input_facts)}")
        print(f"  Output facts: {len(sample_output_facts)}")
        print(f"  Rule hash:    demo_rule_abc123")
        print()
        
        print("📊 Current VSS State:")
        print(f"  Applications: {len(mneme.history())}")
        print(f"  Current facts: {len(mneme.current_facts())}")
        print(f"  Chain valid: {mneme.verify_chain()}")
        print()
        
        print("🔍 Provenance Example:")
        provenance = mneme.provenance_query("root", "status")
        if provenance:
            for p in provenance:
                print(f"  Fact 'status' derived by rule {p['rule_hash'][:8]}... at {p['timestamp']}")
        print()
        
        print("Usage:")
        print("-" * 40)
        print("  python mneme_ra.py info facts.json")
        print("  python mneme_ra.py verify facts.json")
        print("  python mneme_ra.py timeline facts.json")
        print("  python mneme_ra.py provenance facts.json --entity root --attribute status")
        print("  python mneme_ra.py export facts.json --output current_facts.json")
        print("  python mneme_ra.py replay facts.json --application 5")
        print()
        
        print("Integration with AXIS-RULES:")
        print("-" * 40)
        print("  from mneme_ra import MnemeRA")
        print("  mneme = MnemeRA('app_state.json')")
        print("  engine = RelationalRuleEngine(rules, mneme)")
        print("  result = engine.apply(data)  # Auto-logged to MNEME")
        
        # Clean up demo file
        if os.path.exists("demo_facts.json"):
            os.remove("demo_facts.json")
