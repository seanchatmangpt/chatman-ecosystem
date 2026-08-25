from __future__ import annotations
from .evidence import Evidence, EvidenceKind, Outcome
from .identity import Subject, Refused, RefusalCode

_ALLOWED={'success':Outcome.PASS,'failure':Outcome.FAIL,'cancelled':Outcome.FAIL,'in_progress':Outcome.PENDING,'queued':Outcome.PENDING,'pending':Outcome.PENDING}

def github_ci(subject: Subject, rows: list[dict])->tuple[Evidence,...]:
    out=[]
    for row in rows:
        if row.get('head_sha') != subject.sha: raise Refused(RefusalCode.STALE_OR_FOREIGN_SUBJECT,str(row.get('head_sha')))
        status=row.get('conclusion') or row.get('status') or 'pending'
        outcome=_ALLOWED.get(status,Outcome.UNKNOWN)
        out.append(Evidence(f"github-actions:{row['id']}",subject,EvidenceKind.CI,row['updated_at'],outcome,digest=str(row.get('artifact_digest','')),detail=row.get('name','')))
    return tuple(sorted(out,key=lambda e:e.source_id))

def github_pr(subject: Subject, pr: dict)->Evidence:
    if pr.get('head_sha') != subject.sha: raise Refused(RefusalCode.STALE_OR_FOREIGN_SUBJECT,'pr head')
    state=pr.get('state','open'); outcome=Outcome.PENDING if state=='open' else Outcome.PASS if pr.get('merged') else Outcome.UNKNOWN
    return Evidence(f"github-pr:{pr['number']}",subject,EvidenceKind.PR,pr['updated_at'],outcome,detail=pr.get('title',''))
