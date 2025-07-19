#!/bin/bash

# 引数チェック
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_name>"
    echo "Example: $0 'new_article'"
    exit 1
fi

# 第1引数をファイル名として取得
file_name="$1"

git add public/${file_name}

git commit -m "add: ${file_name}"

git push