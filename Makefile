.PHONY: verify test crown

verify:
	python3 scripts/verify_release.py --check-refs
	python3 scripts/verify_portfolio.py

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

crown:
	python3 scripts/verify_release.py --check-refs --require-alive
