# 011 素材の一覧（出典と権利）

取得日：2026-11-19

## 映像

| ファイル（`assets/`） | 中身 | 作者 | ライセンス | 出典 |
|---|---|---|---|---|
| arecibo_nsf_ia.mp4 | NSF が公開した「アレシボ天文台の崩落」の映像（2020-12-01）。前半が管制塔のカメラ、後半が天文台のドローン。最後に NSF のロゴ。1280×720、117.7 秒 | U.S. National Science Foundation（撮影：Arecibo Observatory、NSF の施設） | **CC BY 3.0**（NSF が公式の YouTube チャンネルで「クリエイティブ・コモンズ 表示」として公開）。Commons の同じ映像のページで「CC BY 3.0／作者 National Science Foundation／YouTube の NSF 公式チャンネル ssHkMWcGat4」と表示され、2020-12-08 に Commons の確認役がライセンスを確かめた記録（YouTubeReview、Wayback Machine の保存つき）があることを、11-19 にそのページの本文で確かめた。同じ映像の別の Commons のページ（管制塔の場面、ドローンの場面）は「Public domain（PD-USGov-NSF）」の扱い | ライセンスの表示：https://commons.wikimedia.org/wiki/File:Footage_of_Collapse_Arecibo_Observatory.webm ／ NSF の公開元：https://www.youtube.com/watch?v=ssHkMWcGat4 、https://www.nsf.gov/news/special_reports/arecibo/ ／ **取得元**：Internet Archive https://archive.org/details/nsf-drone-footage-collapse-arecibo-observatory （作者「National Science Foundation」、出どころ nsf.gov の特設ページ。登録したのは第三者の個人で、ライセンスの指定はない） |

- 取得のいきさつ：はじめ Commons から取ろうとしたが、本体の置き場が回数制限（429）を返した（10:04〜10:16）。回避はせず、同じ NSF の映像を Internet Archive から取った。**Internet Archive の版は第三者の登録なので、権利の根拠はその登録ではなく NSF 自身の CC BY の公開に置く。** 取った版の中身（冒頭の題字「Courtesy of the Arecibo Observatory, a U.S. National Science Foundation Facility」、管制塔の映像、ドローンの映像、最後の NSF のロゴ）を 2 秒ごとのコマで確かめ、NSF の公開した映像に第三者の編集・文字・音楽が足されていないことを見た（音は使わないので聞いていない）。Commons の版（113.7 秒）より 4 秒長いのは、最後の NSF のロゴの長さの違いと見る。
- 使う部分（秒は arecibo_nsf_ia.mp4 の位置）：72.8〜77.5（皿に落ちた装置と煙）、4.6〜12.4（管制塔から見た、吊られた装置の無事な姿）、56.2〜64.6（ドローンの大写し、ケーブルの受け口）、12.4〜21.0（装置が傾いて落ちる）、64.6〜72.6（ケーブルが切れ、ドローンが皿の方を向く）、77.6〜112.5（煙の残る皿と塔）。題字の画面（0〜3.5、50〜55 秒）と NSF のロゴ（113 秒〜）は使わない。
- 加工：1280×720 から 708×720 を切り出して拡大（場面ごとに位置を変える。管制塔の映像の左下の撮影時刻の文字は切り出しの外）、順番の組み替え。ドローンの映像の中央に小さく入っている「Arecibo Observatory Drone」の文字は元の映像のまま（NSF の公開版に入っているもの）。
- **元の映像の音は使わない。**
- 写っている人：いない。
- 説明欄に「NSF による支持・推奨を意味しない」と書く。

## 音声

| 素材 | 出典 | 権利 |
|---|---|---|
| ナレーション | VOICEVOX、青山龍星（ノーマル）、速さ 1.15 | 「VOICEVOX:青山龍星」のクレジットで商用可（個人の利用） |
| BGM `assets/bgm_for_the_fallen.mp3` | 「For the Fallen」Kevin MacLeod（incompetech.com）。金管、弦、打楽器。52 BPM、95 秒。https://incompetech.com/music/royalty-free/mp3-royaltyfree/For%20the%20Fallen.mp3 | **CC BY 4.0**（クレジット必須）。配布元の FAQ https://incompetech.com/music/royalty-free/faq.html |

BGM の選び方（自動の回が決定）：狙う感情は「悲しい」で、目安は「旋律のはっきりした弦・ピアノ」（`docs/DESIGN.md` 3b）。配布元の一覧で曲調が「Epic, Intense, Somber」、説明が「グロッケンシュピールの入った美しい和音で始まり、感情をこめて少しずつ盛り上がる。半ばで行進の太鼓が入って高まる」という曲を選んだ。**強いのは盛り上がり**（半ばの太鼓）と弦・金管の旋律。失われたものを悼む曲調が、57 年続いた望遠鏡の最期に合うと考えた。曲調に Calming・Relaxed は入っていない。004〜010 の曲（Heartwarming、Strength of the Titans、Reunited、Carefree、The Descent、Americana、Fluffing a Duck）とは別の曲。**音は聞けていない。**
入れ方：`bgm_peak.py` で測ると、曲は 0〜37 秒で少しずつ大きくなり（−30 → −17 dB）、38〜43 秒に静かな谷（−33 dB）、45〜47 秒で一気に大きくなる（−17 dB。太鼓が入る所と見る）。**曲の 17 秒から使い**、谷が動画の 22〜26 秒（「作業員の命が危ない」「取り壊しが決まりました」）に、盛り上がりが動画の 28〜30 秒（山場の「900トンの装置が、落ちました」）に来るようにした。音量は声より 13 dB 下。

## 自作
題・字幕・出典の文字（フォント：Noto Sans JP、SIL OFL）。

## 使っていないもの（確認）
他人の投稿動画（NSF 自身の公式の公開は除く）、スポーツ中継、テレビ・映画・アニメの映像、市販の曲は使っていない。

## 説明欄に書くクレジット
映像：U.S. National Science Foundation「Footage of Arecibo Observatory collapse」（Courtesy of the Arecibo Observatory, a U.S. National Science Foundation facility）Licensed under CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ 切り出し・並べ替え・文字入れの加工あり。NSF による支持・推奨を意味しません。／音声：VOICEVOX:青山龍星
音楽：For the Fallen Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 https://creativecommons.org/licenses/by/4.0/
