---
title: "[arXiv] Team Unibuc - NLP at SemEval-2024 Task 8: Transformer and Hybrid Deep Learning Based Models for Machine-Generated Text Detection"
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

- **著者**: Teodor-George Marchitan, Claudiu Creanga, Liviu P. Dinu
- **arXiv ID**: [2405.17964](https://arxiv.org/abs/2405.17964)
- **PDF**: [Link](https://arxiv.org/pdf/2405.17964.pdf)

## 要約

UniBuc-NLPチームがSemEval 2024タスク8（機械生成テキスト検出）に取り組んだアプローチを報告している。トランスフォーマーベースとハイブリッド深層学習アーキテクチャを探索し、サブタスクBでは77チーム中2位（精度86.95%）を達成した。しかし、サブタスクAでは過学習が発生し、サブタスクC（トークンレベル分類）でもハイブリッドモデルが過学習により人間と機械生成テキストの境界検出に失敗した。

## 主要なポイント

1. サブタスクBにおいて、トランスフォーマーベースモデルが86.95%の精度で77チーム中2位という優れた成績を達成し、このタスクへの適合性を実証した
2. サブタスクAでは過学習が発生したが、ファインチューニングの削減と最大シーケンス長の増加により改善可能と示唆している
3. サブタスクC（トークンレベル分類）では、ハイブリッドモデルが訓練時に過学習し、人間と機械生成テキストの遷移検出能力が阻害された

## 意義・影響

この研究は、機械生成テキストの検出において異なるアーキテクチャの有効性と限界を明らかにし、特にトランスフォーマーベースモデルの優位性を実証した。過学習への対処法も提案されており、今後の機械生成テキスト検出システムの改善に貢献する知見を提供している。

#1

