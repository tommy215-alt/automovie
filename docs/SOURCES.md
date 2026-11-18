# 使用の許可がある素材の仕入れ先

見つけたら足す。使う前に、**その素材のページ**でライセンスを確かめ、`assets.md` に URL を書く（サイト全体が OK でも、個別に条件が違うことがある）。

## 映像

| 仕入れ先 | 中身 | 権利 | 探し方 | 状態 |
|---|---|---|---|---|
| Wikimedia Commons（動画） | 米国の政府機関の映像（沿岸警備隊、軍、NASA、国立公園局、魚類野生生物局）、CC BY／CC0 の投稿 | ファイルごとに表示。Public domain・CC0・CC BY は可。**CC BY-SA は、こちらの動画も同じ条件で公開する義務があるので使わない。** NC・ND は不可 | `python tools/commons_search.py "検索語"` | 使用中（004） |
| NASA（images.nasa.gov、svs.gsfc.nasa.gov） | ロケット、宇宙、地球の映像 | 原則パブリックドメイン（NASA のロゴ、人物の肖像は別） | サイト内検索。API `https://images-api.nasa.gov/search?q=...&media_type=video`。Commons に転載ずみの NASA Johnson の 4K 映像（分類「4K NASA videos」「Videos from the NASA Johnson YouTube channel」）は `commons_search.py` で取れる | 使用中（007、Commons 経由） |
| Internet Archive の NASA のコレクション（archive.org、コレクション「nasa」） | NASA の昔の記録映画（アポロ計画など）、16 ミリフィルム | NASA 自身が登録したもの（作者「NASA/…」、コレクション「nasa」、登録者が nasa.gov）はパブリックドメイン。**同じ題の映画でも、第三者が登録したもの（PeriscopeFilm ＝ CC BY-NC-ND など）は使わない** | 検索 `https://archive.org/advancedsearch.php?q=…&output=json`、ファイルの一覧 `https://archive.org/metadata/識別子`（道具の見本は `videos/010/work/ia.py`）。Commons が回数制限（429）で取れないときの代わりになる | 使用中（010） |
| DVIDS（dvidshub.net） | 米軍の公式映像（帰還、救助、訓練、災害派遣） | 原則パブリックドメイン | ダウンロードに無料の登録が要る → **ユーザーに頼む必要あり**。Commons に転載ずみのものは上の方法で取れる | Commons 経由で使用予定（009＝米空軍。`commons_search.py "Military Working Dog"` `"Homecoming"` で、DVIDS の番号つきの映像が多く出る。右上に AFN などの放送局のロゴ、下に帯の文字が入るものがあるので、切り出しで外す。説明欄に「国防総省の支持・推奨を意味しない」と書く） |
| 米国の州・郡・市の警察・保安官の映像（ボディカメラなど） | 救助、動物を助けた警察官など。「警察官 感動」（11-16 の分析で中央値 88 万）に合う | Commons では「Public domain」（フロリダ州・カリフォルニア州の公文書は州の法律で著作権がない、という扱い）。連邦政府の著作物とは根拠が別で、転載元が第三者のまとめチャンネルのものもある。一般の人が写る | `commons_search.py "deputy rescue"` `"police officer saves"` | **使ってよい（11-17 ユーザーの決定）。ただし 1 本ごとに次を全部確かめ、`assets.md` に書く。1 つでも確かめられなければ使わない**：①どの州・郡・市の機関が撮ったか（公式の発表やその機関の公式チャンネルで裏を取る）、②その州の公文書に著作権がないとする根拠（Commons のライセンスのテンプレートと、その州の法律・判例の名前。確実なのはフロリダ州・カリフォルニア州。ほかの州は根拠がはっきり書かれているものだけ）、③Commons のファイルが公式の出どころから来ているか（第三者のまとめチャンネルが編集・音楽・字幕を足したものは、その部分に別の権利があるので使わない）、④写っている一般の人の扱い（名前を出さない、顔がはっきり分かる被害者・未成年・容疑者の場面は使わない、遺体・流血は使わない）。有罪が確定していない人を犯人と言わない（`docs/DESIGN.md` 3a） |
| NOAA、USGS、国立公園局（NPS） | 嵐、火山、野生動物、海の生き物 | 米国政府の著作物はパブリックドメイン（提供者が別の場合あり） | 各サイトの動画ライブラリ、Commons。USGS の火山の映像（作者「USGS Volcanoes」「Hawaiian Volcano Observatory」）は Commons に多く、`commons_search.py "Kilauea lava USGS"` で取れる。元のページ（usgs.gov/media）にも「Public Domain」と出る。魚類野生生物局（USFWS）の動物の映像も `"Fish and Wildlife Service 〜"` で多く出る | 使用中（005＝NOAA、008＝USGS） |
| Pexels、Pixabay | 動物、自然、街、人の映像 | 各サイトのライセンスで商用・改変可（素材だけの再配布は不可） | 自動での取得は API キーが要る → **ユーザーに頼む必要あり**。それまでは使わない | 未着手 |
| YouTube の「クリエイティブ・コモンズ」表示の動画 | 個人・団体の投稿 | CC BY（再利用可・クレジット必須）。ただし投稿者が本当の権利者かは別に確かめる | 取得の道具（yt-dlp）は PC にない。**入れるかどうかはユーザーが決める** | 未着手 |
| 日本の官公庁（海上保安庁、気象庁、JAXA など） | 救助、気象、宇宙 | 省庁ごとに利用規約が違う。「政府標準利用規約」「CC BY 互換」と書いてあるものだけ | 各サイト | 未着手 |

## 音楽

| 仕入れ先 | 権利 | 探し方 | 状態 |
|---|---|---|---|
| incompetech.com（Kevin MacLeod） | CC BY 4.0。クレジット必須 | 一覧 `https://incompetech.com/music/royalty-free/pieces.json` を楽器・曲調・テンポで絞る | 使用中（004） |
| Wikimedia Commons（音声） | ファイルごと。PD・CC0・CC BY のみ | Commons の検索で `filetype:audio` | 未使用 |

## 使えないもの（決まり）

他人が投稿した動画（上の CC BY 表示のものを除く）、スポーツの試合・中継、テレビ・映画・アニメ・ゲーム実況、権利がはっきりしないもの、市販の曲。
