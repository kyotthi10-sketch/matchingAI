import os
import re
import asyncio
from typing import List, Optional

from dotenv import load_dotenv

# スクリプトのディレクトリを基準に.envを読み込む（最優先で実行）
_script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_script_dir, ".env"), override=True)
load_dotenv(os.path.join(os.path.dirname(_script_dir), ".env"), override=False)

import discord
from discord import app_commands
from discord.ext import commands

from questions_multi_category import (
    CATEGORY_META,
    CATEGORY_QUESTIONS,
    CHOICES_5
)
from db_multi import (
    init_db,
    get_or_create_user,
    get_user_by_discord_id,
    get_profile,
    create_or_update_profile,
    get_user_categories,
    get_state,
    set_state,
    save_answer,
    load_answers,
    get_or_create_order,
    get_message_id,
    set_message_id,
    reset_user_category,
    create_match,
    get_user_matches,
    update_match_status,
    count_total_users,
    count_completed_users,
    get_category_stats,
)
from ai_matching_gemini import (
    AIMatchingEngine,
    build_category_profile,
    STAR_MAP,
)

# =========================================================
# 環境変数
# =========================================================
TOKEN = os.environ["DISCORD_TOKEN"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GUILD_ID = int(os.environ.get("GUILD_ID", "0"))
AUTO_CLOSE_SECONDS = int(os.environ.get("AUTO_CLOSE_SECONDS", "300"))
ADMIN_ROLE_ID = int(os.environ.get("ADMIN_ROLE_ID", "0"))
BOTADMIN_ROLE_ID = int(os.environ.get("BOTADMIN_ROLE_ID", "0"))
ADMIN_CHANNEL_ID = int(os.environ.get("ADMIN_CHANNEL_ID", "0"))
WELCOME_CHANNEL_ID = int(os.environ.get("WELCOME_CHANNEL_ID", "0"))

# =========================================================
# Bot初期化
# =========================================================
intents = discord.Intents.default()
intents.members = False  # on_member_join 用
intents.message_content = False
bot = commands.Bot(command_prefix="!", intents=intents)


# AIマッチングエンジン
matching_engine = AIMatchingEngine()

# =========================================================
# ユーティリティ
# =========================================================
def safe_channel_name(name: str) -> str:
    """Discordチャンネル名は英小文字/数字/ハイフンが安全"""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    return name or "user"


def is_user_room(channel: discord.abc.GuildChannel, user_id: int) -> bool:
    """topic でユーザールームか判定 (topic: "user:{id} ...")"""
    if not isinstance(channel, discord.TextChannel):
        return False
    return (channel.topic or "").startswith(f"user:{user_id}")


def compatibility_percent(picks_a: dict, picks_b: dict, categories: List[str]) -> int:
    """2ユーザーの回答一致率を％で返す"""
    usable = [c for c in categories if c in picks_a and c in picks_b]
    if not usable:
        return 0
    same = sum(1 for c in usable if picks_a[c] == picks_b[c])
    return int(round(same / len(usable) * 100))


def has_role_id(member: discord.Member, role_id: int) -> bool:
    if role_id <= 0:
        return False
    return any(r.id == role_id for r in member.roles)


def stars(letter: str) -> str:
    n = STAR_MAP.get(letter, 3)
    return "★" * n + "☆" * (5 - n)


def progress_bar(current: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return ""
    filled = int(round((current / total) * width))
    filled = max(0, min(width, filled))
    return "■" * filled + "□" * (width - filled)


def q_by_id(questions: List[dict], qid: int) -> dict:
    for q in questions:
        if q["id"] == qid:
            return q
    raise KeyError(f"question id not found: {qid}")


# =========================================================
# カテゴリー選択View
# =========================================================
class CategorySelectView(discord.ui.View):
    """カテゴリー選択UI"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.category = None
    
    @discord.ui.button(label="👥 友達探し", style=discord.ButtonStyle.primary, custom_id="cat:friendship")
    async def friendship_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._select_category(interaction, "friendship")
    
    @discord.ui.button(label="💕 恋愛マッチング", style=discord.ButtonStyle.danger, custom_id="cat:dating")
    async def dating_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._select_category(interaction, "dating")
    
    @discord.ui.button(label="🎮 ゲーム仲間", style=discord.ButtonStyle.success, custom_id="cat:gaming")
    async def gaming_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._select_category(interaction, "gaming")
    
    @discord.ui.button(label="💼 ビジネス", style=discord.ButtonStyle.secondary, custom_id="cat:business")
    async def business_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._select_category(interaction, "business")
    
    async def _select_category(self, interaction: discord.Interaction, category: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("これはあなたの選択ではありません。", ephemeral=True)
            return
        
        self.category = category
        self.stop()
        
        meta = CATEGORY_META[category]
        await interaction.response.send_message(
            f"{meta['emoji']} **{meta['name']}** を選択しました！\n診断を開始します...",
            ephemeral=True
        )


# =========================================================
# 専用ルーム作成・パネル
# =========================================================
async def create_or_open_room(interaction: discord.Interaction):
    """専用診断ルームを作成し、カテゴリー選択から診断を開始"""
    guild = interaction.guild
    if guild is None:
        return
    member = interaction.user
    if not isinstance(member, discord.Member):
        return

    discord_id = member.id
    safe_name = safe_channel_name(member.display_name)
    channel_name = f"match-{safe_name}-{discord_id % 10000}"

    # 既存ルーム再利用
    for ch in guild.text_channels:
        if is_user_room(ch, discord_id):
            await interaction.response.send_message(f"既にあります：{ch.mention}", ephemeral=True)
            return

    if guild.me is None:
        await interaction.response.send_message("Bot情報の取得に失敗しました。", ephemeral=True)
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }

    ch = await guild.create_text_channel(
        channel_name,
        topic=f"user:{discord_id} name:{member.display_name}",
        overwrites=overwrites
    )

    await interaction.response.send_message(f"専用ルームを作成しました：{ch.mention}", ephemeral=True)
    await ch.send("📝 このルームは診断専用です。カテゴリーを選んで開始してください。")

    user_id = await asyncio.to_thread(
        get_or_create_user, str(discord_id), member.name
    )

    embed = discord.Embed(
        title="🎯 AIマッチングサービス",
        description="どのカテゴリーで診断を始めますか？",
        color=discord.Color.blue()
    )
    for cat_id, meta in CATEGORY_META.items():
        embed.add_field(name=f"{meta['emoji']} {meta['name']}", value=meta['description'], inline=False)

    view = CategorySelectView(discord_id)
    await ch.send(embed=embed, view=view)
    await view.wait()

    if view.category:
        questions = CATEGORY_QUESTIONS[view.category]
        order = await asyncio.to_thread(
            get_or_create_order, user_id, view.category, [q["id"] for q in questions]
        )
        await update_question_message(ch, user_id, view.category, 0, order, questions)


class StartRoomView(discord.ui.View):
    """診断開始ボタン（永続用）"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="診断を始める", style=discord.ButtonStyle.success, custom_id="start_room_button")
    async def start_room_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("サーバー内で押してください。", ephemeral=True)
            return
        await create_or_open_room(interaction)


async def post_panel(channel: discord.TextChannel):
    """診断開始ボタンを設置"""
    embed = discord.Embed(
        title="🎯 AIマッチング診断スタート",
        description="下のボタンを押すと、あなた専用の診断ルームが作成されます。",
    )
    await channel.send(embed=embed, view=StartRoomView())


# =========================================================
# 質問回答View
# =========================================================
class AnswerButtonsView(discord.ui.View):
    """回答ボタンUI（A〜E）"""
    
    def __init__(self, user_id: int, category: str, idx: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.category = category
        self.idx = idx
        
        # A〜Eボタンを追加
        for key, label in CHOICES_5:
            button = discord.ui.Button(
                label=f"{key}: {stars(key)}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"ans:{user_id}:{category}:{idx}:{key}"
            )
            button.callback = self.make_answer_callback(key)
            self.add_item(button)
    
    def make_answer_callback(self, key: str):
        async def callback(interaction: discord.Interaction):
            await handle_answer(interaction, self.user_id, self.category, self.idx, key)
        return callback


async def handle_answer(
    interaction: discord.Interaction,
    user_id: int,
    category: str,
    idx: int,
    key: str
):
    """回答処理"""
    # 権限チェック
    if interaction.user.id != user_id:
        await interaction.response.send_message("これはあなたの診断ではありません。", ephemeral=True)
        return
    
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)
    
    try:
        # 質問取得
        questions = CATEGORY_QUESTIONS[category]
        order = await asyncio.to_thread(
            get_or_create_order,
            user_id,
            category,
            [q["id"] for q in questions]
        )
        
        # 現在の進捗を確認
        cur_idx = await asyncio.to_thread(get_state, user_id, category)
        if isinstance(cur_idx, int) and 0 <= cur_idx < len(order):
            idx = cur_idx
        
        # 回答を保存
        q = q_by_id(questions, order[idx])
        await asyncio.to_thread(save_answer, user_id, category, q["id"], key)
        
        next_idx = idx + 1
        await asyncio.to_thread(set_state, user_id, category, next_idx)
        
        # 完了チェック
        if next_idx >= len(order):
            await handle_completion(interaction, user_id, category, questions)
        else:
            # 次の質問へ
            await update_question_message(interaction.channel, user_id, category, next_idx, order, questions)
    
    except Exception as e:
        await interaction.followup.send(f"⚠️ エラー：{type(e).__name__}", ephemeral=True)
        raise


async def handle_completion(
    interaction: discord.Interaction,
    user_id: int,
    category: str,
    questions: List[dict]
):
    """診断完了処理"""
    meta = CATEGORY_META[category]
    
    # 回答をロード
    answers = await asyncio.to_thread(load_answers, user_id, category)
    
    # AI分析
    question_data = {q["id"]: q["text"] for q in questions}
    profile_analysis = await matching_engine.analyze_profile(
        category,
        answers,
        question_data
    )
    
    # プロフィールを保存
    await asyncio.to_thread(
        create_or_update_profile,
        user_id,
        category,
        bio=profile_analysis.get("personality_summary", ""),
        interests=profile_analysis.get("match_keywords", []),
        personality_traits=profile_analysis
    )
    
    # 結果表示
    embed = discord.Embed(
        title=f"{meta['emoji']} 診断完了！",
        description=f"**{meta['name']}**の診断が完了しました。",
        color=meta['color']
    )
    
    embed.add_field(
        name="📝 性格分析",
        value=profile_analysis.get("personality_summary", "分析中..."),
        inline=False
    )
    
    traits = profile_analysis.get("key_traits", [])
    if traits:
        embed.add_field(
            name="✨ 主な特徴",
            value="• " + "\n• ".join(traits[:5]),
            inline=False
        )
    
    embed.add_field(
        name="🎯 次のステップ",
        value=f"`/match {category}` でマッチング相手を探す\n`/profile {category}` でプロフィールを確認",
        inline=False
    )
    
    mid = await asyncio.to_thread(get_message_id, user_id, category)
    if mid:
        try:
            msg = await interaction.channel.fetch_message(mid)
            await msg.edit(embed=embed, view=None)
        except Exception:
            await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)


async def update_question_message(
    channel: discord.TextChannel,
    user_id: int,
    category: str,
    idx: int,
    order: List[int],
    questions: List[dict]
):
    """質問メッセージを更新"""
    q = q_by_id(questions, order[idx])
    meta = CATEGORY_META[category]
    
    embed = discord.Embed(
        title=f"{meta['emoji']} {meta['name']} 診断",
        color=meta['color']
    )
    
    embed.add_field(
        name="📊 進捗",
        value=f"{progress_bar(idx + 1, len(order), 12)}  {idx + 1} / {len(order)}",
        inline=False
    )
    
    embed.add_field(
        name="❓ 質問",
        value=f"Q{idx + 1}. {q['text']}",
        inline=False
    )
    
    embed.set_footer(text="★が多いほど強い傾向です")
    
    view = AnswerButtonsView(user_id, category, idx)
    
    mid = await asyncio.to_thread(get_message_id, user_id, category)
    if mid:
        try:
            msg = await channel.fetch_message(mid)
            await msg.edit(embed=embed, view=view)
            return
        except Exception:
            pass
    
    # 新規メッセージ
    msg = await channel.send(embed=embed, view=view)
    await asyncio.to_thread(set_message_id, user_id, category, msg.id)


# =========================================================
# コマンド
# =========================================================
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    init_db()
    try:
        bot.add_view(StartRoomView())
    except Exception as e:
        print("add_view failed:", repr(e))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_member_join(member: discord.Member):
    """新規メンバー参加時にウェルカムチャンネルへ診断開始ボタンを投稿"""
    if member.bot:
        return
    if WELCOME_CHANNEL_ID <= 0:
        return
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel is None or not isinstance(channel, discord.TextChannel):
        return
    embed = discord.Embed(
        title="🎯 AIマッチング診断スタート",
        description=f"👋 {member.mention} さん、ようこそ！下のボタンを押すと、あなた専用の診断ルームが作成されます。",
    )
    await channel.send(embed=embed, view=StartRoomView())


@bot.tree.command(name="room", description="専用診断ルームを作成し自動で開始")
async def room(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
        return
    await create_or_open_room(interaction)


@bot.tree.command(name="panel", description="診断開始ボタンを設置（運営専用）")
async def panel(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
        return
    if not has_role_id(interaction.user, BOTADMIN_ROLE_ID) and BOTADMIN_ROLE_ID > 0:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    await post_panel(interaction.channel)
    await interaction.response.send_message("✅ 設置しました。", ephemeral=True)


@bot.tree.command(name="ping", description="動作確認（運営専用）")
async def ping(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
        return
    if not has_role_id(interaction.user, ADMIN_ROLE_ID) and ADMIN_ROLE_ID > 0:
        await interaction.response.send_message("このコマンドは運営専用です。", ephemeral=True)
        return
    await interaction.response.send_message("🏓 pong!", ephemeral=True)


@bot.tree.command(name="logs", description="管理者用：利用状況を表示（Embed）")
async def logs(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
        return
    if ADMIN_CHANNEL_ID > 0 and interaction.channel_id != ADMIN_CHANNEL_ID:
        await interaction.response.send_message("このコマンドは管理者チャンネルでのみ使用できます。", ephemeral=True)
        return
    if not has_role_id(interaction.user, ADMIN_ROLE_ID) and ADMIN_ROLE_ID > 0:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return

    total = await asyncio.to_thread(count_total_users)
    cat_stats = await asyncio.to_thread(get_category_stats)
    completed_total = 0
    for cat, questions in CATEGORY_QUESTIONS.items():
        n = await asyncio.to_thread(count_completed_users, cat, len(questions))
        completed_total += n
    rooms = [ch for ch in interaction.guild.text_channels if ch.name.startswith("match-")]
    total_questions = sum(len(q) for q in CATEGORY_QUESTIONS.values())

    embed = discord.Embed(
        title="📊 診断Bot 利用状況",
        description="管理者向けの集計情報です。",
    )
    embed.add_field(name="総ユーザー数", value=str(total), inline=True)
    embed.add_field(name="診断完了（全カテゴリー合計）", value=str(completed_total), inline=True)
    embed.add_field(name="専用ルーム数", value=str(len(rooms)), inline=True)
    embed.add_field(name="総質問数", value=str(total_questions), inline=True)
    for cat, meta in CATEGORY_META.items():
        s = cat_stats.get(cat, {"users": 0, "answers": 0})
        embed.add_field(
            name=f"{meta['emoji']} {meta['name']}",
            value=f"ユーザー: {s['users']}\n回答数: {s['answers']}",
            inline=True
        )
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="start", description="マッチングサービスを開始")
async def start(interaction: discord.Interaction):
    """マッチングサービスの開始"""
    if interaction.guild is None:
        await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
        return
    
    # ユーザー登録
    user_id = await asyncio.to_thread(
        get_or_create_user,
        str(interaction.user.id),
        interaction.user.name
    )
    
    # カテゴリー選択
    embed = discord.Embed(
        title="🎯 AIマッチングサービス",
        description="どのカテゴリーで診断を始めますか？",
        color=discord.Color.blue()
    )
    
    for cat_id, meta in CATEGORY_META.items():
        embed.add_field(
            name=f"{meta['emoji']} {meta['name']}",
            value=meta['description'],
            inline=False
        )
    
    view = CategorySelectView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    # カテゴリー選択を待つ
    await view.wait()
    
    if view.category:
        # 診断開始
        questions = CATEGORY_QUESTIONS[view.category]
        order = await asyncio.to_thread(
            get_or_create_order,
            user_id,
            view.category,
            [q["id"] for q in questions]
        )
        
        await update_question_message(
            interaction.channel,
            user_id,
            view.category,
            0,
            order,
            questions
        )


@bot.tree.command(name="profile", description="プロフィールを表示")
@app_commands.describe(category="カテゴリー（省略時は全て表示）")
@app_commands.choices(category=[
    app_commands.Choice(name="友達探し", value="friendship"),
    app_commands.Choice(name="恋愛マッチング", value="dating"),
    app_commands.Choice(name="ゲーム仲間", value="gaming"),
    app_commands.Choice(name="ビジネス", value="business"),
])
async def profile(interaction: discord.Interaction, category: Optional[str] = None):
    """プロフィール表示"""
    user_id = await asyncio.to_thread(
        get_user_by_discord_id,
        str(interaction.user.id)
    )
    
    if not user_id:
        await interaction.response.send_message(
            "まだ登録されていません。`/start` で開始してください。",
            ephemeral=True
        )
        return
    
    if category:
        categories = [category]
    else:
        categories = await asyncio.to_thread(get_user_categories, user_id)
    
    if not categories:
        await interaction.response.send_message(
            "プロフィールがありません。`/start` で診断を開始してください。",
            ephemeral=True
        )
        return
    
    embeds = []
    for cat in categories:
        profile_data = await asyncio.to_thread(get_profile, user_id, cat)
        if not profile_data:
            continue
        
        meta = CATEGORY_META[cat]
        embed = discord.Embed(
            title=f"{meta['emoji']} {meta['name']}",
            color=meta['color']
        )
        
        if profile_data['bio']:
            embed.add_field(
                name="📝 プロフィール",
                value=profile_data['bio'],
                inline=False
            )
        
        if profile_data['interests']:
            embed.add_field(
                name="🏷️ キーワード",
                value=", ".join(profile_data['interests'][:10]),
                inline=False
            )
        
        traits = profile_data.get('personality_traits', {})
        if isinstance(traits, dict) and 'key_traits' in traits:
            embed.add_field(
                name="✨ 特徴",
                value="• " + "\n• ".join(traits['key_traits'][:5]),
                inline=False
            )
        
        embeds.append(embed)
    
    await interaction.response.send_message(embeds=embeds[:10], ephemeral=True)


@bot.tree.command(name="match", description="マッチング相手を探す")
@app_commands.describe(category="カテゴリー")
@app_commands.choices(category=[
    app_commands.Choice(name="友達探し", value="friendship"),
    app_commands.Choice(name="恋愛マッチング", value="dating"),
    app_commands.Choice(name="ゲーム仲間", value="gaming"),
    app_commands.Choice(name="ビジネス", value="business"),
])
async def match(interaction: discord.Interaction, category: str):
    """マッチング検索"""
    await interaction.response.defer(ephemeral=True)
    
    user_id = await asyncio.to_thread(
        get_user_by_discord_id,
        str(interaction.user.id)
    )
    
    if not user_id:
        await interaction.followup.send("まだ登録されていません。`/start` で開始してください。", ephemeral=True)
        return
    
    # 診断完了チェック
    questions = CATEGORY_QUESTIONS[category]
    if await asyncio.to_thread(get_state, user_id, category) < len(questions):
        await interaction.followup.send(
            f"まず `/start` で{CATEGORY_META[category]['name']}の診断を完了してください。",
            ephemeral=True
        )
        return
    
    # 自分のプロフィールと回答を取得
    my_profile = await asyncio.to_thread(get_profile, user_id, category)
    my_answers = await asyncio.to_thread(load_answers, user_id, category)
    
    # 他のユーザーを検索
    # TODO: データベースから効率的に検索する実装
    # 現状はシンプルなデモ実装
    await interaction.followup.send(
        f"🔍 {CATEGORY_META[category]['emoji']} {CATEGORY_META[category]['name']}で検索中...\n\n"
        f"現在、マッチング機能を実装中です。近日公開予定！",
        ephemeral=True
    )


@bot.tree.command(name="stats", description="サービスの統計情報")
async def stats(interaction: discord.Interaction):
    """統計情報表示"""
    if not has_role_id(interaction.user, ADMIN_ROLE_ID) and ADMIN_ROLE_ID > 0:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    
    total_users = await asyncio.to_thread(count_total_users)
    cat_stats = await asyncio.to_thread(get_category_stats)
    
    embed = discord.Embed(
        title="📊 サービス統計",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="総ユーザー数", value=str(total_users), inline=True)
    
    for cat, meta in CATEGORY_META.items():
        stats = cat_stats.get(cat, {"users": 0, "answers": 0})
        embed.add_field(
            name=f"{meta['emoji']} {meta['name']}",
            value=f"ユーザー: {stats['users']}\n回答数: {stats['answers']}",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# 起動
# =========================================================
if __name__ == "__main__":
    bot.run(TOKEN)
