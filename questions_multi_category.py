# questions_multi_category.py
# 複数カテゴリー（友達/恋愛/ゲーム/ビジネス）に対応した質問セット

# 5段階選択肢
CHOICES_5 = [
    ("A", "まったく当てはまらない"),
    ("B", "あまり当てはまらない"),
    ("C", "どちらとも言えない"),
    ("D", "やや当てはまる"),
    ("E", "とても当てはまる"),
]

# カテゴリーメタデータ
CATEGORY_META = {
    "friendship": {
        "name": "友達探し",
        "emoji": "👥",
        "description": "趣味や価値観が合う友達を見つける",
        "color": 0x3498db  # Blue
    },
    "dating": {
        "name": "恋愛マッチング",
        "emoji": "💕",
        "description": "真剣な出会いを求める方向け",
        "color": 0xe91e63  # Pink
    },
    "gaming": {
        "name": "ゲーム仲間",
        "emoji": "🎮",
        "description": "一緒にゲームを楽しむ仲間探し",
        "color": 0x9c27b0  # Purple
    },
    "business": {
        "name": "ビジネス・スキル",
        "emoji": "💼",
        "description": "協業やスキル交換のパートナー探し",
        "color": 0x607d8b  # Blue Grey
    }
}

# =========================================================
# 友達探し用質問（30問）
# =========================================================
QUESTIONS_FRIENDSHIP = [
    # コミュニケーションスタイル
    {"id": 101, "category": "communication_style", "text": "初対面の人とも比較的すぐに打ち解けられる。", "choices": CHOICES_5},
    {"id": 102, "category": "communication_style", "text": "雑談や会話を楽しむことが好きだ。", "choices": CHOICES_5},
    {"id": 103, "category": "communication_style", "text": "深い話や真面目な議論も好きだ。", "choices": CHOICES_5},
    {"id": 104, "category": "communication_style", "text": "テキストよりも通話やVCの方が好きだ。", "choices": CHOICES_5},
    {"id": 105, "category": "communication_style", "text": "頻繁に連絡を取り合う関係が好きだ。", "choices": CHOICES_5},

    # 趣味・活動
    {"id": 106, "category": "hobbies", "text": "インドア派だ。", "choices": CHOICES_5},
    {"id": 107, "category": "hobbies", "text": "新しいことに挑戦するのが好きだ。", "choices": CHOICES_5},
    {"id": 108, "category": "hobbies", "text": "創作活動（絵、音楽、文章など）に興味がある。", "choices": CHOICES_5},
    {"id": 109, "category": "hobbies", "text": "ゲームやアニメが好きだ。", "choices": CHOICES_5},
    {"id": 110, "category": "hobbies", "text": "体を動かすことが好きだ。", "choices": CHOICES_5},

    # 性格・価値観
    {"id": 111, "category": "personality", "text": "計画的に物事を進めるタイプだ。", "choices": CHOICES_5},
    {"id": 112, "category": "personality", "text": "几帳面で細かいことが気になる。", "choices": CHOICES_5},
    {"id": 113, "category": "personality", "text": "感情表現が豊かな方だ。", "choices": CHOICES_5},
    {"id": 114, "category": "personality", "text": "ユーモアやジョークが好きだ。", "choices": CHOICES_5},
    {"id": 115, "category": "personality", "text": "論理的に考えることが得意だ。", "choices": CHOICES_5},

    # 関係性の深さ
    {"id": 116, "category": "relationship_depth", "text": "少人数の深い関係を好む。", "choices": CHOICES_5},
    {"id": 117, "category": "relationship_depth", "text": "プライベートな悩みも共有したい。", "choices": CHOICES_5},
    {"id": 118, "category": "relationship_depth", "text": "一緒にいる時間を大切にしたい。", "choices": CHOICES_5},
    {"id": 119, "category": "relationship_depth", "text": "互いの生活に干渉しすぎない距離感が好きだ。", "choices": CHOICES_5},
    {"id": 120, "category": "relationship_depth", "text": "長期的な友人関係を築きたい。", "choices": CHOICES_5},

    # 生活リズム
    {"id": 121, "category": "lifestyle", "text": "夜型の生活リズムだ。", "choices": CHOICES_5},
    {"id": 122, "category": "lifestyle", "text": "平日も時間に余裕がある方だ。", "choices": CHOICES_5},
    {"id": 123, "category": "lifestyle", "text": "予定は柔軟に調整できる。", "choices": CHOICES_5},
    {"id": 124, "category": "lifestyle", "text": "定期的に会う約束をしたい。", "choices": CHOICES_5},
    {"id": 125, "category": "lifestyle", "text": "オンラインでの交流が中心で構わない。", "choices": CHOICES_5},

    # 価値観・将来
    {"id": 126, "category": "values", "text": "自己成長や学びを大切にしている。", "choices": CHOICES_5},
    {"id": 127, "category": "values", "text": "楽しさや刺激を重視する。", "choices": CHOICES_5},
    {"id": 128, "category": "values", "text": "安定や安心感を求める。", "choices": CHOICES_5},
    {"id": 129, "category": "values", "text": "多様な価値観を受け入れられる。", "choices": CHOICES_5},
    {"id": 130, "category": "values", "text": "友達との価値観の一致を重視する。", "choices": CHOICES_5},
]

# =========================================================
# 恋愛マッチング用質問（30問）
# =========================================================
QUESTIONS_DATING = [
    # 恋愛観
    {"id": 201, "category": "dating_style", "text": "真剣な交際を前提にした出会いを求めている。", "choices": CHOICES_5},
    {"id": 202, "category": "dating_style", "text": "結婚も視野に入れている。", "choices": CHOICES_5},
    {"id": 203, "category": "dating_style", "text": "じっくり時間をかけて関係を築きたい。", "choices": CHOICES_5},
    {"id": 204, "category": "dating_style", "text": "デートは計画的に楽しみたい。", "choices": CHOICES_5},
    {"id": 205, "category": "dating_style", "text": "ロマンチックな演出が好きだ。", "choices": CHOICES_5},

    # コミュニケーション
    {"id": 206, "category": "communication", "text": "毎日連絡を取り合いたい。", "choices": CHOICES_5},
    {"id": 207, "category": "communication", "text": "素直に気持ちを伝えることを大切にしている。", "choices": CHOICES_5},
    {"id": 208, "category": "communication", "text": "喧嘩してもしっかり話し合いたい。", "choices": CHOICES_5},
    {"id": 209, "category": "communication", "text": "相手の話をじっくり聞くタイプだ。", "choices": CHOICES_5},
    {"id": 210, "category": "communication", "text": "愛情表現は言葉でしっかり伝えたい。", "choices": CHOICES_5},

    # 性格・相性
    {"id": 211, "category": "personality", "text": "感情的になりやすい方だ。", "choices": CHOICES_5},
    {"id": 212, "category": "personality", "text": "嫉妬しやすい方だ。", "choices": CHOICES_5},
    {"id": 213, "category": "personality", "text": "相手に尽くすタイプだ。", "choices": CHOICES_5},
    {"id": 214, "category": "personality", "text": "リードしてほしい/リードしたい。", "choices": CHOICES_5},
    {"id": 215, "category": "personality", "text": "対等な関係を重視する。", "choices": CHOICES_5},

    # デート・過ごし方
    {"id": 216, "category": "activities", "text": "家でまったり過ごすのが好きだ。", "choices": CHOICES_5},
    {"id": 217, "category": "activities", "text": "外出してアクティブに過ごしたい。", "choices": CHOICES_5},
    {"id": 218, "category": "activities", "text": "趣味を一緒に楽しみたい。", "choices": CHOICES_5},
    {"id": 219, "category": "activities", "text": "お互いの時間も大切にしたい。", "choices": CHOICES_5},
    {"id": 220, "category": "activities", "text": "できるだけ一緒にいたい。", "choices": CHOICES_5},

    # 価値観・将来
    {"id": 221, "category": "values", "text": "金銭感覚が合うことを重視する。", "choices": CHOICES_5},
    {"id": 222, "category": "values", "text": "家族を大切にすることを重視する。", "choices": CHOICES_5},
    {"id": 223, "category": "values", "text": "お互いのキャリアを尊重し合いたい。", "choices": CHOICES_5},
    {"id": 224, "category": "values", "text": "将来の目標や夢を共有したい。", "choices": CHOICES_5},
    {"id": 225, "category": "values", "text": "宗教や文化的背景の違いは気にしない。", "choices": CHOICES_5},

    # ライフスタイル
    {"id": 226, "category": "lifestyle", "text": "健康的な生活を心がけている。", "choices": CHOICES_5},
    {"id": 227, "category": "lifestyle", "text": "お酒を飲む機会が多い。", "choices": CHOICES_5},
    {"id": 228, "category": "lifestyle", "text": "タバコは吸わない/気にしない。", "choices": CHOICES_5},
    {"id": 229, "category": "lifestyle", "text": "遠距離恋愛も可能だ。", "choices": CHOICES_5},
    {"id": 230, "category": "lifestyle", "text": "ペットを飼いたい/飼っている。", "choices": CHOICES_5},
]

# =========================================================
# ゲーム仲間用質問（30問）- 既存のQUESTIONSを活用
# =========================================================
QUESTIONS_GAMING = [
    # game_style（ゲームスタイル）
    {"id": 1, "category": "game_style", "text": "勝敗には強くこだわる方だ。", "choices": CHOICES_5},
    {"id": 2, "category": "game_style", "text": "負けた時もすぐ切り替えられる。", "choices": CHOICES_5},
    {"id": 3, "category": "game_style", "text": "攻略情報（Wiki/動画）をよく調べる。", "choices": CHOICES_5},
    {"id": 4, "category": "game_style", "text": "効率重視でプレイすることが多い。", "choices": CHOICES_5},
    {"id": 5, "category": "game_style", "text": "ひとつのゲームを長く続けるタイプだ。", "choices": CHOICES_5},

    # communication（コミュニケーション）
    {"id": 6, "category": "communication", "text": "VC（ボイスチャット）で話しながら遊ぶのが好きだ。", "choices": CHOICES_5},
    {"id": 7, "category": "communication", "text": "連携が必要な場面では自分から指示や提案を出す。", "choices": CHOICES_5},
    {"id": 8, "category": "communication", "text": "無言で一緒に遊んでも気にならない。", "choices": CHOICES_5},
    {"id": 9, "category": "communication", "text": "初対面の人とも比較的すぐに打ち解けられる。", "choices": CHOICES_5},
    {"id": 10, "category": "communication", "text": "ゲーム中の雑談やノリの共有は大事だと思う。", "choices": CHOICES_5},

    # play_time（プレイ時間・生活リズム）
    {"id": 11, "category": "play_time", "text": "平日でも定期的にゲームをする。", "choices": CHOICES_5},
    {"id": 12, "category": "play_time", "text": "深夜帯にプレイすることが多い。", "choices": CHOICES_5},
    {"id": 13, "category": "play_time", "text": "予定があっても、ついゲームを優先しがちだ。", "choices": CHOICES_5},
    {"id": 14, "category": "play_time", "text": "生活リズムは比較的安定している。", "choices": CHOICES_5},
    {"id": 15, "category": "play_time", "text": "ゲーム以外の趣味や時間も大切にしている。", "choices": CHOICES_5},

    # distance（距離感・人間関係）
    {"id": 16, "category": "distance", "text": "毎日こまめに連絡を取りたいタイプだ。", "choices": CHOICES_5},
    {"id": 17, "category": "distance", "text": "束縛や干渉が強い関係は苦手だ。", "choices": CHOICES_5},
    {"id": 18, "category": "distance", "text": "一人の時間は多めに必要だ。", "choices": CHOICES_5},
    {"id": 19, "category": "distance", "text": "トラブルや誤解があれば話し合って解決したい。", "choices": CHOICES_5},
    {"id": 20, "category": "distance", "text": "フレンド関係でも、プライベートの境界は分けたい。", "choices": CHOICES_5},

    # money（お金・課金感覚）
    {"id": 21, "category": "money", "text": "課金（スキン/バトルパス等）に抵抗は少ない。", "choices": CHOICES_5},
    {"id": 22, "category": "money", "text": "ゲームにお金をかけるのは"体験への投資"だと思う。", "choices": CHOICES_5},
    {"id": 23, "category": "money", "text": "趣味の出費は計画的に管理している。", "choices": CHOICES_5},
    {"id": 24, "category": "money", "text": "ガチャや限定品に熱くなりやすい。", "choices": CHOICES_5},
    {"id": 25, "category": "money", "text": "コスパ（費用対効果）を重視する。", "choices": CHOICES_5},

    # future（将来観・価値観）
    {"id": 26, "category": "future", "text": "ゲームは人生の中でかなり大きな存在だ。", "choices": CHOICES_5},
    {"id": 27, "category": "future", "text": "新しいことに挑戦するのが好きだ。", "choices": CHOICES_5},
    {"id": 28, "category": "future", "text": "安定よりも刺激や変化を求めることが多い。", "choices": CHOICES_5},
    {"id": 29, "category": "future", "text": "将来の目標や計画を立てる方だ。", "choices": CHOICES_5},
    {"id": 30, "category": "future", "text": "相手とは早めに価値観をすり合わせたい。", "choices": CHOICES_5},
]

# =========================================================
# ビジネス・スキル用質問（30問）
# =========================================================
QUESTIONS_BUSINESS = [
    # 働き方・スタイル
    {"id": 301, "category": "work_style", "text": "リモートワークが主体だ。", "choices": CHOICES_5},
    {"id": 302, "category": "work_style", "text": "フリーランスや個人事業主だ。", "choices": CHOICES_5},
    {"id": 303, "category": "work_style", "text": "チームでの協業が好きだ。", "choices": CHOICES_5},
    {"id": 304, "category": "work_style", "text": "締め切りを守ることを重視する。", "choices": CHOICES_5},
    {"id": 305, "category": "work_style", "text": "品質にこだわる方だ。", "choices": CHOICES_5},

    # スキル・専門性
    {"id": 306, "category": "skills", "text": "技術系（エンジニア、デザイン等）のスキルがある。", "choices": CHOICES_5},
    {"id": 307, "category": "skills", "text": "マーケティングやビジネス戦略が得意だ。", "choices": CHOICES_5},
    {"id": 308, "category": "skills", "text": "クリエイティブな仕事をしている。", "choices": CHOICES_5},
    {"id": 309, "category": "skills", "text": "新しいスキルを学ぶことに意欲的だ。", "choices": CHOICES_5},
    {"id": 310, "category": "skills", "text": "専門分野を深く追求したい。", "choices": CHOICES_5},

    # コミュニケーション
    {"id": 311, "category": "communication", "text": "定期的なミーティングを好む。", "choices": CHOICES_5},
    {"id": 312, "category": "communication", "text": "テキストコミュニケーションが得意だ。", "choices": CHOICES_5},
    {"id": 313, "category": "communication", "text": "フィードバックを率直に伝え合いたい。", "choices": CHOICES_5},
    {"id": 314, "category": "communication", "text": "レスポンスは早い方だ。", "choices": CHOICES_5},
    {"id": 315, "category": "communication", "text": "ドキュメント化を重視する。", "choices": CHOICES_5},

    # プロジェクト志向
    {"id": 316, "category": "project_goals", "text": "短期プロジェクトが好きだ。", "choices": CHOICES_5},
    {"id": 317, "category": "project_goals", "text": "長期的な関係を築きたい。", "choices": CHOICES_5},
    {"id": 318, "category": "project_goals", "text": "収益化を目指したい。", "choices": CHOICES_5},
    {"id": 319, "category": "project_goals", "text": "学びや経験を重視する。", "choices": CHOICES_5},
    {"id": 320, "category": "project_goals", "text": "社会的インパクトを重視する。", "choices": CHOICES_5},

    # 価値観・マインドセット
    {"id": 321, "category": "mindset", "text": "失敗を恐れずチャレンジしたい。", "choices": CHOICES_5},
    {"id": 322, "category": "mindset", "text": "データや根拠を重視する。", "choices": CHOICES_5},
    {"id": 323, "category": "mindset", "text": "直感や創造性も大切にする。", "choices": CHOICES_5},
    {"id": 324, "category": "mindset", "text": "効率や生産性を追求する。", "choices": CHOICES_5},
    {"id": 325, "category": "mindset", "text": "ワークライフバランスを大切にする。", "choices": CHOICES_5},

    # 協業スタイル
    {"id": 326, "category": "collaboration", "text": "役割分担を明確にしたい。", "choices": CHOICES_5},
    {"id": 327, "category": "collaboration", "text": "柔軟に助け合える関係が良い。", "choices": CHOICES_5},
    {"id": 328, "category": "collaboration", "text": "リーダーシップを取ることが多い。", "choices": CHOICES_5},
    {"id": 329, "category": "collaboration", "text": "対等なパートナーシップを好む。", "choices": CHOICES_5},
    {"id": 330, "category": "collaboration", "text": "契約や条件は明確にしたい。", "choices": CHOICES_5},
]

# =========================================================
# カテゴリー別質問マッピング
# =========================================================
CATEGORY_QUESTIONS = {
    "friendship": QUESTIONS_FRIENDSHIP,
    "dating": QUESTIONS_DATING,
    "gaming": QUESTIONS_GAMING,
    "business": QUESTIONS_BUSINESS,
}

# 全質問のID重複チェック用
ALL_QUESTION_IDS = set()
for questions in CATEGORY_QUESTIONS.values():
    for q in questions:
        qid = q["id"]
        if qid in ALL_QUESTION_IDS:
            raise ValueError(f"Duplicate question ID: {qid}")
        ALL_QUESTION_IDS.add(qid)
