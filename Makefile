.PHONY: install clean

install:
	python3 install.py

clean:
	find ~ -name '*.bak' -exec rm -rf {} +
