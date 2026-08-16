use crate::{Error, Result};
use std::collections::BTreeMap;

pub fn expand(input: &str, values: &BTreeMap<String, String>) -> Result<String> {
    let mut output = String::with_capacity(input.len());
    let mut rest = input;
    while let Some(start) = rest.find('{') {
        output.push_str(&rest[..start]);
        let after = &rest[start + 1..];
        let Some(end) = after.find('}') else {
            return Err(Error::UnterminatedPlaceholder(input.to_owned()));
        };
        let key = &after[..end];
        let value = values
            .get(key)
            .ok_or_else(|| Error::UnknownPlaceholder(key.to_owned()))?;
        output.push_str(value);
        rest = &after[end + 1..];
    }
    output.push_str(rest);
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expands_known_values() {
        let values = BTreeMap::from([("domain".to_owned(), "d.pddl".to_owned())]);
        assert_eq!(
            expand("--domain={domain}", &values).unwrap(),
            "--domain=d.pddl"
        );
    }

    #[test]
    fn refuses_unknown_values() {
        assert!(matches!(
            expand("{missing}", &BTreeMap::new()),
            Err(Error::UnknownPlaceholder(_))
        ));
    }
}
