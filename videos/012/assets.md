# 012 素材の出典と権利

## 映像
| ファイル | 中身 | 出典 | 権利 |
|---|---|---|---|
| `assets/seal_release.mp4`（68.0 秒、1920×1080、23.976 fps） | オレゴン・コースト水族館の職員と BLM のレンジャーが、キタオットセイの子を Yaquina Head の Quarry Cove で放す様子（2018-01） | 撮影：Jeremy Scroggins（BLM＝米国土地管理局の職員）。BLM Oregon & Washington の Flickr https://www.flickr.com/photos/blmoregon/39972565471/ 。Commons に転載 https://commons.wikimedia.org/wiki/File:Seal_pup_released_at_Yaquina_Head_(39972565471).webm | **パブリックドメイン**（米国の連邦政府職員が職務で撮った著作物。Commons の判定は「Public domain」、テンプレート PD-USGov-BLM／分類「PD US BLM」「Flickr videos reviewed by trusted users」）。Flickr の表示は CC BY 2.0（どちらでも改変・商用の再利用が可。説明欄にクレジットを書く） |

- 取り方：Commons の本体（upload.wikimedia.org）は 10:05〜10:13 に 5 回とも回数制限（429）で取れなかった。回避はせず、**同じ映像を、撮った BLM 自身の Flickr のダウンロード（`https://www.flickr.com/video_download.gne?id=39972565471`）から取った**（元のファイル、36.5 MB）。Commons の転載元と同じ写真番号・同じ長さ（68.0 秒）。
- 元の映像に入っている英語の字幕（BLM が入れたもの）は、切り出しで画面の外に出した（コマの一覧で確かめた）。元の映像の音は使っていない。
- 写っている人：水族館の職員と BLM のレンジャー（放流の作業をしている所。名前は出さない）。被害者・未成年・容疑者は写っていない。オットセイの体に小さな赤い所（傷か、識別の札）があるが、流血の場面ではない。4〜6 秒に水族館の車のナンバープレートが写る（団体の車）。
- 説明欄に「BLM による支持・推奨を意味しない」と書く。

## 声
- VOICEVOX:青山龍星（`tools/voice.py`、話者 13、速さ 1.15）。クレジットを画面の下と説明欄に表示。

## BGM
| ファイル | 曲 | 出典 | 権利 |
|---|---|---|---|
| `assets/bgm_super_friendly.mp3` | Super Friendly（Kevin MacLeod、2 分 14 秒、108 BPM、エレクトリックピアノ・合唱・シンセ・ドラム） | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Super%20Friendly.mp3 （一覧 pieces.json の項目。filmmusic.io の頁 https://incompetech.filmmusic.io/song/4442-super-friendly/ ） | CC BY 4.0。クレジット：Super Friendly Kevin MacLeod (incompetech.com) / Licensed under Creative Commons: By Attribution 4.0 / https://creativecommons.org/licenses/by/4.0/ |

BGM の選び方（自動の回が決定）：狙う感情は「感動」で、目安は「後半で大きく盛り上がる曲」（`docs/DESIGN.md` 3b）。配布元の一覧で曲調が「Bouncy, Bright, Uplifting」、説明が「静かに始まって高まり、また静かに戻る。幸せな勝利のような曲（ユーカタストロフ＝悲劇からの思いがけない救い）」という曲を選んだ。**強いのは拍（ドラム）と、合唱が入る盛り上がり**。分析（11-16）で「いい話は軽快で明るい曲で見せるものが多い」と出たことにも合わせた。曲調に Calming・Relaxed は入っていない。直近 5 本（007 Carefree、008 The Descent、009 Americana、010 Fluffing a Duck、011 For the Fallen）とは別の曲。**音は聞けていない。**
入れ方：`bgm_peak.py` で測ると、曲は 2 秒から −20〜−22 dB でほぼ一定、57〜65 秒がいちばん大きい（−17.3 dB）。道具の自動の提案（0 秒から）は使わず、**曲の 25 秒から使い**、大きい所が動画の 32〜40 秒（山場の「波を越えて、外の海へ…歓声が上がりました」と最後の一言）に来るようにした。音量は声より 13 dB 下（音声の検査は −13 dB のままで合格）。
