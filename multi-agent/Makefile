.PHONY: install test test-e2e fault-drill demo-fig01 demo-fig02 demo-happy test-metrics ci

install:
	pip install -e ".[dev]"

test:
	pytest -q

ci: test fault-drill

test-e2e:
	pytest -q tests/test_figure01_skeleton.py tests/test_e2e_refund_coupon.py

fault-drill:
	python scripts/fault_drill/run_all.py

demo-fig01:
	python -m multi_agent.demo figure-01

demo-fig02:
	python -m multi_agent.demo figure-02

test-metrics:
	pytest -q -m metrics

demo-happy:
	python -m multi_agent.demo happy