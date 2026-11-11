.PHONY: check extension deb all

check:
	./scripts/check.sh

extension:
	./scripts/build-extension.sh

deb:
	./scripts/build-deb.sh

all: check extension deb
