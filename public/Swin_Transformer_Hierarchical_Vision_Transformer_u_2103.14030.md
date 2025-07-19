---
title: "[arXiv] Swin Transformer: Hierarchical Vision Transformer using Shifted Windows"
tags:
  - "機械学習"
  - "AI"
  - "論文"
  - "arXiv"
  - "Python"
private: false
updated_at: ""
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

## 論文情報

- **著者**: Ze Liu, Yutong Lin, Yue Cao, Han Hu, Yixuan Wei, Zheng Zhang, Stephen Lin, B. Guo
- **arXiv ID**: [2103.14030](https://arxiv.org/abs/2103.14030)
- **PDF**: [Link](https://arxiv.org/pdf/2103.14030.pdf)

## 要約

Swin Transformerは、コンピュータビジョンの汎用バックボーンとして機能する新しいビジョンTransformerです。シフトされたウィンドウを使用した階層的なアーキテクチャにより、局所的な自己注意計算と効率的なクロスウィンドウ接続を実現しています。画像サイズに対して線形の計算複雑度を持ち、画像分類から物体検出、セマンティックセグメンテーションまで幅広いビジョンタスクで最先端の性能を達成しました。

## 主要なポイント

1. **シフトウィンドウメカニズム**: 重複しない局所ウィンドウ内で自己注意を計算し、ウィンドウ間の接続を可能にすることで、計算効率と表現力のバランスを実現
2. **階層的アーキテクチャ**: 異なるスケールでのモデリングが可能で、画像サイズに対して線形の計算複雑度を維持
3. **優れた性能**: ImageNet-1Kで87.3%の精度、COCOで58.7 box AP、ADE20Kで53.5 mIoUを達成し、従来の最先端を大幅に上回る

## 意義・影響

この研究は、Transformerベースのモデルがコンピュータビジョンのバックボーンとして極めて有効であることを実証しました。シフトウィンドウアプローチは計算効率と性能の両立という長年の課題を解決し、その後の多くのビジョンTransformerの設計に影響を与えています。

#1

