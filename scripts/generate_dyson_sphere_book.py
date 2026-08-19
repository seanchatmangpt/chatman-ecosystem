from pathlib import Path
import os, re, json, textwrap, math

REPO_ROOT = Path(os.environ.get('CHATMAN_REPO_ROOT', '.')).resolve()
ROOT = Path(os.environ.get('DYSON_BOOK_ROOT', str(REPO_ROOT / 'docs' / 'how-to-build-a-dyson-sphere'))).resolve()
ROOT.mkdir(parents=True, exist_ok=True)

parts = [
(1, 'The Dyson Sphere as a Manufacturing Problem', [
('The Civilization-Scale Build', ['Why a Dyson Sphere Is Not a Construction Project','From Megastructure to Manufacturing System','The Difference Between a Dyson Shell and a Dyson Swarm','Why the Swarm Is the Primary Reference Architecture','The Minimum Viable Dyson System']),
('The Chatman Equation at Stellar Scale', ['A = μ(O*)','Observation','Admission','Manufacture','Artifact','Standing','Why Generated Infrastructure Does Not Yet Exist','Receipts as the Boundary of Reality']),
('Dyson Sphere DfCM', ['Design for Combinatorial Maximalism','Preserve Before Selecting','Reversible Versus Irreversible Decisions',"Chesterton's Fence at Astronomical Scale",'One Failed Orbit Is Not a Failed Civilization','Search Space Before Commitment']),
('SELECT, CONSTRUCT, DO', ['Three Different Kinds of Authority','SELECT','CONSTRUCT','DO','Why Models Do Not Get Ambient Actuation Authority','BRCE: Zero Unreceipted Actuation','Hooks Manufacture Intents, Not Actions']),
]),
(2, 'Define the Star Before Touching the Star', [
('Stellar Observation', ['Stellar Classification','Mass, Luminosity, Radius, and Age','Spectral Measurements','Magnetic Activity','Coronal Mass Ejections','Solar Wind','Long-Horizon Stellar Evolution']),
('The Solar System as an RDF Graph', ['The Public Ontology First Principle','Astronomical Objects','Orbits as First-Class Objects','Resources and Material Bodies','Agents and Organizations','Processes and Events','Measurements and Uncertainty','Provenance','Authority','Constraints']),
('O*.toml for a Star System', ['The Admitted Observation Carrier','Identity','Epistemic Bounds','Source Provenance','Measurement Confidence','Temporal Validity','Contradiction Handling','UNKNOWN Is Not ADMITTED']),
('The Stellar Digital Twin', ['What Must Be Modeled','Ephemerides','Radiation Environment','Thermal Environment','Planetary Bodies','Asteroids and Minor Bodies','Communication Delays','Model Drift']),
]),
(3, 'The Dyson Ontology', [
('Objects', ['Stars','Collectors','Habitats','Factories','Miners','Transporters','Relays','Radiators','Storage Systems','Computational Substrates']),
('Morphisms', ['Observe','Extract','Refine','Manufacture','Transport','Deploy','Orbit','Collect','Transmit','Repair','Recycle','Decommission']),
('Public Ontologies', ['PROV-O','DCAT','DCTERMS','SKOS','SHACL','ODRL','QUDT','SOSA and SSN','ORG','FOAF','OCEL','PREMIS','Extending Without Forking Meaning']),
('Dyson SHACL', ['Shape Constraints','Orbital Safety Shapes','Energy Shapes','Material Provenance Shapes','Authority Shapes','Receipt Shapes','Fail-Closed Admission']),
]),
(4, 'Physics Is the Type System', [
('Orbital Mechanics', ['Two-Body Approximation','N-Body Reality','Keplerian Elements','Perturbations','Resonances','Station Keeping','Collision Probability']),
('Energy', ['The Solar Constant as a Function','Collector Efficiency','Conversion Losses','Transmission Losses','Storage','Dispatch','Energy Accounting']),
('Thermodynamics', ['Every Collector Is Also a Radiator','Waste Heat','Operating Temperature','Radiator Area','Carnot Limits','Thermal Failure Domains']),
('Materials', ['Mass Is the Primary Budget','Metals','Silicates','Carbon','Volatiles','Semiconductors','Radiation Damage','Fatigue and Lifetime']),
('Information Physics', ['Compute Is Physical',"Landauer's Limit",'Latency','Bandwidth','Synchronization Without Global Time','Eventual Consistency Across AU-Scale Systems']),
]),
(5, 'gymact: Build the Solar System Before Building in It', [
('Why Simulation Comes First', ['Simulation Is Not Proof','Simulation as an Observation Generator','Bounded Worlds','Falsifiable Scenarios']),
('The Dyson Gym', ['World','Roles','Policies','Planners','Observation Projections','Action Projections','Information Partitions','Authority']),
('Planetary and Asteroid Environments', ['Mercury','Venus','Earth and the Moon','Mars','The Asteroid Belt','Jovian System','Saturnian System','Outer-System Resources']),
('Scenario Generation', ['Nominal Worlds','Rare Events','Adversarial Worlds','Sensor Failure','Communication Failure','Manufacturing Defects','Orbital Cascade Events','Solar Storms']),
('Benchmarking Civilization-Scale Policies', ['Throughput','Yield','Energy Return','Material Efficiency','Fault Recovery','Reversibility','Safety','Receipt Completeness']),
]),
(6, 'ggen: Manufacturing the Civilization', [
('From Ontology to Artifact', ['Graph','Query','ggen','Formal Admission','Runtime','BRCE','Receipt','Replay','Release']),
('Generative Manufacturing', ['Generators as Projections','Generated Artifacts Are Not the Source of Truth','Deterministic Generation','Content Addressability','Dependency Closure','Regeneration']),
('Factory Templates', ['Mining Factory','Refining Factory','Photovoltaic Factory','Electronics Factory','Robotics Factory','Propulsion Factory','Habitat Factory','Radiator Factory']),
('Self-Replication Without Unbounded Replication', ['The Replication Problem','No Ambient Reproduction Authority','Resource Budgets','Generation Limits','Geofenced and Orbit-Fenced Replication','Shutdown Semantics','Reproduction Receipts']),
]),
(7, 'Formal Admission', [
('ggen Renders, Lean Admits, mfact Certifies', ['Rendering Is Not Admission','Proof-Carrying Designs','Invariant Classes','Machine-Checkable Claims','Certification Receipts']),
('Orbital Invariants', ['Safe Separation','Periapsis and Apoapsis Bounds','Collision Exclusion','Thermal Bounds','Pointing Constraints','Fail-Safe Trajectories']),
('Resource Invariants', ['Mass Conservation','Energy Accounting','Inventory Provenance','Waste Accounting','Closed-Loop Recovery']),
('Authority Invariants', ['Who May Observe','Who May Construct','Who May Actuate','Scope','Expiry','Delegation','Revocation']),
]),
(8, 'CASTLE: Security for a Stellar Civilization', [
('The Threat Model', ['Accidental Failure','Compromised Nodes','Malicious Agents','Corrupted Models','Supply-Chain Attacks','Identity Attacks','Replay Attacks']),
('Zero Trust Across Astronomical Distance', ['Identity','Authentication','Authorization','Attestation','Policy','Least Authority','Compartmentalization']),
('Cryptographic Receipts', ['BLAKE3','Content Identity','Merkle Structures','Signed Receipts','Post-Quantum Migration','ML-DSA','SLH-DSA','Long-Lived Verification']),
('Byzantine Failure', ['No Assumption of Universal Honesty','Partitioned Authority','Quorum Strategies','Local Truth','Eventual Reconciliation']),
]),
(9, 'Weaver: Observe Everything', [
('OpenTelemetry for the Solar System', ['Signals','Metrics','Logs','Traces','Events','Resources']),
('Semantic Conventions', ['Spacecraft','Factory','Collector','Orbit','Energy','Materials','Authority','Receipts']),
('From Telemetry to Admitted Observation', ['Raw Signal','Normalization','Provenance','Admission','O*','Replanning']),
]),
(10, 'AutoFDE for Autonomous Industry', [
('Forward-Deployed Engineering Without Forward-Deployed Humans', ['Environment Discovery','Capability Discovery','Constraint Discovery','Plan Construction','Admission','Execution','Verification']),
('The Autonomous Repair Loop', ['Observe','Classify','Localize','Construct','Admit','Actuate','Verify','Encode the Permanent Guard']),
('Fleet Operations', ['Thousands of Factories','Millions of Collectors','Local Autonomy','Regional Coordination','System-Wide Policy','No Single Global Control Loop']),
]),
(11, 'The Industrial Bootstrap', [
('Phase Zero: Earth', ['Knowledge Manufacturing','Robotics','Autonomous Factories','Launch Systems','Orbital Manufacturing','Simulation Infrastructure']),
('Phase One: Cislunar Industry', ['Lunar Mining','Orbital Refineries','Propellant Production','Assembly Yards','Solar Power Demonstrators']),
('Phase Two: Asteroid Industry', ['Prospecting','Resource Classification','Extraction','Refinement','Mass Drivers','Distributed Manufacturing']),
('Phase Three: Mercury', ['Why Mercury','Solar Energy Availability','Resource Extraction','Thermal Challenges','Planetary Protection','Alternative Resource Strategies']),
('Phase Four: The First Swarm', ['Collector 00000001','First Replication Chain','First Gigawatt','First Terawatt','First Petawatt','Scaling Laws']),
]),
(12, 'Collector Architecture', [
('The Collector', ['Power Surface','Structure','Attitude Control','Thermal Control','Compute','Communications','Navigation','Repair']),
('Collector Classes', ['Minimal Collectors','Power Satellites','Compute Collectors','Industrial Collectors','Habitat Collectors','Communication Collectors']),
('Modular Design', ['Replaceable Components','Standard Interfaces','Mechanical Interoperability','Electrical Interoperability','Semantic Interoperability']),
]),
(13, 'The Swarm as a Distributed System', [
('There Is No Central Computer', ['Scale','Latency','Partition','Failure','Autonomy']),
('Stellar Event Sourcing', ['Events as Facts','OCEL','Causal Graphs','Replay','Derived State']),
('Local-First Control', ['Local Observation','Local Admission','Local Execution','Federated Standing','System-Wide Reconciliation']),
('Communication Topology', ['Optical Links','Radio','Mesh Networks','Delay-Tolerant Networking','Routing','Partition Recovery']),
]),
(14, 'The Energy Internet', [
('Energy as a First-Class Object', ['Generation','Storage','Transmission','Consumption','Waste Heat']),
('Beamed Power', ['Microwave Transmission','Laser Transmission','Beam Geometry','Pointing','Receiving Arrays','Safety Interlocks','No Unreceipted Beam Actuation']),
('Energy Markets', ['Allocation','Priority','Scarcity','Reserves','Emergency Capacity','Machine-Verifiable Settlement']),
]),
(15, 'Economics of a Dyson Civilization', [
('The Capital Problem', ['Bootstrapping','Compounding Industrial Capacity','Marginal Collector Cost','Energy Return on Energy Invested','When Growth Becomes Self-Funding']),
('Resource Accounting', ['Mass Ledgers','Energy Ledgers','Compute Ledgers','Entropy Budgets','Opportunity Cost']),
('Markets Without Semantic Ambiguity', ['Products as Graphs','Capabilities as Contracts','Entitlements','Usage','Settlement','Machine-Readable Regulation']),
]),
(16, 'ggen-marketplace for a Solar Economy', [
('Accumulated Executable Knowledge', ['Why Knowledge Must Be Packaged','Pack Identity','Dependencies','Capabilities','Proof','Receipts']),
('The Dyson Pack', ['Ontology Pack','Simulation Pack','Collector Pack','Factory Pack','Orbital Pack','Security Pack','Telemetry Pack','Governance Pack']),
('Instance Closure to Class Closure', ['Solve One Collector','Extract the Class','Generalize the Pack','Qualify the Class','Manufacture the Fleet']),
]),
(17, 'Planetary Protection and Safety', [
('Earth Is Not Raw Material', ['Human Habitability','Ecological Standing','Protected Mass','Protected Orbits','Protected Energy Flux']),
('No Single Point of Existential Failure', ['Fail-Closed Systems','Safe Defaults','Independent Shutdown','Containment','Recovery']),
('Collision Governance', ['Ephemeris Publication','Reservation of Orbital Regions','Conjunction Assessment','Autonomous Avoidance','Post-Incident Replay']),
]),
(18, 'Governance', [
('Who Owns a Star?', ['Property Versus Stewardship','Commons','Resource Rights','Energy Rights','Future Generations']),
('Constitutional Infrastructure', ['Ontology Before Policy','Policy as Data','ODRL','Machine-Readable Authority','Appeals','Amendment']),
('Polycentric Governance', ['No Planetary Monolith','Local Jurisdiction','Federation','Interoperability','Dispute Resolution']),
('Governance Receipts', ['Identity','Authority','Decision','Consequence','Replay','Standing']),
]),
(19, 'Humans, Machines, and Intelligence', [
('LLMs Are Not the Control Plane', ['Inference Is Not Authority','Planner Output Is Not Actuation','Hallucination as Unadmitted Observation','Bounded Oracle Roles']),
('Post-AGI Infrastructure', ['Intelligence Becomes Abundant','Authority Remains Scarce','Proof Remains Necessary','Physics Remains Authoritative','Receipts Remain Necessary']),
('Human Standing', ['Human Objectives','Consent','Delegation','Revocation','Right to Refuse']),
]),
(20, 'Verification at Civilization Scale', [
('The Validation Ladder', ['Static Validation','Unit Validation','Integration Validation','Simulation','Hardware-in-the-Loop','Orbital Demonstration','Fleet Demonstration','Exact-Subject ALIVE']),
('Status Is a Type', ['UNKNOWN','PARTIAL_ALIVE','ALIVE','BLOCKED','BUILD_BROKEN','UNSUPPORTED','REFUSED']),
('The Exact-Subject Law', ['Inspection Is Not Execution','Workflow Exists Is Not Workflow Passed','Simulation Is Not Deployment','A Receipt Name Is Not a Receipt','Observed Execution Against the Admitted Subject']),
]),
(21, 'Failure Engineering', [
('Design for Failure', ['Everything Eventually Fails','Bounded Failure Domains','Graceful Degradation','Redundancy','Repairability']),
('Failure Injection', ['Collector Loss','Factory Loss','Navigation Failure','Clock Failure','Sensor Corruption','Network Partition','Authority Corruption']),
('Replay the Accident', ['Immutable Event History','Reconstruction','Counterfactual Simulation','Root Cause','Permanent Guard']),
]),
(22, 'Scaling Laws', [
('From One Collector to One Billion', ['Linear Scaling','Nonlinear Effects','Network Effects','Coordination Cost','Autonomy as a Scaling Requirement']),
('Industrial Doubling', ['Replication Rate','Bottleneck Analysis',"Little's Law",'Constraint Theory','Learning Curves','Compounding Capacity']),
('When the Swarm Becomes the Economy', ['Energy Abundance','Compute Abundance','Manufacturing Abundance','Scarcity Moves Up the Stack','Authority as the Remaining Scarcity']),
]),
(23, 'From Dyson Swarm to Matrioshka Brain', [
('Computation as the Load', ['Why Compute','Energy-to-Compute Conversion','Thermal Constraints','Latency Domains']),
('Nested Thermal Layers', ['Hot Inner Compute','Intermediate Layers','Cold Outer Compute','Waste-Heat Cascades']),
('The Matrioshka Graph', ['Compute as an Ontological Resource','Workload Placement','Thermal-Aware Scheduling','Energy-Aware Scheduling','Proof-Aware Scheduling']),
]),
(24, 'Interstellar Extension', [
('A Dyson Sphere Is Not the End', ['Local Completion Versus Expansion','Interstellar Probes','Seed Factories','Local Ontology Reconstruction']),
('Reconstituting the Ecosystem Around Another Star', ['Observe','Construct Local O*','Admit Local Physics','Generate Local Industry','Build Local Receipts','Establish Local Standing']),
('No Universal Configuration', ['Every Star Is a New Subject','Portable Semantics','Local Admission','Federated Civilization']),
]),
(25, 'The Full Chatman Ecosystem', [
('ggen', ['Knowledge Manufacturing','Graph-to-Artifact Compilation','Deterministic Regeneration']),
('ggen-marketplace', ['Capability Distribution','Executable Knowledge','Pack Qualification']),
('gymact', ['World Modeling','Policy Evaluation','Simulation Receipts']),
('AutoFDE', ['Autonomous Environment Integration','Diagnosis and Repair','Operational Closure']),
('CASTLE', ['Security','Authority','Cryptographic Standing']),
('Weaver', ['Telemetry','Semantic Conventions','Observation Manufacturing']),
('mfact', ['Certification','Machine Facts','Receipt Binding']),
('The Ecosystem Is a Pipeline, Not a Platform', ['Observe','Ontology','Constraint','Construction','Admission','Actuation','Receipt','Replay','Standing']),
]),
(26, 'The End-to-End Build', [
('Define the Civilization', ['Objectives','Exclusions','Falsifiers','Authority','Standing']),
('Build the Knowledge Graph', ['Canonical Entities','Relationships','Constraints','Policies','Measurements']),
('Generate the Dyson System', ['Query the Graph','Generate Artifacts','Compile','Admit','Package']),
('Prove It in gymact', ['Nominal Simulation','Adversarial Simulation','Chaos','Stress','Long-Horizon Simulation']),
('Actuate Through BRCE', ['Intent','Admission','Authority','Execution','Receipt','Replay']),
('Collector One', ['Exact Identity','Exact Materials','Exact Orbit','Exact Authority','Exact Execution','Exact Receipt','SUBJECT_ALIVE']),
('From Collector One to Dyson Swarm', ['Replication','Specialization','Federation','Growth','Stability','Civilizational Standing']),
]),
(27, 'What Does “Done” Mean?', [
('Dyson Sphere Completion Is Not a Percentage', ['Coverage','Capacity','Reliability','Standing','Open-Ended Evolution']),
('The ALIVE Criterion', ['Observed','Admitted','Executed','Changed','Verified','Receipted','Replayable']),
('The Final Inversion', ['Do Not Build a Dyson Sphere','Build a System That Can Lawfully Manufacture One','The Sphere Is a Projection','The Graph Is the Civilization','The Receipt Is the Boundary of Reality']),
]),
]

appendices = [
('A','Mathematical Foundations',['Orbital Equations','Radiative Equilibrium','Energy Scaling','Mass Scaling','Replication Models','Reliability Models']),
('B','Reference Ontology',['Classes','Properties','Shapes','Policies','Units','Mappings']),
('C','Dyson O*.toml',['Schema','Solar Example','Collector Example','Factory Example']),
('D','Receipt Schemas',['Observation Receipt','Admission Receipt','Construction Receipt','Actuation Receipt','Verification Receipt','Replay Receipt']),
('E','ggen Pack Layout',['Manifest','Ontology','Queries','Templates','Validators','Tests','Receipts']),
('F','gymact Environment',['World Schema','Agent Schema','Policy Schema','Episode Schema','Reward and Objective Functions']),
('G','BRCE Reference',['Admission','Authority','Actuation','Receipt','Replay','Refusal']),
('H','Status and Refusal Taxonomy',['UNKNOWN','PARTIAL_ALIVE','ALIVE','BLOCKED','BUILD_BROKEN','UNSUPPORTED','Typed REFUSED']),
('I','Failure Catalogue',['Observation Failures','Admission Failures','Construction Failures','Actuation Failures','Verification Failures','Authority Failures']),
('J','Civilization-Scale SLOs',['Availability','Safety','Energy','Manufacturing','Repair','Observation','Receipt Completeness']),
('K','Example SPARQL Queries',['Find Available Material','Find Safe Orbital Regions','Find Unreceipted Actions','Find Unproven Collector Designs','Find Resource Bottlenecks']),
('L','Example SHACL Shapes',['Collector Shape','Orbit Shape','Factory Shape','Authority Shape','Receipt Shape']),
('M','Example Lean Properties',['Orbital Safety','Mass Conservation','Energy Bounds','Authority Non-Escalation','Receipt Completeness']),
('N','Deployment Environments',['Earth Development','Orbital Testbed','Lunar Industrial Zone','Asteroid Factory','Mercury Industrial Network','Inner-System Swarm']),
('O','Glossary',[]),
('P','Symbols and Notation',[]),
('Q','Bibliography',[]),
('R','Further Research',[]),
]

def slug(s):
    s = s.lower().replace('μ','mu').replace('*.','-star-').replace('*','star').replace('o*','o-star')
    s = s.replace('“','').replace('”','').replace("'",'').replace('—','-').replace('–','-').replace('≠','-ne-').replace('=','eq').replace('&','and').replace('/','-')
    s = re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s[:72].rstrip('-')

# Technical note library. Selected by title/part keywords.
RULES = [
(['dyson','swarm','collector'], "A physically credible Dyson program begins with a swarm, not a rigid shell. Independent orbiting collectors can be added incrementally, placed on families of stable trajectories, repaired or retired locally, and diversified by function. A rigid shell around a star has no known passive structural mechanism that keeps it centered; even before material strength is considered, it creates a global stability problem that a swarm avoids."),
(['stellar','star','solar constant','luminosity'], "Stellar power is the dominant external input. For an approximately isotropic star of luminosity L, irradiance at radius r is F=L/(4πr²). This inverse-square relation turns orbital radius into an energy-density and thermal-design parameter. For the Sun, total luminosity is about 3.8×10^26 W; a civilization need not capture all of it for the industrial consequences to be enormous."),
(['orbit','orbital','kepler','periapsis','apoapsis','resonance','ephemer'], "Orbital state is not a location label; it is a dynamical state with uncertainty. In the two-body approximation, orbital period satisfies T²=4π²a³/μ, where a is semimajor axis and μ is the standard gravitational parameter. Operational designs must then add perturbations, multi-body effects, solar radiation pressure, station-keeping budgets, conjunction probability, and covariance growth."),
(['thermo','thermal','radiator','waste heat','temperature','carnot'], "Every useful energy conversion ends as heat. A collector that absorbs stellar power must either radiate comparable power, export energy, store it temporarily, or fail thermally. Radiative disposal scales as P=εσAT⁴, making radiator area and operating temperature architectural variables. The T⁴ dependence rewards hotter radiators with compact area, but material limits, conversion efficiency, computation density, and component lifetime constrain that choice."),
(['energy','power','gigawatt','terawatt','petawatt','beam'], "Energy architecture must distinguish generation, conversion, storage, transmission, dispatch, and final dissipation. Counting nameplate collection without conversion losses and thermal rejection is a category error. In the Chatman frame, each transfer is a typed morphism with measured efficiency, uncertainty, authority boundary, and receiptable consequence."),
(['material','mass','metal','silicate','carbon','volatile','semiconductor','mercury','asteroid','mining','refin'], "Matter is the hard budget that prevents a Dyson program from collapsing into pure software metaphor. Each design must close a mass ledger from feedstock through extraction, refining, fabrication, deployment, maintenance, recycling, and unrecoverable loss. Composition uncertainty is therefore an admitted observation problem before it is a manufacturing problem."),
(['information','compute','landauer','latency','bandwidth','synchron','consistency'], "Information processing remains physical. Landauer's principle gives a lower bound kT ln 2 for irreversible bit erasure, while real systems operate far above that limit because memory, communication, control, error correction, and heat removal dominate. At solar-system scale, propagation delay is also constitutional: one astronomical unit is roughly 499 light-seconds, so globally synchronous control loops are structurally inappropriate."),
(['rdf','ontology','semantic','prov','dcat','dcterms','skos','shacl','odrl','qudt','sosa','ssn','org','foaf','ocel','premis','graph'], "The semantic layer exists to prevent identical reality from fragmenting into incompatible local names. Public vocabularies are preferred where they already express provenance, units, sensors, organizations, policy, preservation, and events. Custom terms are admitted only for genuinely new stellar-industrial meaning. Generated APIs, documents, schemas, simulations, and dashboards are projections over that graph rather than rival semantic authorities."),
(['o-star','o*','observation','admission','unknown','measurement','provenance','identity'], "Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed."),
(['ggen','generate','generation','template','pack','marketplace'], "ggen is treated as a semantic manufacturing compiler: graph and query select meaning, templates render projections, validators reject malformed output, and receipts bind the generated artifact to the admitted subject. Generation is not evidence of correctness. The value of the generator is reproducibility and class closure—once a construction pattern is admitted, it can be regenerated for new subjects without rediscovering the pattern manually."),
(['lean','mfact','formal','proof','invariant','certif'], "Formal admission is used only where a machine-checkable invariant can be stated precisely. The critical separation is that rendering, proving, and certifying are different operations: ggen can render a candidate, Lean can discharge a theorem obligation, and mfact can bind evidence to a subject. None of those steps grants DO authority by itself."),
(['security','castle','zero trust','authentication','authorization','attestation','cryptographic','blake3','merkle','ml-dsa','slh-dsa','byzantine'], "Stellar scale eliminates the plausibility of a trusted interior. Identity, software provenance, key state, policy, and telemetry can all be stale or compromised. CASTLE therefore treats authority as explicit reachability under least privilege, uses content identity and signed evidence where appropriate, partitions failure domains, and never infers permission from network position or possession of a credential."),
(['telemetry','opentelemetry','signal','metric','log','trace','event','weaver'], "Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly."),
(['autofde','repair','environment discovery','capability discovery','constraint discovery','fleet'], "AutoFDE is the reality-acquisition and repair loop. It discovers an environment, distinguishes observed capability from assumed capability, constructs candidate repairs, seeks admission, actuates only through the brokered path, and verifies the postcondition against the exact subject. At fleet scale, this loop must remain local-first because communication delay and partition are normal conditions."),
(['simulation','gym','scenario','benchmark','world','policy','planner','chaos','stress'], "GymAct provides counterfactual execution before physical consequence. A world model names its state, roles, policies, observation projections, action projections, authority, and episode boundaries. Simulation can falsify a candidate or expose missing constraints, but it cannot prove the physical world will behave identically; its standing is experimental evidence, not deployment evidence."),
(['factory','manufactur','robot','refinement','assembly','replication','self-replication'], "Factory design is a closure problem: feedstock, energy, tooling, calibration, control, spares, maintenance, waste, and output quality must all be represented. Self-replication is especially dangerous to leave implicit. Reproduction therefore consumes explicit material and energy budgets, generation limits, geographic or orbital fences, shutdown semantics, and receipts for each authorized replication transition."),
(['authority','select','construct','do','brce','actuat','consent','delegation','revocation','policy'], "SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt."),
(['receipt','replay','standing','alive','exact-subject','verified','status'], "Standing belongs to an exact subject. Inspection is not execution, execution is not verification, and a named receipt file is not evidence that the intended transition occurred. A useful receipt binds identity, authority, consequence, verifier result, and replay instructions so a later observer can reconstruct why the standing claim was made."),
(['failure','fault','redundancy','recovery','accident','collision','conjunction'], "Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm."),
(['economic','capital','market','cost','accounting','ledger','finops','eroi','opportunity'], "The relevant economic quantity is not merely monetary cost but the opportunity cost of scarce mass, energy, launch delta-v, time, compute, and risk. Every scaling argument must show how industrial capacity compounds without hiding bottlenecks in a downstream ledger. Energy return, material yield, repair burden, and replication cycle time are more fundamental than a single currency price."),
(['governance','own','commons','jurisdiction','federation','constitutional','appeal','amendment'], "Governance is treated as executable constraint, not ornamental prose. Rights, duties, jurisdictions, delegation, amendment, and appeals must be represented so that machines can determine what authority exists without manufacturing policy from ambiguity. Polycentric governance is favored because solar-system latency and heterogeneous communities make one synchronous sovereign control loop both brittle and unnecessary."),
(['human','llm','post-agi','intelligence','oracle'], "Abundant inference does not remove the need for authority, proof, physics, or consent. Models can propose, search, summarize, and construct, but their outputs remain unadmitted until tied to a subject and constraint set. Human standing is preserved through explicit objectives, consent, delegation scope, revocation, and refusal rather than vague claims that intelligence implies legitimacy."),
(['scaling','billion','doubling','little','throughput','yield','capacity'], "Scaling is governed by bottlenecks and feedback, not by extrapolating one prototype linearly. Little's Law, L=λW, connects work-in-process, throughput, and cycle time; at industrial scale it becomes a way to detect hidden queues in mining, refining, fabrication, transport, verification, and repair. Exponential capacity growth is possible only while each replication cycle closes its scarce inputs and does not saturate another constraint."),
(['matrioshka','nested','hot inner','cold outer'], "A Matrioshka-brain architecture extends the Dyson idea by using successive thermal layers. Inner computation or industry consumes high-exergy input and radiates lower-temperature waste heat that can be intercepted again farther out. The idea is thermodynamically suggestive rather than a finished engineering design; workload placement must therefore be driven by temperature, latency, reliability, and communication cost rather than a single abstract compute metric."),
(['interstellar','another star','seed','probe','federated civilization'], "Interstellar expansion breaks any assumption of a universal live control plane. A seed system must reacquire local reality, build a local O*, admit local physics and resources, reconstruct manufacturing capability, and produce local receipts. Portable semantics can survive the journey; configuration and standing cannot simply be copied because the subject has changed."),
]

PART_FRAMES = {
1:'The opening part reframes the megastructure as a lawful manufacturing system. The reader is asked to stop imagining one impossible construction event and instead model a compounding sequence of bounded industrial transitions.',
2:'This part establishes epistemic closure. Before selecting designs, the star system must exist as an admitted subject whose measurements, uncertainties, identities, and temporal validity are explicit.',
3:'This part builds the public semantic substrate. Objects and processes receive stable identities so simulations, factories, policies, and receipts can refer to the same world without semantic drift.',
4:'This part places physics above software preference. Orbital dynamics, energy, thermodynamics, materials, and information limits act like non-negotiable types that candidate designs must inhabit.',
5:'This part creates an experimental world in GymAct. Counterfactual execution is used to eliminate unsafe or incoherent policies before authority is ever granted for physical actuation.',
6:'This part turns admitted semantics into repeatable manufacture. ggen projects knowledge into designs and operational artifacts while keeping the graph, not the rendered file, as the reusable source of meaning.',
7:'This part separates generation from admission. Machine-checkable obligations are discharged where possible, and proof evidence is bound to exact subjects instead of treated as ambient truth.',
8:'This part treats every node, link, model, factory, and key as potentially faulty. Security is built from explicit identity, least authority, attestation, compartmentalization, and replayable evidence.',
9:'This part constructs the observation fabric. Raw signals become useful only after normalization, provenance, subject binding, and admission.',
10:'This part describes autonomous field engineering as a bounded control loop. Discovery, diagnosis, construction, actuation, and verification remain separate so autonomy does not become ambient authority.',
11:'This part works backward from terrestrial industry to the first self-expanding off-world manufacturing network. Each phase must close mass, energy, tooling, verification, and repair.',
12:'This part zooms into the basic swarm unit. Collector architecture is modular because a civilization-scale fleet cannot depend on one monolithic design or maintenance path.',
13:'This part treats the swarm as a delay-tolerant distributed system. Local autonomy is a physical consequence of light-speed latency, not merely a software fashion.',
14:'This part models energy as a routed, metered, hazardous resource. Collection is only the beginning; storage, transmission, safety, settlement, and heat complete the system.',
15:'This part replaces hand-waving about post-scarcity with ledgers. Scarcity changes form but never disappears; mass, energy, time, reliability, authority, and opportunity remain allocative constraints.',
16:'This part turns solved designs into civilization memory. Packs capture the semantic and evidentiary closure of a capability so instances can be manufactured without repeating discovery.',
17:'This part treats planetary protection and existential safety as hard constraints on industrial optimization. Earth and inhabited environments are excluded from naïve resource-maximization objectives.',
18:'This part addresses the authority problem that remains after technology scales. Governance is represented as machine-readable, polycentric, appealable constraint rather than implicit ownership.',
19:'This part preserves the distinction between intelligence and legitimacy. Powerful models remain bounded planners and constructors unless explicitly delegated authority.',
20:'This part defines what evidence can support a claim. Validation advances through a ladder, and ALIVE requires observed execution against the exact admitted subject.',
21:'This part engineers for inevitable failure. The system is designed to contain, reconstruct, learn from, and permanently guard against failure modes without collapsing global capacity.',
22:'This part studies the transition from prototypes to astronomical-scale industry. Bottlenecks, queueing, nonlinear interactions, and autonomous local control determine whether scaling laws remain valid.',
23:'This part considers the thermodynamic continuation from energy collection to computation. Nested thermal layers are evaluated as resource and scheduling graphs, not science-fiction ornament.',
24:'This part extends the constitutional method beyond one star. What travels is executable knowledge; local reality must still be reacquired and readmitted.',
25:'This part maps the book back onto concrete ecosystem components. Each component owns a bounded function in the larger observe-to-standing pipeline.',
26:'This part performs the end-to-end build as a sequence of admitted transitions. The goal is not a diagram but an operational correspondence from graph to artifact to actuation to replay.',
27:'The closing part defines completion without pretending a living civilization has a final percentage. Done means a capability class has evidence-backed standing while remaining open to lawful evolution.',
}

FORMULAS = [
    ('orbit', r"\[T^2 = \frac{4\pi^2 a^3}{\mu}\]"),
    ('stellar', r"\[F(r)=\frac{L}{4\pi r^2}\]"),
    ('solar constant', r"\[F(r)=\frac{L}{4\pi r^2}\]"),
    ('thermal', r"\[P_{rad}=\varepsilon\sigma A T^4\]"),
    ('radiator', r"\[P_{rad}=\varepsilon\sigma A T^4\]"),
    ('waste heat', r"\[P_{in}=P_{useful}+P_{export}+P_{stored}+P_{heat}\]"),
    ('energy', r"\[\eta_{end}=\prod_i \eta_i\]"),
    ('landauer', r"\[E_{bit}\ge kT\ln 2\]"),
    ('little', r"\[L=\lambda W\]"),
    ('replication', r"\[C_n=C_0(1+r)^n\]"),
    ('reliability', r"\[A=\frac{MTBF}{MTBF+MTTR}\]"),
    ('chatman', r"\[A=\mu(O^*)\]"),
    ('a =', r"\[A=\mu(O^*)\]"),
]

STATUS_BLOCK = """The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence."""

PIPELINE = "`parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`"


def notes_for(title, part_title):
    q=(title+' '+part_title).lower()
    selected=[]
    for keys, note in RULES:
        if any(k in q for k in keys):
            selected.append(note)
    if not selected:
        selected.append("The subject is treated as a bounded object in the larger stellar-manufacturing graph. Its inputs, outputs, constraints, failure modes, and evidence obligations must be explicit before the system may generalize from a local success to a reusable class.")
    # cap to avoid overlong repetitive chapters
    return selected[:3]


def formula_for(title):
    q=title.lower()
    for key, formula in FORMULAS:
        if key in q:
            return formula
    return None


def links_for(part_no, chapter_no, subtitles):
    lines=[]
    for i, st in enumerate(subtitles,1):
        p=f"part-{part_no:02d}/{chapter_no:02d}-{i:02d}-{slug(st)}.md"
        lines.append((st,p))
    return lines

# assign global chapter numbers
chapter_records=[]
chapter_no=0
for part_no, part_title, chapters in parts:
    for title, subs in chapters:
        chapter_no += 1
        chapter_records.append((part_no, part_title, chapter_no, title, subs))
assert chapter_no == 104, chapter_no


def write(rel, content):
    p=ROOT/rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip()+"\n", encoding='utf-8')


def intro():
    return rf"""# How to Build a Dyson Sphere with the Chatman Ecosystem

## From speculative megastructure to evidence-bounded civilization manufacture

A Dyson sphere is useful precisely because it is too large to be treated as an ordinary engineering object. The phrase compresses a civilization-scale problem—stellar observation, orbital dynamics, mining, refining, manufacturing, robotics, energy conversion, heat rejection, communication, governance, safety, verification, repair, and economic compounding—into a single image. That compression is inspiring, but it is also the first modeling error.

This book expands the problem again.

The physically preferred reference architecture here is a **Dyson swarm**: a very large population of independent orbiting collectors, factories, habitats, radiators, relays, and compute substrates. A rigid shell is not assumed. The swarm grows incrementally; individual elements can fail without requiring a global structural response; orbital families can be redesigned; and industrial capacity can compound. The book therefore asks not *how do we fabricate one shell?* but:

> How can an intelligence acquire a star system as partial reality, admit a bounded model of it, preserve the largest lawful design space, manufacture candidate industrial systems, prove and simulate what can be proven or simulated, actuate only under explicit authority, and leave replayable evidence of what actually changed?

The Chatman Ecosystem expresses that manufacturing problem as:

\[
A = \mu(O^*)
\]

where `O*` is admitted observation, `μ` is lawful manufacture, and `A` is an artifact or actuation whose standing is bounded by evidence. Consequential execution is further separated into three authority classes:

\[
\text{{SELECT}} \neq \text{{CONSTRUCT}} \neq \text{{DO}}
\]

A model may SELECT among orbital architectures. ggen may CONSTRUCT a candidate collector design, simulation world, policy bundle, or control interface. Neither receives DO authority simply because the output exists. Physical consequence is routed through BRCE: **zero unreceipted actuation**.

## Physics outranks narrative

No part of this book treats ontology or software as a substitute for physics. Orbital trajectories must close under gravitational dynamics; energy accounts must close; heat must be rejected; mass must come from somewhere; structures age; sensors lie; communication is bounded by the speed of light; and every real actuator can fail. At one astronomical unit, light takes roughly 499 seconds one way. A solar-system-scale civilization therefore cannot be a low-latency centralized application no matter how intelligent its software becomes.

The stable analytical backbone is simple enough to state and severe enough to govern the entire program. Stellar irradiance falls with the inverse square of distance:

\[
F(r)=\frac{{L}}{{4\pi r^2}}
\]

Radiative cooling scales with the fourth power of temperature:

\[
P_{{rad}}=\varepsilon\sigma A T^4
\]

and Keplerian orbital period in the two-body approximation scales with semimajor axis as:

\[
T^2=\frac{{4\pi^2 a^3}}{{\mu}}
\]

These equations are not the complete design, but they demonstrate the book's operating stance: the candidate space is large, while admission is constrained.

## The ecosystem correspondence

The book uses ecosystem components as bounded roles rather than as a monolithic platform:

- **ggen** manufactures projections from admitted semantic state.
- **ggen-marketplace** captures solved capability classes as accumulated executable knowledge.
- **GymAct** executes counterfactual worlds and adversarial scenarios before physical consequence.
- **AutoFDE** acquires unknown environments and runs bounded diagnosis/repair loops.
- **CASTLE** constrains identity, policy, least authority, attestation, and evidence integrity.
- **Weaver/OpenTelemetry** captures raw signals that may become admitted observations after normalization and provenance checks.
- **Lean** admits formal obligations where theorem statements are meaningful.
- **mfact** binds machine facts and evidence to exact subjects.
- **BRCE** is the exclusive DO path and produces receipts that make consequence replayable.

The invariant pipeline is:

{PIPELINE}

No named technology is allowed to collapse those stages.

## What “build” means in this book

“Build” is used in three senses, and the distinction is essential.

**SELECT** means choosing or ranking a candidate. **CONSTRUCT** means manufacturing a candidate artifact, proof obligation, simulation, plan, policy, or physical design. **DO** means causing consequence in a real or authority-bearing environment. Most of the book lives above the DO boundary because civilization-scale safety requires maximal intelligence before consequence and minimal implicit authority at consequence.

A simulation can reach `ALIVE` standing for the exact simulation subject if it really executed and its verifier passed. That does not make a physical collector `ALIVE`. A formal proof can establish a theorem about a model. That does not prove the model is a complete representation of the Sun. A telemetry pipeline can receive measurements. That does not make every measurement admitted. The book repeatedly preserves these non-collapses because civilization-scale errors often begin when two adjacent evidence types are treated as equivalent.

## The working-backwards target

The target state is not “a finished sphere.” It is a civilization with a lawful manufacturing loop capable of expanding a swarm while protecting inhabited environments and retaining evidence of every consequential transition. Collector one is important because it makes the method falsifiable. Collector one billion is possible only if the first unit's knowledge can be lifted into a reusable class without copying hidden assumptions.

The final inversion is therefore the thesis of the entire book:

> **Do not build a Dyson sphere. Build a system that can lawfully manufacture, verify, repair, govern, and evolve one.**

The sphere is a projection. The graph is the civilization's shared machine-readable memory. The receipt is the boundary between what was proposed and what actually happened.
"""

write('README.md', intro())

summary=['# Summary','', '[How to Build a Dyson Sphere with the Chatman Ecosystem](README.md)','']

for part_no, part_title, _, _, _ in []:
    pass

# Write numbered chapters and subchapters
for part_no, part_title, cnum, title, subs in chapter_records:
    part_dir=f'part-{part_no:02d}'
    main_path=f'{part_dir}/{cnum:02d}-{slug(title)}.md'
    # chapter summary block for SUMMARY
    if not any(line == f'# Part {part_no}' for line in summary):
        # use Roman numerals for presentation
        def roman(n):
            vals=[(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
            out=''
            for v,sym in vals:
                while n>=v: out+=sym; n-=v
            return out
        summary.extend([f'# Part {roman(part_no)} — {part_title}',''])
    summary.append(f'- [{cnum}. {title}]({main_path})')
    sublinks=links_for(part_no,cnum,subs)
    for st, p in sublinks:
        summary.append(f'    - [{st}]({p})')
    summary.append('')

    notes=notes_for(title, part_title)
    formula=formula_for(title)
    body=[f'# {cnum}. {title}','',f'> **Part {part_no}: {part_title}.** {PART_FRAMES[part_no]}','',
          '## Thesis','',
          f'{title} is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.','']
    for note in notes:
        body.extend([note,''])
    if formula:
        body.extend(['## Governing relation','',formula,'', 'The equation is a model boundary, not a complete design. Its variables must be bound to units, provenance, uncertainty, and a validity interval before a downstream system may treat the result as admitted engineering input.',''])
    body.extend(['## Chatman-Ecosystem realization','',
                 f'The operational path is {PIPELINE}. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.','',
                 STATUS_BLOCK,'',
                 '## Chapter map',''])
    for st,p in sublinks:
        body.append(f'- [{st}]({Path(p).name})')
    body.extend(['','## Acceptance boundary','',
                 'This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.','',
                 '## Falsifiers','',
                 '- A required physical ledger does not close.','- The subject identity is ambiguous or stale.','- A simulation result is presented as physical execution evidence.','- A proof is about a model that was never admitted as the operational subject.','- An actuator can be reached outside the brokered receipt path.','- Replay cannot reconstruct the transition that supposedly established standing.',''])
    write(main_path, '\n'.join(body))

    for idx,(st,p) in enumerate(sublinks,1):
        sn=notes_for(st+' '+title, part_title)
        sf=formula_for(st+' '+title)
        sub=[f'# {cnum}.{idx} {st}','',f'**Parent:** [{cnum}. {title}]({Path(main_path).name})','',
             '## Claim','',
             f'`{st}` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger {title.lower()} system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.','']
        for note in sn:
            sub.extend([note,''])
        if sf:
            sub.extend(['## Model', '', sf, '', 'Any numeric use of this relation is admitted only after units, parameter source, uncertainty, epoch, and approximation regime are recorded. Model validity is part of the subject, not metadata that may be discarded after calculation.',''])
        sub.extend(['## Operationalization','',
                    f'The implementation path is {PIPELINE}. The decisive rule is that the semantic or analytical result produced in this subchapter has **no ambient execution authority**. It may change the candidate set, create a proof obligation, generate a simulation, or manufacture an intent. A consequential action still requires explicit subject identity, authority, preconditions, execution, postcondition verification, and a receipt.','',
                    'A practical record for this topic should contain:','',
                    '- exact subject and revision/epoch;','- observed inputs with units and provenance;','- admitted assumptions and explicit UNKNOWNs;','- candidate construction or policy;','- constraints and refusal conditions;','- required authority class: SELECT, CONSTRUCT, or DO;','- verifier and postcondition;','- receipt identity and replay method when consequence occurs;','',
                    '## Evidence boundary','',
                    f'For `{st}`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.','',
                    '## Falsifier','',
                    f'The working claim for `{st}` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.',''])
        write(p, '\n'.join(sub))

# Appendices
summary.extend(['# Appendices',''])
for letter, title, subs in appendices:
    main=f'appendices/{letter.lower()}-{slug(title)}.md'
    summary.append(f'- [Appendix {letter} — {title}]({main})')
    subpaths=[]
    for i,st in enumerate(subs,1):
        p=f'appendices/{letter.lower()}-{i:02d}-{slug(st)}.md'
        summary.append(f'    - [{st}]({p})')
        subpaths.append((st,p))
    summary.append('')
    notes=notes_for(title,'Appendices')
    b=[f'# Appendix {letter} — {title}','',
       'This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.','']
    for note in notes: b.extend([note,''])
    if subs:
        b.extend(['## Sections',''])
        for st,p in subpaths: b.append(f'- [{st}]({Path(p).name})')
    if letter=='O':
        b += ['', '## Core terms','',
              '**Admission** — the transition from observed or proposed information into bounded information permitted to participate in manufacture.',
              '', '**ALIVE** — standing supported by observed execution against the exact admitted subject with required verification and replay evidence.',
              '', '**BRCE** — the brokered consequential execution path that enforces zero unreceipted actuation.',
              '', '**DfCM** — Design for Combinatorial Maximalism: preserve the maximal reversible lawful possibility space before irreversible selection.',
              '', '**Dyson swarm** — a population of independent orbiting structures that collectively intercept a significant fraction of stellar output.',
              '', '**O*** — admitted observation: identity-, provenance-, unit-, uncertainty-, and scope-bounded observation.',
              '', '**Receipt** — evidence object binding identity, authority, consequence, postcondition, and replay.',
              '', '**Standing** — the bounded evidentiary status of a claim about an exact subject.']
    elif letter=='P':
        b += ['', '## Symbols','',
              '| Symbol | Meaning |','|---|---|','| `A` | manufactured artifact or admitted actuation |','| `O` | partial observation |','| `O*` | admitted observation |','| `μ` | lawful manufacture |','| `R` | receipt |','| `L` | stellar luminosity |','| `r` | distance from stellar center |','| `F` | irradiance |','| `σ` | Stefan–Boltzmann constant |','| `ε` | emissivity |','| `T` | absolute temperature |','| `a` | orbital semimajor axis |','| `μ_g` | standard gravitational parameter when disambiguation is required |']
    elif letter=='Q':
        b += ['', '## Foundational references','',
              '- Freeman J. Dyson, “Search for Artificial Stellar Sources of Infrared Radiation” (1960).',
              '- Johannes Kepler and later Newtonian orbital mechanics for the two-body relations used throughout the text.',
              '- Rolf Landauer, “Irreversibility and Heat Generation in the Computing Process” (1961).',
              '- Ludwig Boltzmann, Josef Stefan, and modern radiative-transfer treatments for blackbody and graybody heat rejection.',
              '- W3C Recommendations for RDF, PROV-O, DCAT, SKOS, SHACL, ODRL, SOSA/SSN and related semantic-web standards.',
              '- OpenTelemetry specifications for vendor-neutral telemetry representation.',
              '- OCEL 2.0 literature for object-centric event representation.',
              '- NIST FIPS 204 (ML-DSA) and FIPS 205 (SLH-DSA) for post-quantum signature standards.',
              '', 'The bibliography is deliberately a map of primary intellectual dependencies rather than a claim that any cited work endorses the Chatman Ecosystem framing.']
    elif letter=='R':
        b += ['', '## Open research frontier','',
              'The most important unresolved work is not a larger rendering of a sphere. It is closure across coupled physical and institutional systems: high-fidelity long-horizon orbital traffic management, autonomous in-space refining, self-maintaining robotics, low-mass radiators, radiation-hard computation, bounded self-replication, machine-checkable governance, and experiments that can distinguish attractive simulations from robust physical policies.',
              '', 'A second frontier is epistemic. As autonomous systems become better at proposing designs, the civilization needs better methods for recording why a design was admitted, which evidence was excluded, which approximations remain open, and what observation would falsify the current standing claim.']
    write(main,'\n'.join(b))
    for i,(st,p) in enumerate(subpaths,1):
        sn=notes_for(st+' '+title,'Appendices')
        sf=formula_for(st+' '+title)
        sb=[f'# Appendix {letter}.{i} — {st}','',f'**Parent:** [Appendix {letter} — {title}]({Path(main).name})','']
        for note in sn: sb.extend([note,''])
        if sf: sb.extend(['## Reference relation','',sf,''])
        # specialized snippets
        lower=st.lower()
        if 'schema' in lower or 'receipt' in lower:
            sb += ['## Minimal record','', '```text', 'subject = <exact identity>', 'observed = <bounded inputs>', 'admitted = <constraints and uncertainty>', 'authority = <SELECT|CONSTRUCT|DO>', 'executed = <observed action or NONE>', 'verified = <postcondition evidence>', 'receipt = <content identity>', 'replay = <deterministic reconstruction method>', 'standing = <bounded status>', '```','']
        if 'sparql' in title.lower() or lower.startswith('find '):
            sb += ['## Query pattern','', '```sparql', 'SELECT ?subject ?evidence', 'WHERE {', '  ?subject ?predicate ?evidence .', '  FILTER(BOUND(?evidence))', '}', '```','', 'The concrete ontology IRIs and predicates must come from the admitted graph. This generic pattern is illustrative and must not be mistaken for a canonical query against an unspecified schema.','']
        if 'shape' in lower:
            sb += ['## SHACL pattern','', '```turtle', '@prefix sh: <http://www.w3.org/ns/shacl#> .', '@prefix ex: <https://example.invalid/dyson/> .', '', 'ex:ExampleShape a sh:NodeShape ;', '  sh:targetClass ex:Example ;', '  sh:closed false .', '```','', 'The example is intentionally incomplete. Production shapes must bind to the canonical ontology and include the actual constraints required by the subject.','']
        if any(k in lower for k in ['lean','safety','mass conservation','energy bounds','authority non-escalation']):
            sb += ['## Formalization boundary','', 'The theorem statement must be written over the exact model used by construction. Proving a simplified invariant is useful only if the projection from the operational subject into the theorem model is itself admitted and reviewable.','']
        sb += ['## Standing rule','',STATUS_BLOCK,'']
        write(p,'\n'.join(sb))

# Afterword + contributors + index
summary.extend(['-----------','', '[Afterword — You Were Never Building the Sphere](afterword.md)','', '[Contributors](misc/contributors.md)','', '[Index](misc/index.md)',''])
write('SUMMARY.md','\n'.join(summary))

write('afterword.md', rf"""# Afterword — You Were Never Building the Sphere

The visual metaphor of a Dyson sphere suggests an object. The engineering reality is a civilization of transitions.

A collector is mined from a body whose composition was imperfectly observed. Its feedstock is refined by equipment with calibration error. Its design is selected from alternatives whose assumptions may be wrong. It is manufactured by tools that age, transported through a dynamical system that never stops moving, deployed under authority that should be revocable, and operated inside a radiation and thermal environment that changes with stellar activity. Its telemetry is partial. Its software is replaceable. Its governing institutions will change. Its failures will become data for designs that do not yet exist.

That means the durable artifact is not the collector. It is the correspondence that allows a civilization to move from observation to standing without losing meaning:

\[
O \rightarrow O^* \rightarrow \mu \rightarrow A \rightarrow R \rightarrow O'
\]

A civilization that preserves that correspondence can replace implementations while retaining accumulated knowledge. It can abandon a bad orbit without declaring the whole graph a failure. It can discover that a material assumption was false and trace which candidate classes depended on it. It can refuse an unauthorized actuator even when a model is confident. It can replay an accident. It can lift a successful collector into a capability class without pretending that one success proves every future instance.

This is why the final inversion is not rhetorical.

Do not optimize for the picture of a completed sphere. Optimize for the lawful manufacturing system whose local actions remain bounded, whose physics closes, whose authority is explicit, whose evidence survives turnover, and whose successful constructions become reusable civilization memory.

Then a Dyson swarm is no longer one impossible project. It is the asymptotic output of a system that knows how to learn without forgetting what it actually knows, build without confusing a proposal for reality, and act without erasing the evidence of consequence.

You were never building the sphere.

You were building the civilization that could deserve the power of one.
""")

write('misc/contributors.md', """# Contributors

## Sean Chatman

Originator of the Chatman Ecosystem framing used throughout this manuscript: the Chatman Equation `A = μ(O*)`, the separation of SELECT/CONSTRUCT/DO, receipt-bounded actuation, DfCM, exact-subject standing, and the ecosystem composition described in the book.

## Machine-assisted manufacture

The manuscript was machine-manufactured from the admitted outline and repository doctrine. Machine generation is a construction fact, not an authority or correctness claim. Physics, policy, implementation, and evidentiary claims remain bounded by the verification rules stated in the book.
""")

# Alphabetical index of chapters and subchapters
idx=['# Index','', 'This index points to manuscript subjects; it is not a semantic ontology.','']
entries=[]
for part_no,part_title,cnum,title,subs in chapter_records:
    main=f'../part-{part_no:02d}/{cnum:02d}-{slug(title)}.md'
    entries.append((title,main))
    for i,st in enumerate(subs,1):
        entries.append((st,f'../part-{part_no:02d}/{cnum:02d}-{i:02d}-{slug(st)}.md'))
for letter,title,subs in appendices:
    entries.append((f'Appendix {letter} — {title}',f'../appendices/{letter.lower()}-{slug(title)}.md'))
for title,path in sorted(entries,key=lambda x:x[0].lower()):
    idx.append(f'- [{title}]({path})')
write('misc/index.md','\n'.join(idx))

# Validation
summary_text=(ROOT/'SUMMARY.md').read_text()
links=re.findall(r'\[[^\]]+\]\(([^)]+\.md)\)',summary_text)
missing=[]
for link in links:
    p=(ROOT/link)
    if not p.exists(): missing.append(link)
all_md=list(ROOT.rglob('*.md'))
word_counts={str(p.relative_to(ROOT)):len(re.findall(r"\b[\w'μ]+\b",p.read_text())) for p in all_md}
short=[(p,w) for p,w in word_counts.items() if w<120 and not p.endswith('SUMMARY.md')]
report={
    'chapters':len(chapter_records),
    'summary_links':len(links),
    'markdown_files':len(all_md),
    'missing_links':missing,
    'short_files':short[:20],
    'min_words':min((w for p,w in word_counts.items() if not p.endswith('SUMMARY.md')), default=0),
    'total_words':sum(word_counts.values()),
}
validation_path = Path(os.environ.get('DYSON_VALIDATION_PATH', '/tmp/dyson-book-validation.json'))
validation_path.write_text(json.dumps(report, indent=2))

# Integrate the nested manuscript into the composition-root documentation index without
# hand-editing the generated projection on subsequent replays.
root_summary = REPO_ROOT / 'docs' / 'SUMMARY.md'
if root_summary.exists():
    start = '<!-- BEGIN HOW-TO-BUILD-A-DYSON-SPHERE -->'
    end = '<!-- END HOW-TO-BUILD-A-DYSON-SPHERE -->'
    nested = (ROOT / 'SUMMARY.md').read_text()
    body_lines = []
    for line in nested.splitlines():
        if line.strip() == '# Summary':
            continue
        line = re.sub(r'\((?!https?://)([^)]+\.md)\)', lambda m: f'(how-to-build-a-dyson-sphere/{m.group(1)})', line)
        body_lines.append(line)
    block = '\n'.join([start, '# Book — How to Build a Dyson Sphere with the Chatman Ecosystem', '', *body_lines, end, ''])
    current = root_summary.read_text()
    if start in current and end in current:
        current = re.sub(re.escape(start) + r'.*?' + re.escape(end) + r'\n?', block.rstrip() + '\n', current, flags=re.S)
    else:
        current = current.rstrip() + '\n\n' + block
    root_summary.write_text(current)

catalog = REPO_ROOT / 'catalog' / 'documents.toml'
if catalog.exists():
    entry = '''[[document]]
id = "document:how-to-build-a-dyson-sphere"
title = "How to Build a Dyson Sphere with the Chatman Ecosystem"
path = "docs/how-to-build-a-dyson-sphere/README.md"
canonical = false
'''
    current = catalog.read_text()
    marker = 'id = "document:how-to-build-a-dyson-sphere"'
    if marker not in current:
        catalog.write_text(current.rstrip() + '\n\n' + entry)

if missing or len(chapter_records) != 104 or len(links) != 838 or len(all_md) != 839:
    raise SystemExit(f'validation failed: {json.dumps(report, sort_keys=True)}')
print(json.dumps(report, indent=2))
