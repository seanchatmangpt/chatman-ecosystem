from pathlib import Path

path = Path("crates/ecosystem-core/src/lib.rs")
text = path.read_text()

replacements = {
    "            pub fn parse(value: impl Into<String>) -> Result<Self, Error> {": """            /// Parses and validates a stable identifier.
            ///
            /// # Errors
            /// Returns [`Error::InvalidId`] when the value is noncanonical or uses the wrong prefix.
            pub fn parse(value: impl Into<String>) -> Result<Self, Error> {""",
    """impl ExactSubject {
    pub fn validate(&self) -> Result<(), Error> {""": """impl ExactSubject {
    /// Validates the exact-subject shape and digest syntax.
    ///
    /// # Errors
    /// Returns [`Error::InvalidSubject`] when the subject is not canonical.
    pub fn validate(&self) -> Result<(), Error> {""",
    """impl Standing {
    pub fn permits(self, next: Self) -> bool {""": """impl Standing {
    /// Reports whether this standing may lawfully transition to `next`.
    #[must_use]
    pub fn permits(self, next: Self) -> bool {""",
    """impl Authority {
    pub fn permits(self, required: Self) -> bool {""": """impl Authority {
    /// Reports whether this exact authority matches the required authority.
    #[must_use]
    pub fn permits(self, required: Self) -> bool {""",
    """impl Transition {
    pub fn validate(&self, required: Authority) -> Result<(), Error> {""": """impl Transition {
    /// Validates the subject, standing transition, authority, and evidence.
    ///
    /// # Errors
    /// Returns an error when any constitutional precondition is unsatisfied.
    pub fn validate(&self, required: Authority) -> Result<(), Error> {""",
    """impl Catalog {
    pub fn load(root: &Path) -> Result<Self, Error> {""": """impl Catalog {
    /// Loads all canonical catalog manifests below `root`.
    ///
    /// # Errors
    /// Returns an I/O or TOML error when a manifest cannot be read or parsed.
    pub fn load(root: &Path) -> Result<Self, Error> {""",
    "    pub fn validate(&self, root: &Path) -> Result<(), Error> {": """    /// Validates stable identities, references, evidence paths, and shared subjects.
    ///
    /// # Errors
    /// Returns [`Error::Catalog`] when any catalog law is violated.
    pub fn validate(&self, root: &Path) -> Result<(), Error> {""",
    "    pub fn calculate_digest(&self) -> Result<String, Error> {": """    /// Calculates the canonical BLAKE3 digest of the unsigned receipt.
    ///
    /// # Errors
    /// Returns [`Error::Receipt`] when canonical serialization fails.
    pub fn calculate_digest(&self) -> Result<String, Error> {""",
    "    pub fn sign(&mut self) -> Result<(), Error> {": """    /// Seals this receipt with its canonical BLAKE3 digest.
    ///
    /// # Errors
    /// Returns [`Error::Receipt`] when canonical serialization fails.
    pub fn sign(&mut self) -> Result<(), Error> {""",
    "    pub fn verify(&self) -> Result<(), Error> {": """    /// Verifies receipt completeness, transition legality, and digest integrity.
    ///
    /// # Errors
    /// Returns [`Error::Receipt`] when the receipt is incomplete, unlawful, or tampered.
    pub fn verify(&self) -> Result<(), Error> {""",
    "pub fn verify_all_receipts(root: &Path) -> Result<usize, Error> {": """/// Seals source receipts when needed and verifies every canonical receipt.
///
/// # Errors
/// Returns an I/O, TOML, or receipt-integrity error when admission fails.
pub fn verify_all_receipts(root: &Path) -> Result<usize, Error> {""",
    "pub fn render_standing(catalog: &Catalog) -> String {": """/// Renders the deterministic standing projection.
#[must_use]
pub fn render_standing(catalog: &Catalog) -> String {""",
    "pub fn render_portfolio(catalog: &Catalog) -> String {": """/// Renders the deterministic repository and document portfolio.
#[must_use]
pub fn render_portfolio(catalog: &Catalog) -> String {""",
    "pub fn render_all(root: &Path) -> Result<BTreeMap<PathBuf, String>, Error> {": """/// Renders every generated projection without writing files.
///
/// # Errors
/// Returns a catalog or I/O error when canonical inputs are invalid.
pub fn render_all(root: &Path) -> Result<BTreeMap<PathBuf, String>, Error> {""",
    "pub fn write_projections(root: &Path) -> Result<usize, Error> {": """/// Atomically writes every generated projection.
///
/// # Errors
/// Returns a rendering or I/O error when projection cannot complete atomically.
pub fn write_projections(root: &Path) -> Result<usize, Error> {""",
    "pub fn check_projections(root: &Path) -> Result<usize, Error> {": """/// Verifies that committed projections equal deterministic rendering.
///
/// # Errors
/// Returns [`Error::Projection`] when generated files have drifted.
pub fn check_projections(root: &Path) -> Result<usize, Error> {""",
    "pub fn check_architecture(root: &Path) -> Result<(), Error> {": """/// Enforces framework-free core dependencies and required workspace members.
///
/// # Errors
/// Returns [`Error::Architecture`] when a dependency boundary is violated.
pub fn check_architecture(root: &Path) -> Result<(), Error> {""",
    """impl CrownReport {
    pub fn evaluate(root: &Path, subject: impl Into<String>) -> Result<Self, Error> {""": """impl CrownReport {
    /// Evaluates every required rail against exact-subject admission evidence.
    ///
    /// # Errors
    /// Returns an error when the subject, catalog, receipts, projections, architecture, or admission evidence fails.
    pub fn evaluate(root: &Path, subject: impl Into<String>) -> Result<Self, Error> {""",
    "                rail.subject = subject.clone();": "                rail.subject.clone_from(&subject);",
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"missing expected source fragment:\n{old}")
    text = text.replace(old, new, 1)

standing_old = '''    for rail in rails {
        out.push_str(&format!(
            "| `{}` | `{:?}` | `{}` | {} |\\n",
            rail.id,
            rail.standing,
            rail.subject,
            rail.evidence.join("<br>")
        ));
    }'''
standing_new = '''    for rail in rails {
        let _write_result = std::fmt::Write::write_fmt(
            &mut out,
            format_args!(
                "| `{}` | `{:?}` | `{}` | {} |\\n",
                rail.id,
                rail.standing,
                rail.subject,
                rail.evidence.join("<br>")
            ),
        );
    }'''

portfolio_header_old = '''    let mut out = format!(
        "# {} Portfolio\\n\\nVersion: `{}`\\n\\n## Repositories\\n\\n| Repository | Role | Standing |\\n|---|---|---|\\n",
        catalog.ecosystem.ecosystem.name, catalog.ecosystem.ecosystem.version
    );'''
portfolio_header_new = '''    let mut out = String::new();
    let _write_result = std::fmt::Write::write_fmt(
        &mut out,
        format_args!(
            "# {} Portfolio\\n\\nVersion: `{}`\\n\\n## Repositories\\n\\n| Repository | Role | Standing |\\n|---|---|---|\\n",
            catalog.ecosystem.ecosystem.name, catalog.ecosystem.ecosystem.version
        ),
    );'''

repository_old = '''    for item in repositories {
        out.push_str(&format!(
            "| `{}` | {} | `{:?}` |\\n",
            item.id, item.role, item.standing
        ));
    }'''
repository_new = '''    for item in repositories {
        let _write_result = std::fmt::Write::write_fmt(
            &mut out,
            format_args!(
                "| `{}` | {} | `{:?}` |\\n",
                item.id, item.role, item.standing
            ),
        );
    }'''

document_old = '''    for item in documents {
        out.push_str(&format!(
            "| `{}` | `{}` | {} |\\n",
            item.id, item.path, item.canonical
        ));
    }'''
document_new = '''    for item in documents {
        let _write_result = std::fmt::Write::write_fmt(
            &mut out,
            format_args!(
                "| `{}` | `{}` | {} |\\n",
                item.id, item.path, item.canonical
            ),
        );
    }'''

for old, new in [
    (standing_old, standing_new),
    (portfolio_header_old, portfolio_header_new),
    (repository_old, repository_new),
    (document_old, document_new),
]:
    if old not in text:
        raise SystemExit(f"missing rendering source fragment:\n{old}")
    text = text.replace(old, new, 1)

if "out.push_str(&format!" in text:
    raise SystemExit("format_push_string pattern remains")

path.write_text(text)
