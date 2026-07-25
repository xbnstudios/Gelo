#!/usr/bin/env bash
set -eou pipefail

case "$SELFCI_JOB_NAME" in
  main)
    uv sync
    selfci job start "lint"
    selfci job start "test"
    ;;
  test)
    #nix build -L .#ci.test
		uv run pytest
    ;;
  lint)
    #nix build -L .#ci.lint
		nix-shell -p ty --command "ty check"
    ;;
  *)
    echo "Unknown job: $SELFCI_JOB_NAME"
    exit 1
esac
