---
title: "[arXiv] CogVideoX: Text-to-Video Diffusion Models with An Expert Transformer"
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

- **著者**: Zhuoyi Yang, Jiayan Teng, Wendi Zheng, Ming Ding, Shiyu Huang, Jiazheng Xu, Yuanming Yang, Wenyi Hong, Xiaohan Zhang, Guanyu Feng, Da Yin, Xiaotao Gu, Yuxuan Zhang, Weihan Wang, Yean Cheng, Ting Liu, Bin Xu, Yuxiao Dong, Jie Tang
- **arXiv ID**: [2408.06072](https://arxiv.org/abs/2408.06072)
- **PDF**: [Link](https://arxiv.org/pdf/2408.06072.pdf)

## 要約

CogVideoXは、テキストプロンプトから768×1360ピクセル、16fpsで10秒間の連続した動画を生成できる大規模な拡散トランスフォーマーベースのテキスト・動画生成モデルです。3D変分オートエンコーダー（VAE）による時空間圧縮、エキスパートトランスフォーマーによるテキスト・動画の深い融合、段階的トレーニングとマルチ解像度フレームパック技術により、従来モデルの課題であった動きの少なさや短時間性を克服しています。高品質なデータ処理パイプラインと組み合わせることで、機械評価と人間評価の両方で最先端の性能を達成しました。

## 主要なポイント

1. **3D VAE技術**：空間次元と時間次元の両方でビデオを圧縮し、圧縮率とビデオの忠実度を同時に向上させる新しいアーキテクチャを提案
2. **エキスパートトランスフォーマー**：エキスパート適応LayerNormを用いてテキストと動画の2つのモダリティ間の深い融合を実現し、テキスト・動画のアライメントを大幅に改善
3. **段階的トレーニングとマルチ解像度技術**：長時間で大きな動きのある一貫性のある動画生成を可能にし、様々な形状の動画にも対応

## 意義・影響

この研究は、長時間かつ高品質なテキスト・動画生成を実現することで、動画コンテンツ制作の自動化に大きく貢献します。モデルの重みが公開されていることから、研究コミュニティでの更なる発展が期待され、クリエイティブ産業における新たなアプリケーションの創出につながる可能性があります。

#1

