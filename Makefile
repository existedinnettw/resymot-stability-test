# Makefile for Resymot Stress Test Ansible Project
# Following official Ansible best practices

.PHONY: help ping setup full-test start stop clean lint ping-staging full-test-staging start-staging stop-staging

# Default target
help:
	@echo "Available targets:"
	@echo "  ping             - Test connection to all nodes (production)"
	@echo "  full-test        - Run complete stress test (production)"
	@echo "  clean            - Clean up logs and temporary files"
	@echo "  lint             - Lint playbooks and roles"
	@echo ""
	@echo "Environment-specific targets:"
	@echo "  ping-staging     - Test connection to staging nodes"
	@echo "  full-test-staging - Full test on staging (start, wait, stop)"

# Production environment (default)
ping:
	ansible all -i production -m ping

# Run full stress test (start, wait duration, stop)
full-test:
	ansible-playbook -i production stress_test.yml

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
