#!/bin/bash

# 1. 先提交當前更改
git add .gitignore tools/
git commit -m "更新 gitignore 和工具腳本"

# 2. 同步同事的分支
git fetch origin
git checkout -b fix/voice-order-feature origin/fix/voice-order-feature

# 3. 測試同事的功能後再合併
git checkout feature/integration
git merge fix/voice-order-feature

# 4. 解決衝突後推送
git push origin feature/integration
