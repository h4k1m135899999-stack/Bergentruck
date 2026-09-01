#!/bin/bash

set -e

git fetch origin
git reset --hard origin/main
git clean -fd

echo "✅ Repositório atualizado!"
