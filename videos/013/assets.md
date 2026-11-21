# 013 素材の出典と権利

## 映像
| ファイル | 中身 | 出典 | 権利 |
|---|---|---|---|
| `assets/pov-polar-bear-collar-cam-b-roll-2019-2021-and-2022.mp4`（6 分 2 秒、1920×1080、30 fps） | 北極グマに付けた GPS つきカメラの首輪の映像（クマの目線）。カナダ・ワプスク国立公園とチャーチル近く、ハドソン湾。2019・2021・2022 年の 8〜9 月 | U.S. Geological Survey（USGS）の映像のページ「POV Polar Bear Collar Cam B-roll 2019, 2021, and 2022」（2024-02-02）https://www.usgs.gov/media/videos/pov-polar-bear-collar-cam-b-roll-2019-2021-and-2022 。ファイルはそのページの「Download Video」（USGS の保管先 usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com …/PolarBearCollarCamera.mp4、815.8 MB）から取った | **パブリックドメイン**。ページの「Sources/Usage」に「Public Domain.」と明記。クレジット：Polar Bear Footage: Anthony Pagano (USGS)。撮影者は USGS の研究者（米国連邦政府職員が職務で作った著作物） |

- 使った区間（素材の秒）：190〜195（海面から顔を出すクマ、水中のクマ）、26〜33（陸で休むクマ）、110〜117（浜を歩く）、208〜221（木の実・草・トナカイの角）、76〜86（浜）、316〜326・340〜343（シロイルカの死がいのまわりを泳ぐ）、105〜110（海を見る）。
- 元の映像の右下の英語の説明の字幕と左下の USGS のロゴは、切り出し（上から 880 の高さ）で外した。コマの一覧で写っていないことを確かめた。冒頭と最後の USGS のロゴ・説明・クレジットの画面は使っていない。
- **使わなかった場面**：鳥の死がいを食べる場面（血が写る。素材の 1:21〜1:26、2:30〜2:36、3:26〜3:43 あたり）、シロイルカに赤い所が写る区間（331〜340 秒あたり）。
- 元の映像の音は使っていない。
- 写っている人：いない。
- 説明欄に「USGS による支持・推奨を意味しない」と書く。
- 研究の支援に Polar Bears International なども入っているが（WSU の発表）、この映像の撮影者は USGS の Anthony Pagano 氏とページに書かれ、ページの表示はパブリックドメイン。2014〜2016 年の別の B-roll（Polar Bears International・WWF カナダと共同で撮った分を含む）は使っていない。

## 声
- VOICEVOX:青山龍星（`tools/voice.py`、話者 13、速さ 1.15）。クレジットを画面の下と説明欄に表示。

## BGM
| ファイル | 曲 | 出典 | 権利 |
|---|---|---|---|
| `assets/bgm_rains_will_fall.mp3` | Rains Will Fall（Kevin MacLeod、3 分 42 秒、85 BPM、ピアノ・ドラム・弦） | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Rains%20Will%20Fall.mp3 （一覧 pieces.json の項目） | CC BY 4.0。クレジット：Rains Will Fall Kevin MacLeod (incompetech.com) / Licensed under Creative Commons: By Attribution 4.0 / https://creativecommons.org/licenses/by/4.0/ |

BGM の選び方（自動の回が決定）：狙う感情は「悲しい」で、目安は「旋律のはっきりした弦・ピアノ」（`docs/DESIGN.md` 3b）。配布元の一覧で曲調が「Calming, Somber, Uplifting」、説明が「ピアノが物悲しいワルツの旋律を弾き、弦がそっと入る。2 分目の半ばから少し希望のある調子に」という曲を選んだ。**強いのは旋律（ピアノ）と、ワルツの拍（ドラム）**。曲調は Calming だけではなく Somber が入っている。直近 5 本（008 The Descent、009 Americana、010 Fluffing a Duck、011 For the Fallen、012 Super Friendly）とは別の曲。**音は聞けていない。**
入れ方：`bgm_peak.py` で測ると、曲は全体に −22〜−28 dB で、140〜186 秒が続けて大きい（169〜184 秒に −21 dB 前後の山）。道具の自動の提案（42 秒の山に合わせて 12 秒から）は山が小さいので使わず、**曲の 142 秒から使い**、大きい所（169〜181 秒）が動画の 27〜39 秒（シロイルカの山場と最後の一言）に来るようにした。音量は声より 13 dB 下（音声の検査は −13 dB のままで合格）。

## 取ったが使わなかった素材（作業フォルダから消した）
- Commons「T-Shirt the Bear Gets Stuck in a Dumpster…」（Placer County Sheriff's Office、PD-CAGov）：429 で取れず。
- USFWS Mountain-Prairie の Flickr のキジオライチョウ 4 本、Katmai NPS の Flickr のクマのじゃれあい 1 本、USGS の木で背中をかくクマ 3 本（320×240）：絵が小さい・粗いので使わない。
