.PHONY: verify test survey survey-check crown audit-stubs west-check west-plan

verify:
	python3 scripts/verify_release.py --check-refs
	python3 scripts/verify_portfolio.py

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

survey:
	python3 scripts/survey_portfolio.py --output-dir .artifacts/portfolio-survey --fail-on-blocking

survey-check:
	python3 scripts/survey_portfolio.py --output-dir .artifacts/portfolio-survey --fail-on-blocking --require-policy-current

crown:
	python3 scripts/verify_release.py --check-refs --require-alive

audit-stubs:
	python3 scripts/audit_stubs_wip.py --write

west-check:
	python3 scripts/verify_west_workspace.py --json

west-plan:
	west dfcm-plan --all --json
