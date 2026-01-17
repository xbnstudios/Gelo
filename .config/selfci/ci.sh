#!/usr/bin/env bash
set -eou pipefail

case "$SELFCI_JOB_NAME" in
  main)
    selfci job start "lint"
    selfci job start "test"
    ;;
  test)
    nix build -L .#ci.test
    ;;
  lint)
    nix build -L .#ci.lint
    ;;
  *)
    echo "Unknown job: $SELFCI_JOB_NAME"
    exit 1
esac
