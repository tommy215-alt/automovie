# 009 素材の一覧（出典と権利）

取得日：2026-11-16

## 映像

| ファイル（`assets/`） | 中身 | 作者 | ライセンス | 出典 |
|---|---|---|---|---|
| usaf_mwd_axel.webm | 「Military Working Dog Retirement」（60 秒、1920×1080、撮影 2025-07-24／25） | U.S. Air Force video by Airman 1st Class Jessica Mun（米空軍、AFN Spangdahlem） | **パブリックドメイン**（米国の連邦政府の著作物。Commons のファイルのページで「Public domain」、DVIDS の元のページでも「PUBLIC DOMAIN」と表示されているのを 11-16 に確かめた） | https://commons.wikimedia.org/wiki/File:Military_Working_Dog_Retirement_(972398).webm ／元：https://www.dvidshub.net/video/972398/military-working-dog-retirement |

- 使う予定の部分（`script.json` の blocks。声を作ってから確定）：25.4〜28.2 秒（すわる犬の大写し）、7.1〜8.7 秒（車の「MILITARY WORKING DOG」の文字）、14.6〜17.5 秒（式の壇上）、17.7〜21.5 秒（客席と犬）、21.7〜25.2 秒（壇上）、35.8〜39.5 秒（ベッドでひと休み）、45.8〜48.6 秒（車の横の犬の大写し）、32.2〜35.5 秒（ベッドの上の大写し）、48.9〜54.2 秒（隊員と犬）。
- 加工：横長の映像から 1060×1080 を切り出す（場面ごとに位置を変える）、順番の組み替え。
- **元の動画の音（ナレーション・インタビュー・音楽）は使わない。**
- 画面右上の AFN のロゴは、切り出しの位置（左から 390 以下）で外す。下の帯の文字（9〜13 秒、40〜44 秒、54〜57 秒）が出る時間は使わない。**書き出したあと、コマの一覧でロゴと帯が入っていないことを確かめる。**
- 写っている人：米空軍の隊員（公務中、公式の広報映像）。名前は出さない。
- DVIDS の決まり（https://www.dvidshub.net/about/copyright）：国防総省の映像を使っても、国防総省が支持・推奨していることにはならない、と説明欄に書く。

## 音声

| 素材 | 出典 | 権利 |
|---|---|---|
| ナレーション | VOICEVOX、青山龍星（ノーマル）。**未作成** | 「VOICEVOX:青山龍星」のクレジットで商用可（個人の利用） |
| BGM `assets/bgm_americana.mp3` | 「Americana」Kevin MacLeod（incompetech.com）。チェロ、木管、フレンチホルン、トロンボーン、チューバ、打楽器、チェレスタ、バイオリン。104 BPM、3 分 22 秒。https://incompetech.com/music/royalty-free/mp3-royaltyfree/Americana.mp3 | **CC BY 4.0**（クレジット必須）。配布元の FAQ https://incompetech.com/music/royalty-free/faq.html |

BGM の選び方（制作のセッションが決定）：狙う感情は感動で、目安は「後半で大きく盛り上がる曲」（`docs/DESIGN.md` 3b）。配布元の一覧で曲調が「Epic, Uplifting」、説明が「チェロと木管で素朴に始まり、金管を重ねて壮大になっていく」という曲を選んだ。**強いのは盛り上がり**（金管が重なる後半）。軍の式典という絵にも合うと考えた。曲調に Calming・Relaxed は入っていない。004（Heartwarming）、005（Strength of the Titans）、006（Reunited）、007（Carefree）、008（The Descent）とは別の曲。**音は聞けていない。**
入れ方（未実施）：声を作ったあと `python -X utf8 tools/bgm_peak.py videos/009/assets/bgm_americana.mp3 動画の秒数 山場の秒` で盛り上がりの位置を測り、`script.json` の bgm に `"start"` を書く（山場は「引き取りました」の行）。音量は声より 13 dB 下。

## 自作
題・字幕・出典の文字（フォント：Noto Sans JP、SIL OFL）。

## 使っていないもの（確認）
他人の投稿動画、スポーツ中継、テレビ・映画・アニメの映像、市販の曲は使っていない。

## 説明欄に書くクレジット
映像：U.S. Air Force（米空軍、パブリックドメイン）。米国防総省の映像の使用は、同省による支持・推奨を意味しません。／音声：VOICEVOX:青山龍星
音楽：Americana Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 https://creativecommons.org/licenses/by/4.0/
