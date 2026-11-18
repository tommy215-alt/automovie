# 010 素材の一覧（出典と権利）

取得日：2026-11-18

## 映像

| ファイル（`assets/`） | 中身 | 作者 | ライセンス | 出典 |
|---|---|---|---|---|
| a17_giants_jsc.mp4 | NASA の記録映画「Apollo 17: On the Shoulders of Giants」（JSC 603、1973 年、28 分 36 秒、720×480） | NASA（ジョンソン宇宙センター） | **パブリックドメイン**（米国の連邦政府の著作物）。同じ映画の Commons のページで「Public domain／作者 NASA／Copyrighted: False」と表示されているのを 11-18 に確かめた | 取得元：Internet Archive の NASA のコレクション（作者「NASA/JSC」、コレクション「nasa」「johnsonspacecentervideocollection」、登録者は nasa.gov のアカウント。11-18 に項目の情報を読んで確かめた）https://archive.org/details/JSC603_Apollo17_On_the_Shoulders_of_Giants.wmv ／権利の表示：https://commons.wikimedia.org/wiki/File:Apollo_17_-_On_the_Shoulders_of_Giants.webm |

- 取得のいきさつ：はじめ Commons から取ろうとしたが、回数制限（429）が 1 時間半たっても解けなかった（回避はしていない）。同じ映画を NASA 自身が Internet Archive に置いているので、そちらから取った。
- **使っていないもの（assets/ に残っているが完成版には入っていない）**：`a17_giants.mp4`（同じ映画の、第三者が Internet Archive に登録した版。640×480。位置を調べるのに使っただけ）、`a17_jsc_43.mp4`（縦横比を直そうとして作った中間ファイル。直す必要がなかったので使っていない）。Commons の短い 2 本（`Ap17_strolling.ogv`、`Ap17_schmitt_falls.ogv`）は取れておらず、使っていない。
- 使う部分（`script.json` の blocks。秒は a17_giants_jsc.mp4 の位置）：917.4〜（歩いていて前に転ぶ）、1236.9〜（旗と 2 人）、544.1〜（観測装置をかついで跳ねて運ぶ）、1204.9〜（こちらへ跳ねてくる）、610.3〜（1 人が地面に倒れ、もう 1 人が起こす）、924.75〜927.7（笑う管制室の職員）、1164.95〜1170.2（正面の大写し）と 1047.8〜（遠くを跳ねて進む）。
- 加工：720×480 から 472×480 を切り出して拡大（場面ごとに位置を変える）、順番の組み替え。元が 1972 年のテレビ中継と 16 ミリフィルムなので、絵は粗い。
- **元の映画の音（ナレーション・交信・音楽）は使わない。**
- 映画に入っている名前の字幕が重なる時間は使わない。**書き出したあと、コマの一覧で字幕が入っていないことを確かめる。**
- 写っている人：宇宙飛行士 2 人（公務中、宇宙服で顔は見えない）と、管制室の NASA の職員（公務中、NASA 自身の記録映画に写っている場面。3 秒ほど。名前は出さない）。名前を言うのは、公式の記録にあるシュミット飛行士だけ。
- NASA の映像の使い方の決まり（https://www.nasa.gov/nasa-brand-center/images-and-media/）：NASA が支持・推奨しているように見せない。NASA のロゴは使っていない。

## 音声

| 素材 | 出典 | 権利 |
|---|---|---|
| ナレーション | VOICEVOX、青山龍星（ノーマル）、速さ 1.15 | 「VOICEVOX:青山龍星」のクレジットで商用可（個人の利用） |
| BGM `assets/bgm_fluffing_a_duck.mp3` | 「Fluffing a Duck」Kevin MacLeod（incompetech.com）。チューバ、フルート、トロンボーン、バスクラリネット、クラリネット、打楽器。122 BPM、67 秒。https://incompetech.com/music/royalty-free/mp3-royaltyfree/Fluffing%20a%20Duck.mp3 | **CC BY 4.0**（クレジット必須）。配布元の FAQ https://incompetech.com/music/royalty-free/faq.html |

BGM の選び方（自動の回が決定）：狙う感情は「笑える」で、目安は「とぼけた旋律が耳に残る曲」（`docs/DESIGN.md` 3b）。配布元の一覧で曲調が「Bouncy, Bright, Humorous」、説明が「トロンボーンがおどけた旋律を吹き、ティンパニと木管が付く」という曲を選んだ。**強いのは旋律**（トロンボーン）と拍。転ぶ絵に合うと考えた。曲調に Calming・Relaxed は入っていない。004（Heartwarming）、005（Strength of the Titans）、006（Reunited）、007（Carefree）、008（The Descent）、009（Americana）とは別の曲。**音は聞けていない。**
入れ方：`bgm_peak.py` で測ると、曲はほぼ同じ大きさで続き（1 秒ごとに −17〜−21 dB）、27〜29 秒がいちばん大きく（−17 dB）、30 秒に一瞬の切れ目（−31 dB）がある。**曲の 8 秒から使い**、大きい所が動画の 19〜21 秒（山場の「そして、また転びます」）に、切れ目が 22 秒あたり（「くるりと回って」の前）に来るようにした。音量は声より 13 dB 下。

## 自作
題・字幕・出典の文字（フォント：Noto Sans JP、SIL OFL）。

## 使っていないもの（確認）
他人の投稿動画、スポーツ中継、テレビ・映画・アニメの映像、市販の曲は使っていない（使った映画は NASA 自身が作った記録映画）。

## 説明欄に書くクレジット
映像：NASA（パブリックドメイン）「Apollo 17: On the Shoulders of Giants」より。NASA の映像の使用は、NASA による支持・推奨を意味しません。／音声：VOICEVOX:青山龍星
音楽：Fluffing a Duck Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 https://creativecommons.org/licenses/by/4.0/
