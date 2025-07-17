# Makefile for Resymot Stress Test Ansible Project
# Following official Ansible best practices

.PHONY: help ping setup full-test start stop clean lint ping-staging full-test-staging start-staging stop-staging

# Default target
help:
	@echo "Available targets:"
	@echo "  ping             - Test connection to all nodes (production)"
	@echo "  full-test        - Run complete stress test (production)"
	@echo "  start            - Start stress test only (production)"
	@echo "  stop             - Stop stress test and cleanup"
	@echo "  clean            - Clean up logs and temporary files"
	@echo "  lint             - Lint playbooks and roles"
	@echo ""
	@echo "Environment-specific targets:"
	@echo "  ping-staging     - Test connection to staging nodes"
	@echo "  full-test-staging - Full test on staging (start, wait, stop)"
	@echo "  start-staging    - Start stress test only on staging"
	@echo "  stop-staging     - Stop stress test on staging"

# Production environment (default)
ping:
	ansible all -i production -m ping

# Run full stress test (start, wait duration, stop)
full-test:
	ansible-playbook -i production stress_test.yml

# Start stress test only (no automatic stop)
start:
	ansible-playbook -i production start_stress_test.yml

# Stop stress test and cleanup all processes
stop:
	ansible-playbook -i production stop_stress_test.yml

# Clean up logs and temporary files
clean:
	rm -rf logs/
	rm -f *.log
	@echo "Cleaned up logs and temporary files"

# Lint playbooks and roles
lint:
	ansible-lint *.yml
	ansible-lint roles/

# Staging environment
ping-staging:
	ansible all -i staging -m ping

# Run full stress test on staging (start, wait duration, stop)
full-test-staging:
	ansible-playbook -i staging stress_test.yml

# Start stress test only on staging (no automatic stop)
start-staging:
	ansible-playbook -i staging start_stress_test.yml

# Stop stress test on staging and cleanup all processes
stop-staging:
	ansible-playbook -i staging stop_stress_test.yml
