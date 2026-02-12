"""
Turso (LibSQL) 対応のマルチカテゴリーDB層
"""
import os
import json
import random
import threading
from typing import List, Tuple, Optional, Dict

import libsql
from dotenv import load_dotenv

# スクリプトのディレクトリを基準に.envを読み込む
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, "env.example")
load_dotenv(_env_path, override=True)

# 親ディレクトリの.envもフォールバック
_parent_env = os.path.join(os.path.dirname(_script_dir), "env.example")
if os.path.exists(_parent_env):
    load_dotenv(_parent_env, override=False)

_raw_db = os.environ.get("DB_PATH", "app_multi.db")
DB_PATH = _raw_db if os.path.isabs(_raw_db) else os.path.join(_script_dir, os.path.basename(_raw_db))
LIBSQL_URL = os.environ.get("LIBSQL_URL", "").strip()
LIBSQL_AUTH_TOKEN = os.environ.get("LIBSQL_AUTH_TOKEN", "").strip()

# グローバル接続（Turso同期用）
_conn: Optional[libsql.Connection] = None
_lock = threading.Lock()


def _get_conn() -> libsql.Connection:
    """Turso接続を取得（シングルトン）"""
    global _conn
    if _conn is None:
        with _lock:
            if _conn is None:
                if not LIBSQL_URL or not LIBSQL_AUTH_TOKEN:
                    raise RuntimeError(
                        "LIBSQL_URL と LIBSQL_AUTH_TOKEN を env.example に設定してください。"
                    )
                # WAL関連ファイルが残っているとエラーになる環境があるため削除を試行
                for suf in ("-wal", "-shm"):
                    p = DB_PATH + suf
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except OSError:
                            pass
                _conn = libsql.connect(
                    DB_PATH,
                    sync_url=LIBSQL_URL,
                    auth_token=LIBSQL_AUTH_TOKEN,
                )
                # ★WALが相性悪い環境向け：最初にjournal_modeを変更
                _conn.execute("PRAGMA journal_mode=DELETE;")
                _conn.execute("PRAGMA synchronous=NORMAL;")
                _conn.commit()  # PRAGMAを反映
    return _conn


def sync_db() -> None:
    """ローカルDBの変更をTursoへ同期（アップロード）"""
    conn = _get_conn()
    if hasattr(conn, "sync"):
        try:
            conn.sync()
        except Exception:
            pass  # 同期失敗時は無視（オフライン等）


def init_db() -> None:
    """複数カテゴリー対応のデータベース初期化"""
    conn = _get_conn()
    with _lock:
        # ユーザーテーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            discord_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reputation_score REAL DEFAULT 5.0,
            is_active INTEGER DEFAULT 1
        )
        """)

        # カテゴリー別プロフィール
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            bio TEXT,
            interests TEXT,
            personality_traits TEXT,
            active_status INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, category)
        )
        """)

        # 質問状態（カテゴリー別）
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            idx INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, category)
        )
        """)

        # 回答データ（カテゴリー別）
        conn.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, category, question_id)
        )
        """)

        # 質問順序（カテゴリー別）
        conn.execute("""
        CREATE TABLE IF NOT EXISTS question_order (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            order_json TEXT NOT NULL,
            PRIMARY KEY (user_id, category)
        )
        """)

        # マッチング履歴
        conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            match_score REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users(user_id),
            FOREIGN KEY (user2_id) REFERENCES users(user_id)
        )
        """)

        # 会話履歴
        conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            channel_id TEXT,
            messages TEXT,
            ai_insights TEXT,
            quality_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches(id)
        )
        """)

        # メッセージID管理（カテゴリー別）
        conn.execute("""
        CREATE TABLE IF NOT EXISTS user_msg (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, category)
        )
        """)

        conn.commit()
        sync_db()


# =========================================================
# ユーザー管理
# =========================================================
def get_or_create_user(discord_id: str, username: str) -> int:
    """ユーザーを取得または作成"""
    conn = _get_conn()
    with _lock:
        row = conn.execute("SELECT user_id FROM users WHERE discord_id=?", (discord_id,)).fetchone()

        if row:
            return int(row[0])

        conn.execute(
            "INSERT INTO users(discord_id, username) VALUES(?, ?)",
            (discord_id, username)
        )
        conn.commit()
        row = conn.execute("SELECT last_insert_rowid()").fetchone()
        sync_db()
        return int(row[0])


def get_user_by_discord_id(discord_id: str) -> Optional[int]:
    """Discord IDからユーザーIDを取得"""
    conn = _get_conn()
    with _lock:
        row = conn.execute("SELECT user_id FROM users WHERE discord_id=?", (discord_id,)).fetchone()
        return int(row[0]) if row else None


# =========================================================
# プロフィール管理
# =========================================================
def create_or_update_profile(
    user_id: int,
    category: str,
    bio: str = "",
    interests: List[str] = None,
    personality_traits: Dict = None
) -> None:
    """プロフィールを作成または更新"""
    conn = _get_conn()
    with _lock:
        interests_json = json.dumps(interests or [])
        traits_json = json.dumps(personality_traits or {})

        conn.execute("""
        INSERT INTO user_profiles(user_id, category, bio, interests, personality_traits)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(user_id, category) DO UPDATE SET
            bio=excluded.bio,
            interests=excluded.interests,
            personality_traits=excluded.personality_traits,
            updated_at=CURRENT_TIMESTAMP
        """, (user_id, category, bio, interests_json, traits_json))

        conn.commit()
        sync_db()


def get_profile(user_id: int, category: str) -> Optional[Dict]:
    """プロフィールを取得"""
    conn = _get_conn()
    with _lock:
        row = conn.execute("""
        SELECT bio, interests, personality_traits, active_status
        FROM user_profiles
        WHERE user_id=? AND category=?
        """, (user_id, category)).fetchone()
        if not row:
            return None

        return {
            "bio": row[0],
            "interests": json.loads(row[1]) if row[1] else [],
            "personality_traits": json.loads(row[2]) if row[2] else {},
            "active_status": bool(row[3])
        }


def get_user_categories(user_id: int) -> List[str]:
    """ユーザーが登録しているカテゴリー一覧を取得"""
    conn = _get_conn()
    with _lock:
        rows = conn.execute("""
        SELECT category FROM user_profiles
        WHERE user_id=? AND active_status=1
        """, (user_id,)).fetchall()
        return [row[0] for row in rows]


# =========================================================
# 質問状態管理（カテゴリー別）
# =========================================================
def get_state(user_id: int, category: str) -> int:
    """カテゴリー別の質問進捗を取得"""
    conn = _get_conn()
    with _lock:
        row = conn.execute(
            "SELECT idx FROM user_state WHERE user_id=? AND category=?",
            (user_id, category)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO user_state(user_id, category, idx) VALUES(?, ?, 0)",
                (user_id, category)
            )
            conn.commit()
            sync_db()
            return 0
        return int(row[0])


def set_state(user_id: int, category: str, idx: int) -> None:
    """カテゴリー別の質問進捗を更新"""
    conn = _get_conn()
    with _lock:
        conn.execute("""
        INSERT INTO user_state(user_id, category, idx) VALUES(?, ?, ?)
        ON CONFLICT(user_id, category) DO UPDATE SET idx=excluded.idx
        """, (user_id, category, idx))
        conn.commit()
        sync_db()


# =========================================================
# 回答管理（カテゴリー別）
# =========================================================
def save_answer(user_id: int, category: str, question_id: int, answer: str) -> None:
    """回答を保存"""
    conn = _get_conn()
    with _lock:
        conn.execute("""
        INSERT INTO answers(user_id, category, question_id, answer)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(user_id, category, question_id)
        DO UPDATE SET answer=excluded.answer, answered_at=CURRENT_TIMESTAMP
        """, (user_id, category, question_id, answer))
        conn.commit()
        sync_db()


def load_answers(user_id: int, category: str) -> List[Tuple[int, str]]:
    """カテゴリー別の回答を読み込み"""
    conn = _get_conn()
    with _lock:
        rows = conn.execute("""
        SELECT question_id, answer
        FROM answers
        WHERE user_id=? AND category=?
        ORDER BY question_id
        """, (user_id, category)).fetchall()
        return [(int(qid), ans) for (qid, ans) in rows]


def reset_user_category(user_id: int, category: str) -> None:
    """特定カテゴリーのデータをリセット"""
    conn = _get_conn()
    with _lock:
        conn.execute("DELETE FROM answers WHERE user_id=? AND category=?", (user_id, category))
        conn.execute("DELETE FROM user_state WHERE user_id=? AND category=?", (user_id, category))
        conn.execute("DELETE FROM question_order WHERE user_id=? AND category=?", (user_id, category))
        conn.execute("DELETE FROM user_msg WHERE user_id=? AND category=?", (user_id, category))
        conn.commit()


# =========================================================
# 質問順序管理（カテゴリー別）
# =========================================================
def get_or_create_order(user_id: int, category: str, question_ids: List[int]) -> List[int]:
    """質問順序を取得または作成"""
    conn = _get_conn()
    with _lock:
        row = conn.execute(
            "SELECT order_json FROM question_order WHERE user_id=? AND category=?",
            (user_id, category)
        ).fetchone()
        if row:
            return json.loads(row[0])

        ids = question_ids[:]
        random.shuffle(ids)
        conn.execute(
            "INSERT OR REPLACE INTO question_order(user_id, category, order_json) VALUES(?, ?, ?)",
            (user_id, category, json.dumps(ids))
        )
        conn.commit()
        return ids


def reset_order(user_id: int, category: str) -> None:
    """質問順序をリセット"""
    conn = _get_conn()
    with _lock:
        conn.execute(
            "DELETE FROM question_order WHERE user_id=? AND category=?",
            (user_id, category)
        )
        conn.commit()


# =========================================================
# メッセージID管理（カテゴリー別）
# =========================================================
def get_message_id(user_id: int, category: str) -> Optional[int]:
    """メッセージIDを取得"""
    conn = _get_conn()
    with _lock:
        row = conn.execute(
            "SELECT message_id FROM user_msg WHERE user_id=? AND category=?",
            (user_id, category)
        ).fetchone()
        return int(row[0]) if row else None


def set_message_id(user_id: int, category: str, message_id: int) -> None:
    """メッセージIDを保存"""
    conn = _get_conn()
    with _lock:
        conn.execute("""
        INSERT INTO user_msg(user_id, category, message_id) VALUES(?, ?, ?)
        ON CONFLICT(user_id, category) DO UPDATE SET message_id=excluded.message_id
        """, (user_id, category, message_id))
        conn.commit()


def reset_message_id(user_id: int, category: str) -> None:
    """メッセージIDをリセット"""
    conn = _get_conn()
    with _lock:
        conn.execute(
            "DELETE FROM user_msg WHERE user_id=? AND category=?",
            (user_id, category)
        )
        conn.commit()


# =========================================================
# マッチング管理
# =========================================================
def create_match(
    user1_id: int,
    user2_id: int,
    category: str,
    match_score: float
) -> int:
    """マッチを作成"""
    conn = _get_conn()
    with _lock:
        conn.execute("""
        INSERT INTO matches(user1_id, user2_id, category, match_score, status)
        VALUES(?, ?, ?, ?, 'pending')
        """, (user1_id, user2_id, category, match_score))
        conn.commit()
        sync_db()
        row = conn.execute("SELECT last_insert_rowid()").fetchone()
        return int(row[0])


def get_user_matches(user_id: int, category: str, status: str = None) -> List[Dict]:
    """ユーザーのマッチ履歴を取得"""
    conn = _get_conn()
    with _lock:
        query = """
        SELECT id, user1_id, user2_id, match_score, status, created_at
        FROM matches
        WHERE category=? AND (user1_id=? OR user2_id=?)
        """
        params = [category, user_id, user_id]

        if status:
            query += " AND status=?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        rows = conn.execute(query, params).fetchall()

        matches = []
        for row in rows:
            matches.append({
                "id": row[0],
                "user1_id": row[1],
                "user2_id": row[2],
                "match_score": row[3],
                "status": row[4],
                "created_at": row[5]
            })

        return matches


def update_match_status(match_id: int, status: str) -> None:
    """マッチのステータスを更新"""
    conn = _get_conn()
    with _lock:
        conn.execute("""
        UPDATE matches
        SET status=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (status, match_id))
        conn.commit()


# =========================================================
# 統計情報
# =========================================================
def count_total_users() -> int:
    """総ユーザー数"""
    conn = _get_conn()
    with _lock:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0])


def count_completed_users(category: str, total_questions: int) -> int:
    """カテゴリー別の診断完了ユーザー数"""
    conn = _get_conn()
    with _lock:
        row = conn.execute(
            "SELECT COUNT(*) FROM user_state WHERE category=? AND idx >= ?",
            (category, total_questions)
        ).fetchone()
        return int(row[0])


def count_matches_by_category(category: str) -> int:
    """カテゴリー別のマッチ数"""
    conn = _get_conn()
    with _lock:
        row = conn.execute("SELECT COUNT(*) FROM matches WHERE category=?", (category,)).fetchone()
        return int(row[0])


def get_category_stats() -> Dict[str, Dict]:
    """全カテゴリーの統計情報"""
    conn = _get_conn()
    with _lock:
        stats = {}
        categories = ["friendship", "dating", "gaming", "business"]

        for cat in categories:
            row = conn.execute("""
            SELECT
                COUNT(DISTINCT user_id) as user_count,
                COUNT(*) as answer_count
            FROM answers
            WHERE category=?
            """, (cat,)).fetchone()
            stats[cat] = {
                "users": row[0] if row else 0,
                "answers": row[1] if row else 0
            }

        return stats
