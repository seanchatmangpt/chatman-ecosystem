use crate::encoding::Encoder;
use crate::parser::Syntax;
/// Type definitions for compiled SHACL shapes
///
/// These types represent the intermediate representation of SHACL shapes,
/// ready for efficient evaluation.
use crate::tripleindex::TripleIndex;
use std::sync::Arc;

/// CostClass ordering for constraint evaluation: evaluate cheaper constraints
/// (O(1) operations) before expensive ones (O(n) or O(n²) operations).
/// This enables early termination when a constraint fails.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum CostClass {
    /// sh:minCount, sh:maxCount (cardinality check, O(1))
    Cardinality = 0,
    /// sh:nodeKind (type check, O(1))
    NodeKind = 1,
    /// sh:datatype (string comparison, O(1))
    Datatype = 2,
    /// sh:class (subclass lookup, O(closure))
    Class = 3,
    /// sh:path (graph traversal, O(graph))
    Path = 4,
    /// sh:pattern (string regex, O(string))
    Regex = 5,
    /// Recursive shape reference (O(depth) or O(graph))
    Recursive = 6,
}

/// A pre-compiled SHACL constraint, ready for evaluation.
/// Uses String IRIs (not SymbolId) to match current codebase conventions.
#[derive(Debug, Clone)]
pub struct CompiledConstraint {
    /// Cost class determines evaluation order
    pub cost_class: CostClass,
    /// The constraint predicate (e.g., sh:minCount, sh:class, sh:pattern)
    pub predicate: usize,
    /// The constraint value (e.g., class IRI, regex pattern)
    pub value: usize,
    /// Whether this constraint is deactivated (sh:deactivated)
    pub is_optional: bool,
}

/// PropertyMask: a bitmask indicating which required properties (sh:minCount >= 1)
/// must be present on a node when validated against a shape.
/// Bits are indexed by property position in the compiled shape's properties.
/// Used for fast O(1) presence checking during validation.
/// Currently limited to 64 properties per shape; shapes with >64 properties
/// will require Vec<u64> extension (TODO(PROJ-415)).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PropertyMask(pub u64);

/// Target selection for a SHACL shape
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TargetType {
    /// sh:targetNode: explicit focus node
    Node,
    /// sh:targetClass: all instances of a class
    Class,
    /// sh:targetSubjectsOf: all subjects of a property
    SubjectsOf,
    /// sh:targetObjectsOf: all objects of a property
    ObjectsOf,
}

/// Pre-compiled SHACL shape target
#[derive(Debug, Clone)]
pub struct CompiledTarget {
    /// The target value (node IRI, class IRI, or property IRI)
    pub target_value: usize,
    /// The type of target
    pub target_type: TargetType,
}

/// Pre-compiled SHACL shape representation
#[derive(Debug, Clone)]
pub struct CompiledShape {
    /// Shape IRI
    pub iri: usize,
    /// Target nodes/classes/properties
    pub targets: Vec<CompiledTarget>,
    /// Constraints, sorted by CostClass (Cardinality first, Recursive last)
    pub constraints: Vec<CompiledConstraint>,
    /// sh:closed (property whitelist enforcement)
    pub closed: bool,
    /// Property shapes (sh:property, recursion)
    pub property_shapes: Vec<CompiledShape>,
    /// Pattern 2: cached sh:closed allowed predicates (sorted for O(log n) lookup)
    pub allowed_predicates: Vec<usize>,
    /// Pattern 2: bitmask for required properties (sh:minCount >= 1)
    pub required_properties_mask: PropertyMask,
}

/// SHACL-SPARQL Dialect Boundary Decision (PROJ-407 Step 2)
///
/// Decision: CORE_ONLY (most conservative)
///
/// Rationale:
/// - SHACL-SPARQL constraints (sh:sparql, sh:select, sh:ask) are rejected at
///   shape load time. Shape validation is purely constraint-based, with no
///   SPARQL evaluation.
/// - Constraints: v26.7.8 threat model prioritizes smallest attack surface
///   and deterministic (not network-dependent) validation. SPARQL evaluation
///   introduces: (1) unbounded query complexity, (2) remote endpoint risk
///   (if federated), (3) non-determinism (variable query planning).
/// - Existing use cases: Graphlaw's production shapes do not rely on
///   SPARQL constraints; all observed use cases are expressible in SHACL
///   CORE (class, property, cardinality, datatype constraints).
///
/// If future use cases require SPARQL constraints, revisit this decision and
/// implement SPARQL_OPTIONAL (local queries only, no federation) in a
/// follow-up ticket.
pub const SHACL_SPARQL_BOUNDARY: &str = "CORE_ONLY";

/// SHACL shapes graph representation
/// Uses Arc<TripleIndex> snapshot for zero-copy, thread-safe, read-only access
/// across multiple validators without fresh allocation per dialect.
///
/// # Pattern 5 (v26.7.8)
/// Replaces fresh-TripleIndex::new()-per-dialect pattern with Arc-wrapped snapshots.
/// Multiple SHACL validators can share the same immutable shapes graph without copying.
///
/// # Pattern 2 (v26.7.8)
/// Stores pre-compiled shapes for O(log n) access to sh:closed allowed predicates
/// and required property masks during validation.
pub struct ShapesGraph {
    pub raw_index: Arc<TripleIndex>,
    /// Cached compiled shapes by shape IRI (usize).
    /// Built at parse time; used during validation for O(log n) lookups.
    pub compiled_shapes: Arc<std::collections::HashMap<usize, CompiledShape>>,
}

impl ShapesGraph {
    /// Parse Turtle shapes graph and create an immutable Arc-wrapped snapshot.
    ///
    /// # Pattern 5 (v26.7.8)
    /// Replaces fresh-TripleIndex::new()-per-dialect with Arc<TripleIndex> snapshot.
    /// The snapshot is shared read-only across SHACL validators without reallocation.
    ///
    /// # Pattern 2 (v26.7.8)
    /// Also pre-compiles all shapes in the graph at parse time, caching:
    /// - sh:closed allowed-predicate sets (sh:property paths + sh:ignoredProperties)
    /// - Required-property bitmasks (sh:minCount >= 1)
    /// This eliminates per-validation re-derivation, achieving O(log n) lookups.
    pub fn parse(shapes_str: &str) -> Result<Self, String> {
        let triples = crate::parser::Parser::parse_triples(shapes_str, Syntax::Turtle)?;
        let mut raw_index = TripleIndex::new();
        for triple in triples {
            raw_index.add(triple);
        }

        // Pattern 2: Compile shapes at parse time
        let raw_index_arc = Arc::new(raw_index);
        let vocab = super::Vocab::new();
        let compiled = Self::compile_all_shapes(raw_index_arc.as_ref(), &vocab);

        Ok(ShapesGraph {
            raw_index: raw_index_arc,
            compiled_shapes: Arc::new(compiled),
        })
    }

    /// Compile all shapes in the index.
    /// Traverses shape definitions and builds CompiledShape objects with
    /// pre-computed sh:closed allowed predicates and required property masks.
    /// O(|shapes| * |properties|) at parse time → O(log n) per validation.
    fn compile_all_shapes(
        raw_index: &TripleIndex, vocab: &super::Vocab,
    ) -> std::collections::HashMap<usize, CompiledShape> {
        use super::index_utils::get_objects;

        let mut compiled = std::collections::HashMap::new();
        let mut shape_nodes = std::collections::HashSet::new();

        // Find all shape nodes (subjects of rdf:type sh:NodeShape or sh:PropertyShape)
        if let Some(types) = raw_index.pos.get(&vocab.rdf_type) {
            if let Some(objs) = types.get(&vocab.sh_node_shape) {
                for (s, _, _) in objs {
                    shape_nodes.insert(*s);
                }
            }
            if let Some(objs) = types.get(&vocab.sh_property_shape) {
                for (s, _, _) in objs {
                    shape_nodes.insert(*s);
                }
            }
        }

        // Also find shapes that have target declarations but no explicit rdf:type
        for target_pred in [
            vocab.sh_target_class,
            vocab.sh_target_node,
            vocab.sh_target_subjects_of,
            vocab.sh_target_objects_of,
        ] {
            if let Some(objs) = raw_index.pos.get(&target_pred) {
                for subjs in objs.values() {
                    for (s, _, _) in subjs {
                        shape_nodes.insert(*s);
                    }
                }
            }
        }

        // Compile each shape
        for shape_node in shape_nodes {
            let compiled_shape = Self::compile_shape(shape_node, raw_index, vocab);
            compiled.insert(shape_node, compiled_shape);
        }

        compiled
    }

    /// Compile a single shape by pre-computing allowed predicates for sh:closed,
    /// building a required-property mask, and populating targets/constraints/
    /// property_shapes from the RDF graph.
    fn compile_shape(
        shape_node: usize, raw_index: &TripleIndex, vocab: &super::Vocab,
    ) -> CompiledShape {
        Self::compile_shape_inner(
            shape_node,
            raw_index,
            vocab,
            &mut std::collections::HashSet::new(),
        )
    }

    /// Inner recursive compile, guarding against cyclic sh:property references
    /// (e.g. a shape whose property shape points back at an ancestor) via a
    /// `visiting` set threaded through the recursion.
    fn compile_shape_inner(
        shape_node: usize, raw_index: &TripleIndex, vocab: &super::Vocab,
        visiting: &mut std::collections::HashSet<usize>,
    ) -> CompiledShape {
        use super::index_utils::get_objects;

        let mut allowed_predicates = std::collections::HashSet::new();

        // Extract allowed predicates from sh:property paths
        for ps in get_objects(raw_index, shape_node, vocab.sh_property) {
            for p in get_objects(raw_index, ps, vocab.sh_path) {
                allowed_predicates.insert(p);
            }
        }

        // Add sh:ignoredProperties
        for ig_list in get_objects(raw_index, shape_node, vocab.sh_ignored_properties) {
            for ig in super::index_utils::get_rdf_list(raw_index, ig_list) {
                allowed_predicates.insert(ig);
            }
        }

        // Convert to sorted Vec for deterministic iteration and binary search
        let mut allowed_preds_vec: Vec<usize> = allowed_predicates.into_iter().collect();
        allowed_preds_vec.sort();

        // --- Targets: sh:targetClass, sh:targetNode, sh:targetSubjectsOf, sh:targetObjectsOf ---
        let mut targets = Vec::new();
        for target_value in get_objects(raw_index, shape_node, vocab.sh_target_class) {
            targets.push(CompiledTarget { target_value, target_type: TargetType::Class });
        }
        for target_value in get_objects(raw_index, shape_node, vocab.sh_target_node) {
            targets.push(CompiledTarget { target_value, target_type: TargetType::Node });
        }
        for target_value in get_objects(raw_index, shape_node, vocab.sh_target_subjects_of) {
            targets.push(CompiledTarget { target_value, target_type: TargetType::SubjectsOf });
        }
        for target_value in get_objects(raw_index, shape_node, vocab.sh_target_objects_of) {
            targets.push(CompiledTarget { target_value, target_type: TargetType::ObjectsOf });
        }

        // --- Property shapes (sh:property) and their constraints ---
        // Bit position within the 64-bit required_properties_mask, assigned in
        // sh:property iteration order (stable given a deterministic TripleIndex
        // iteration order for a fixed graph).
        let mut required_properties_mask = PropertyMask(0);
        let mut property_shapes = Vec::new();
        let already_visiting = !visiting.insert(shape_node);

        if !already_visiting {
            for (bit_pos, ps) in get_objects(raw_index, shape_node, vocab.sh_property)
                .into_iter()
                .enumerate()
            {
                let compiled_ps = Self::compile_shape_inner(ps, raw_index, vocab, visiting);

                // sh:minCount >= 1 on this property shape marks the property required.
                if bit_pos < 64 {
                    for min_count_val in get_objects(raw_index, ps, vocab.sh_min_count) {
                        if let Some(lex) = super::values::get_lexical_form(min_count_val) {
                            if let Ok(n) = lex.trim().parse::<i64>() {
                                if n >= 1 {
                                    required_properties_mask.0 |= 1u64 << bit_pos;
                                }
                            }
                        }
                    }
                }

                property_shapes.push(compiled_ps);
            }
            visiting.remove(&shape_node);
        }

        // --- Constraints directly on this shape node: sh:minCount, sh:maxCount, sh:class ---
        let mut constraints = Vec::new();
        for value in get_objects(raw_index, shape_node, vocab.sh_min_count) {
            constraints.push(CompiledConstraint {
                cost_class: CostClass::Cardinality,
                predicate: vocab.sh_min_count,
                value,
                is_optional: false,
            });
        }
        for value in get_objects(raw_index, shape_node, vocab.sh_max_count) {
            constraints.push(CompiledConstraint {
                cost_class: CostClass::Cardinality,
                predicate: vocab.sh_max_count,
                value,
                is_optional: false,
            });
        }
        for value in get_objects(raw_index, shape_node, vocab.sh_class) {
            constraints.push(CompiledConstraint {
                cost_class: CostClass::Class,
                predicate: vocab.sh_class,
                value,
                is_optional: false,
            });
        }
        // Sort by cost class so cheap constraints (Cardinality) evaluate before
        // expensive ones (Class), enabling early termination on failure.
        constraints.sort_by_key(|c| c.cost_class);

        CompiledShape {
            iri: shape_node,
            targets,
            constraints,
            closed: !get_objects(raw_index, shape_node, vocab.sh_closed).is_empty(),
            allowed_predicates: allowed_preds_vec,
            required_properties_mask,
            property_shapes,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Fixture SHACL graph: a NodeShape targeting ex:Person, with one required
    /// sh:property (ex:name, minCount 1, maxCount 1, class ex:NameValue).
    /// Hand-computed expected values below.
    const FIXTURE_SHAPES: &str = r#"
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <http://example.org/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:PersonShape
            a sh:NodeShape ;
            sh:targetClass ex:Person ;
            sh:property ex:NamePropertyShape .

        ex:NamePropertyShape
            sh:path ex:name ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:class ex:NameValue .
    "#;

    #[test]
    fn parses_target_class_from_fixture() {
        let graph = ShapesGraph::parse(FIXTURE_SHAPES).expect("fixture graph should parse");
        let vocab = super::super::Vocab::new();

        let person_shape_iri =
            Encoder::get("<http://example.org/PersonShape>").expect("PersonShape must be encoded");
        let person_class_iri =
            Encoder::get("<http://example.org/Person>").expect("ex:Person must be encoded");

        let compiled = graph
            .compiled_shapes
            .get(&person_shape_iri)
            .expect("PersonShape must be compiled");

        // Real assertion on structural output, not an empty-vec stub.
        assert_eq!(compiled.targets.len(), 1, "expected exactly one target");
        assert_eq!(compiled.targets[0].target_type, TargetType::Class);
        assert_eq!(compiled.targets[0].target_value, person_class_iri);
        let _ = vocab;
    }

    #[test]
    fn parses_property_shapes_and_min_max_count_constraints() {
        let graph = ShapesGraph::parse(FIXTURE_SHAPES).expect("fixture graph should parse");

        let person_shape_iri =
            Encoder::get("<http://example.org/PersonShape>").expect("PersonShape must be encoded");
        let name_prop_shape_iri = Encoder::get("<http://example.org/NamePropertyShape>")
            .expect("NamePropertyShape must be encoded");
        let name_class_iri =
            Encoder::get("<http://example.org/NameValue>").expect("ex:NameValue must be encoded");

        let person_shape = graph
            .compiled_shapes
            .get(&person_shape_iri)
            .expect("PersonShape must be compiled");

        // sh:property produced exactly one nested compiled property shape.
        assert_eq!(person_shape.property_shapes.len(), 1);
        let name_prop = &person_shape.property_shapes[0];
        assert_eq!(name_prop.iri, name_prop_shape_iri);

        // sh:minCount 1 => bit 0 of the parent's required_properties_mask is set
        // (hand-computed: 1 << 0 == 1).
        assert_eq!(
            person_shape.required_properties_mask.0, 1,
            "minCount>=1 on the sole sh:property must set bit 0"
        );

        // The property shape's own compiled constraints: minCount(1), maxCount(1),
        // class(ex:NameValue) -- 3 constraints, non-empty (was always Vec::new()).
        assert_eq!(name_prop.constraints.len(), 3, "expected 3 constraints on the property shape");

        let min_count_constraint = name_prop
            .constraints
            .iter()
            .find(|c| c.predicate == Encoder::get("<http://www.w3.org/ns/shacl#minCount>").unwrap())
            .expect("minCount constraint must be present");
        assert_eq!(
            super::super::values::get_lexical_form(min_count_constraint.value).as_deref(),
            Some("1")
        );
        assert_eq!(min_count_constraint.cost_class, CostClass::Cardinality);

        let max_count_constraint = name_prop
            .constraints
            .iter()
            .find(|c| c.predicate == Encoder::get("<http://www.w3.org/ns/shacl#maxCount>").unwrap())
            .expect("maxCount constraint must be present");
        assert_eq!(
            super::super::values::get_lexical_form(max_count_constraint.value).as_deref(),
            Some("1")
        );

        let class_constraint = name_prop
            .constraints
            .iter()
            .find(|c| c.predicate == Encoder::get("<http://www.w3.org/ns/shacl#class>").unwrap())
            .expect("class constraint must be present");
        assert_eq!(class_constraint.value, name_class_iri);
        assert_eq!(class_constraint.cost_class, CostClass::Class);

        // Cost-class ordering: Cardinality constraints must sort before Class constraints.
        let cardinality_pos = name_prop
            .constraints
            .iter()
            .position(|c| c.cost_class == CostClass::Cardinality)
            .unwrap();
        let class_pos = name_prop
            .constraints
            .iter()
            .position(|c| c.cost_class == CostClass::Class)
            .unwrap();
        assert!(cardinality_pos < class_pos, "Cardinality constraints must sort before Class");
    }
}
