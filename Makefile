###########################################
# Run AVD with various tags               #
# #########################################

.PHONY: help
help: ## Display help message
	@grep -E '^[0-9a-zA-Z_-]+\.*[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: deploy_dc1_dci
deploy_dc1_dci: ## Deploy DC1 DCI configs to non-avd devices
	ansible-playbook playbooks/deploy_dc1_dci_eapi.yml -i sites/dc1/inventory.yml

.PHONY: deploy_dc2_dci
deploy_dc2_dci: ## Deploy DC1 DCI configs to non-avd devices
	ansible-playbook playbooks/deploy_dc2_dci_eapi.yml -i sites/dc2/inventory.yml

.PHONY: deploy_dc1_dci_cvp
deploy_dc1_dci_cvp: ## Deploy DC1 DCI configs to non-avd devices through CVP
	ansible-playbook playbooks/deploy_dc1_dci_cvp.yml -i sites/dc1/inventory.yml

.PHONY: deploy_dc2_dci_cvp
deploy_dc2_dci_cvp: ## Deploy DC2 DCI configs to non-avd devices through CVP
	ansible-playbook playbooks/deploy_dc2_dci_cvp.yml -i sites/dc2/inventory.yml

.PHONY: deploy_dc1_host_cvp
deploy_dc1_host_cvp: ## Deploy DC1 s1-host1/host2 configs to non-avd devices through CVP
	ansible-playbook playbooks/deploy_dc1_host_cvp.yml -i sites/dc1/inventory.yml

.PHONY: deploy_dc1_srv6_cvp
deploy_dc1_srv6_cvp: ## [DESTRUCTIVE] Repurpose s1-spine1/2,leaf1-3,host1/2 for SRv6 uSID demo, tearing down DC1 EVPN-VXLAN
	ansible-playbook playbooks/deploy_dc1_srv6_cvp.yml -i sites/srv6-dc1/inventory.yml

.PHONY: deploy_dc2_host_cvp
deploy_dc2_host_cvp: ## Deploy DC2 s2-host1/host2 configs to non-avd devices through CVP
	ansible-playbook playbooks/deploy_dc2_host_cvp.yml -i sites/dc2/inventory.yml

.PHONY: build_dc1
build_dc1: ## Build AVD Configs for DC1
	ansible-playbook playbooks/build_dc1.yml -i sites/dc1/inventory.yml

.PHONY: build_dc2
build_dc2: ## Build AVD Configs for DC2
	ansible-playbook playbooks/build_dc2.yml -i sites/dc2/inventory.yml

.PHONY: deploy_dc1_cvp
deploy_dc1_cvp: ## Deploy DC1 AVD Configs Through CVP
	ansible-playbook playbooks/deploy_dc1_cvp.yml -i sites/dc1/inventory.yml

.PHONY: deploy_dc2_cvp
deploy_dc2_cvp: ## Deploy DC2 AVD Configs Through CVP
	ansible-playbook playbooks/deploy_dc2_cvp.yml -i sites/dc2/inventory.yml

.PHONY: deploy_dc1_eapi
deploy_dc1_eapi: ## Deploy DC1 Spine/Leaf AVD generated configs via eAPI
	ansible-playbook playbooks/deploy_dc1_eapi.yml -i sites/dc1/inventory.yml

.PHONY: deploy_dc2_eapi
deploy_dc2_eapi: ## Deploy DC1 Spine/Leaf AVD generated configs via eAPI
	ansible-playbook playbooks/deploy_dc2_eapi.yml -i sites/dc2/inventory.yml

.PHONY: verify_dc1
verify_dc1: ## Run ANTA validation against DC1 EOS devices without pushing config
	ansible-playbook playbooks/verify_dc1.yml -i sites/dc1/inventory.yml

.PHONY: verify_dc2
verify_dc2: ## Run ANTA validation against DC2 EOS devices without pushing config
	ansible-playbook playbooks/verify_dc2.yml -i sites/dc2/inventory.yml

.PHONY: bf_install
bf_install: ## Install the Batfish service (JRE + allinone image + pybatfish)
	./batfish/install_batfish.sh

.PHONY: bf_start
bf_start: ## Start the Batfish service
	./batfish/batfishctl.sh start

.PHONY: bf_stop
bf_stop: ## Stop the Batfish service
	./batfish/batfishctl.sh stop

.PHONY: bf_status
bf_status: ## Show Batfish service status
	./batfish/batfishctl.sh status

.PHONY: preflight
preflight: ## Batfish pre-deploy validation of dc1+dc2 intended configs (all lab scenarios)
	python3 batfish/preflight.py --dc all --labs all

.PHONY: preflight_dc1
preflight_dc1: ## Batfish pre-deploy validation of DC1 only
	python3 batfish/preflight.py --dc dc1 --labs all

.PHONY: preflight_dc2
preflight_dc2: ## Batfish pre-deploy validation of DC2 only
	python3 batfish/preflight.py --dc dc2 --labs all

.PHONY: preflight_selftest
preflight_selftest: ## Inject faults into snapshot copies to prove the pre-flight checks catch them
	python3 batfish/selftest.py
