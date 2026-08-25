def project(subject,observations,quorum,standing):
    rows=[{"activity":"replica_observation","repo":subject.repo,"sha":subject.sha,"replica":o.replica_id,
           "generation":o.generation,"digest":o.value_digest,"receipt":o.receipt_sha256,"time":o.observed_at.isoformat()}
          for o in sorted(observations)]
    rows.append({"activity":"quorum_classification","repo":subject.repo,"sha":subject.sha,
                 "state":quorum["state"],"standing":standing})
    return tuple(rows)
