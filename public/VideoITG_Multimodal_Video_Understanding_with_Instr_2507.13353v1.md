---
title: >-
  [arXiv] VideoITG: Multimodal Video Understanding with Instructed Temporal
  Grounding
tags:
  - Python
  - 機械学習
  - 論文
  - AI
  - arXiv
private: false
updated_at: '2025-07-20T06:41:35+09:00'
id: 4d4b73a7f56f3c6b847b
organization_url_name: null
slide: false
ignorePublish: false
---

# VideoITG: Multimodal Video Understanding with Instructed Temporal
  Grounding

## 論文情報

- **著者**: Shihao Wang, Guo Chen, De-an Huang, Zhiqi Li, Minghan Li, Guilin Li, Jose M. Alvarez, Lei Zhang, Zhiding Yu
- **arXiv ID**: [2507.13353v1](http://arxiv.org/abs/2507.13353v1)
- **PDF**: [Link](https://arxiv.org/pdf/2507.13353v1.pdf)

## 要約

VideoITGは、ユーザーの指示に基づいて動画フレームを効果的に選択する新しい手法である。従来の教師なし学習アプローチとは異なり、VidThinkerという自動アノテーションフレームワークを通じて人間のアノテーション過程を模倣し、指示に合致した時間的グラウンディング（temporal grounding）を実現する。このアプローチにより、長い動画の理解において複雑なシナリオに対応でき、Video Large Language Models（Video-LLMs）の性能を大幅に向上させることができる。

## 主要なポイント

1. **VidThinkerパイプライン**: 指示条件付きでクリップレベルの詳細キャプションを生成し、指示誘導推論を通じて関連動画セグメントを検索、最終的に最も情報量の多い視覚的証拠を特定する自動アノテーションフレームワーク
2. **VideoITG-40Kデータセット**: 40,000本の動画と500,000件の指示付き時間的グラウンディングアノテーションを含む大規模データセットの構築
3. **プラグアンドプレイ対応**: Video-LLMsの視覚言語アライメントと推論能力を活用し、識別的な方法で効果的なフレーム選択を行うモデル設計

## 意義・影響

この研究は、動画理解における情報量の多いフレーム選択という根本的な問題に対して、指示ベースの新しいアプローチを提案している。複数のマルチモーダル動画理解ベンチマークで一貫した性能向上を達成しており、長時間動画の理解や実用的な動画AI応用の発展に大きく貢献する可能性がある。

#1

## 参考リンク

- [arXiv](http://arxiv.org/abs/2507.13353v1)
- [PDF](https://arxiv.org/pdf/2507.13353v1.pdf)

---

この記事は自動生成されました。論文の詳細については、元の論文をご確認ください。
