import copy
import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'dfcm_autonomic_finish.py'
spec = importlib.util.spec_from_file_location('dfcm_updated', MODULE)
dfcm = importlib.util.module_from_spec(spec)
assert spec.loader
import sys
sys.modules[spec.name] = dfcm
spec.loader.exec_module(dfcm)


def component(cid, standing, deps=(), blocker=None, receipt=False, role=None):
    row = {
        'id': cid,
        'repository': f'seanchatmangpt/{cid}',
        'ref': 'main',
        'sha': (cid[0] if cid[0] in 'abcdef' else 'a') * 40,
        'role': role or cid,
        'standing': standing,
        'required': True,
        'depends_on': list(deps),
    }
    if blocker:
        row['blocker'] = blocker
    if receipt:
        row['execution_receipt'] = f'test:{cid}'
        row['executed_sha'] = row['sha']
    return row


def manifest(*rows, standing='UNKNOWN', required_roles=()):
    return {
        'release': {'standing': standing, 'required_roles': list(required_roles)},
        'components': list(rows),
    }


class PostAgiCapsuleTests(unittest.TestCase):
    def setUp(self):
        self.subject = manifest(
            component('a', 'PARTIAL_ALIVE'),
            component('b', 'UNKNOWN', ['a']),
            component('c', 'ALIVE', receipt=True),
            component('d', 'BUILD_BROKEN', ['c']),
            component('e', 'BLOCKED', ['c'], blocker='GITHUB_ACTIONS_BILLING_OR_SPENDING_LIMIT'),
            component('f', 'UNSUPPORTED', ['c']),
        )
        self.capsule = dfcm.construct_capsule(self.subject, limit=2)

    def grant(self, intent_index=0, **updates):
        intent = self.capsule['operationalization']['selected_intents'][intent_index]
        grant = {
            'authority_id': 'authority:test',
            'actor': 'test-actor',
            'capsule_digest': self.capsule['capsule_digest'],
            'subject_sha': intent['subject']['sha'],
            'intent_digest': intent['intent_digest'],
            'scope': dfcm.BRCE_SCOPE,
            'issued_at': '2026-08-19T20:00:00Z',
            'not_before': '2026-08-19T20:01:00Z',
            'expires_at': '2026-08-19T21:00:00Z',
        }
        grant.update(updates)
        return grant

    def test_preserve_precedes_selection_and_keeps_blocked_topology(self):
        preserved_ids = {
            x['component'] for x in self.capsule['preserve']['actionable'] + self.capsule['preserve']['blocked']
        }
        self.assertEqual(preserved_ids, {'a', 'b', 'd', 'e', 'f'})
        blocked = {x['component']: x for x in self.capsule['preserve']['blocked']}
        self.assertIn('b', blocked)
        self.assertEqual(blocked['b']['missing_alive_dependencies'], ['a'])
        self.assertFalse(self.capsule['preserve']['selection_performed'])
        self.assertFalse(self.capsule['operationalization']['consequential_do_performed'])
        self.assertEqual(self.capsule['fence']['exclusive_do_path'], 'BRCE')

    def test_capsule_is_deterministic_and_self_authenticating(self):
        other = dfcm.construct_capsule(copy.deepcopy(self.subject), limit=2)
        self.assertEqual(self.capsule, other)
        dfcm.verify_capsule(self.capsule)
        bad = copy.deepcopy(self.capsule)
        bad['fence']['exclusive_do_path'] = 'ambient'
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.verify_capsule(bad)
        self.assertEqual(caught.exception.code, 'CAPSULE_TAMPERED')

    def test_time_bounded_grant_admission(self):
        admission = dfcm.admit_grant(
            self.capsule,
            self.grant(),
            now='2026-08-19T20:30:00Z',
        )
        self.assertTrue(admission['admitted'])
        self.assertFalse(admission['consequential_do_performed'])
        dfcm.verify_admission(admission)

    def test_grant_not_yet_valid_and_expired_refuse(self):
        with self.assertRaises(dfcm.Refusal) as early:
            dfcm.admit_grant(self.capsule, self.grant(), now='2026-08-19T20:00:30Z')
        self.assertEqual(early.exception.code, 'DO_GRANT_NOT_YET_VALID')
        with self.assertRaises(dfcm.Refusal) as late:
            dfcm.admit_grant(self.capsule, self.grant(), now='2026-08-19T21:00:00Z')
        self.assertEqual(late.exception.code, 'DO_GRANT_EXPIRED')

    def test_capsule_and_intent_drift_refuse(self):
        bad_capsule = copy.deepcopy(self.capsule)
        bad_capsule['exclusions'].append('tampered')
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.admit_grant(bad_capsule, self.grant(), now='2026-08-19T20:30:00Z')
        self.assertEqual(caught.exception.code, 'CAPSULE_TAMPERED')

        bad_grant = self.grant(intent_digest='sha256:' + '0' * 64)
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.admit_grant(self.capsule, bad_grant, now='2026-08-19T20:30:00Z')
        self.assertEqual(caught.exception.code, 'DO_INTENT_NOT_SELECTED')

    def test_close_execution_binds_observed_do_without_actuating(self):
        admission = dfcm.admit_grant(self.capsule, self.grant(), now='2026-08-19T20:30:00Z')
        evidence = {
            'subject_sha': admission['subject_sha'],
            'intent_digest': admission['intent_digest'],
            'exit_code': 0,
            'postcondition_verified': True,
            'verifier': 'owning-repository:canonical-verifier',
            'verifier_receipt': 'github-actions:12345',
            'observed_at': '2026-08-19T20:40:00Z',
            'changed': ['bounded-file'],
            'verified': ['exact subject verifier exit=0', 'postcondition matched'],
            'replay': ['canonical verifier --exact-subject'],
        }
        closure = dfcm.close_execution(self.capsule, admission, evidence)
        self.assertEqual(closure['standing'], 'PARTIAL_ALIVE')
        self.assertTrue(closure['promotion_eligible'])
        self.assertFalse(closure['alive_asserted'])
        self.assertFalse(closure['consequential_do_performed_by_controller'])
        self.assertTrue(closure['replay'].startswith('ALIVE:REPLAY:4:'))
        self.assertEqual(closure['next_transition'], 'OWNING_MANIFEST_STANDING_ADMISSION')

    def test_execution_outside_authority_window_refuses(self):
        admission = dfcm.admit_grant(self.capsule, self.grant(), now='2026-08-19T20:30:00Z')
        base = {
            'subject_sha': admission['subject_sha'],
            'intent_digest': admission['intent_digest'],
            'exit_code': 0,
            'postcondition_verified': True,
            'verifier': 'verifier',
            'verifier_receipt': 'receipt',
            'changed': [],
            'verified': ['ok'],
            'replay': ['cmd'],
        }
        before = dict(base, observed_at='2026-08-19T20:00:30Z')
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.close_execution(self.capsule, admission, before)
        self.assertEqual(caught.exception.code, 'EXECUTION_BEFORE_AUTHORITY_WINDOW')
        after = dict(base, observed_at='2026-08-19T21:00:00Z')
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.close_execution(self.capsule, admission, after)
        self.assertEqual(caught.exception.code, 'EXECUTION_AFTER_AUTHORITY_EXPIRY')

    def test_tampered_admission_and_evidence_chain_refuse(self):
        admission = dfcm.admit_grant(self.capsule, self.grant(), now='2026-08-19T20:30:00Z')
        tampered = copy.deepcopy(admission)
        tampered['authority_id'] = 'authority:attacker'
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.verify_admission(tampered)
        self.assertEqual(caught.exception.code, 'ADMISSION_TAMPERED')

        first = dfcm.evidence_event('A', {'x': 1})
        second = dfcm.evidence_event('B', {'x': 2}, first['event_digest'])
        events = [first, second]
        self.assertTrue(dfcm.replay_evidence(events).startswith('ALIVE:REPLAY:2:'))
        events[1]['payload']['x'] = 3
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.replay_evidence(events)
        self.assertEqual(caught.exception.code, 'EVIDENCE_TAMPERED')

    def test_no_lawful_frontier_refuses_but_preserve_still_exposes_topology(self):
        subject = manifest(component('u', 'UNSUPPORTED'), required_roles=('u',))
        preserved = dfcm.preserve(subject)
        self.assertEqual(preserved['blocked'][0]['component'], 'u')
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.construct_capsule(subject)
        self.assertEqual(caught.exception.code, 'NO_LAWFUL_FRONTIER')


if __name__ == '__main__':
    unittest.main()
