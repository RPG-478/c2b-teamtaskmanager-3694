from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import typing
import uuid
import os
import json

# Define paths for data files
TASKS_FILE = 'data/tasks.json'

# Helper functions for JSON persistence (assuming they are in utils/helpers.py but included here for self-containment)
# In a real project, these would be imported from `from utils.helpers import load_json, save_json`
def load_json(file_path: str) -> dict:
    """Loads JSON data from a specified file path."""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}. Returning empty dict.")
        return {}
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return {}

def save_json(file_path: str, data: dict):
    """Saves JSON data to a specified file path."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {e}")

class TaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Initialize task data by loading from 'data/tasks.json'
        # Ensure 'tasks' key exists in the loaded data, defaulting to an empty list.
        self.tasks = load_json(TASKS_FILE)
        self.tasks.setdefault('tasks', [])

    @app_commands.command(name="task_add", description="新しいタスクを作成します。")
    @app_commands.describe(
        title="タスクのタイトル",
        description="タスクの詳細",
        due_date="YYYY-MM-DD形式の期限 (例: 2023-12-31)",
        assignee="タスクの担当者"
    )
    async def task_add(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        description: typing.Optional[str] = None, 
        due_date: typing.Optional[str] = None, 
        assignee: typing.Optional[discord.Member] = None
    ):
        """新しいタスクを作成し、タスクリストに追加します。"""
        await interaction.response.defer(ephemeral=True) # タイムアウトを防ぐため、即座に応答を保留

        # ユニークなタスクIDを生成
        task_id = str(uuid.uuid4())[:8] # 短いIDにするため最初の8文字を使用

        parsed_due_date = None
        if due_date:
            try:
                # YYYY-MM-DD形式の期限を検証
                datetime.datetime.strptime(due_date, '%Y-%m-%d')
                parsed_due_date = due_date
            except ValueError:
                await interaction.followup.send(
                    "エラー: 期限の形式が無効です。YYYY-MM-DD形式で入力してください (例: 2023-12-31)。", 
                    ephemeral=True
                )
                return

        # 新しいタスクの辞書を構築
        new_task = {
            'id': task_id,
            'title': title,
            'description': description if description else "",
            'due_date': parsed_due_date,
            'assignee_id': assignee.id if assignee else None,
            'creator_id': interaction.user.id,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'status': "active"
        }

        # タスクリストに新しいタスクを追加
        self.tasks['tasks'].append(new_task)

        try:
            # 更新されたタスクデータをJSONファイルに保存
            save_json(TASKS_FILE, self.tasks)
        except Exception as e:
            await interaction.followup.send(f"エラー: タスクの保存中に問題が発生しました。{e}", ephemeral=True)
            return

        # タスク作成確認のEmbedを作成して送信
        embed = discord.Embed(
            title="✅ タスクが作成されました！",
            description=f"タスクID: `{task_id}`",
            color=discord.Color.green()
        )
        embed.add_field(name="タイトル", value=title, inline=False)
        if description: embed.add_field(name="詳細", value=description, inline=False)
        if parsed_due_date: embed.add_field(name="期限", value=parsed_due_date, inline=True)
        if assignee: embed.add_field(name="担当者", value=assignee.mention, inline=True)
        embed.add_field(name="作成者", value=interaction.user.mention, inline=True)
        embed.add_field(name="ステータス", value="active", inline=True)
        embed.set_footer(text="タスク管理ボット")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task_list", description="タスクの一覧をEmbedで表示します。")
    async def task_list(
        self, 
        interaction: discord.Interaction
    ):
        """アクティブなタスクの一覧をEmbedで表示します。"""
        await interaction.response.defer(ephemeral=False) # 全員に見えるように応答を保留

        # アクティブなタスクのみをフィルタリング
        active_tasks = [task for task in self.tasks['tasks'] if task['status'] == 'active']

        if not active_tasks:
            await interaction.followup.send("現在、アクティブなタスクはありません。", ephemeral=True)
            return

        # タスク表示用のEmbedを作成
        embed = discord.Embed(
            title="📋 アクティブなタスク一覧",
            description="現在進行中のタスクです。",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"合計 {len(active_tasks)} 件のタスク")

        # 各タスクの情報をEmbedのフィールドに追加
        # Embedのフィールド数には限りがあるため、簡潔に表示
        for i, task in enumerate(active_tasks):
            if i >= 10: # 最大10件まで表示し、それ以上は省略
                embed.add_field(name="...", value="さらに多くのタスクがあります。", inline=False)
                break
            
            assignee_mention = "未割り当て"
            if task['assignee_id']:
                assignee = self.bot.get_user(task['assignee_id']) or await self.bot.fetch_user(task['assignee_id'])
                if assignee: assignee_mention = assignee.mention

            due_date_str = f"期限: {task['due_date']}" if task['due_date'] else "期限なし"
            
            embed.add_field(
                name=f"ID: {task['id']} | {task['title']}",
                value=f"担当: {assignee_mention} | {due_date_str}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task_done", description="指定したタスクを完了済みにします。")
    @app_commands.describe(
        task_id="完了するタスクのID"
    )
    async def task_done(
        self, 
        interaction: discord.Interaction, 
        task_id: str
    ):
        """指定されたタスクを完了済みにマークします。"""
        await interaction.response.defer(ephemeral=True) # タイムアウトを防ぐため、即座に応答を保留

        found_task = None
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                found_task = task
                break

        if not found_task:
            await interaction.followup.send("エラー: 指定されたタスクは見つかりませんでした。", ephemeral=True)
            return

        if found_task['status'] == 'done':
            await interaction.followup.send("エラー: このタスクは既に完了済みです。", ephemeral=True)
            return
        if found_task['status'] == 'deleted':
            await interaction.followup.send("エラー: このタスクは既に削除されています。", ephemeral=True)
            return

        # タスクのステータスを「完了」に更新し、完了日時を記録
        found_task['status'] = 'done'
        found_task['completed_at'] = datetime.datetime.utcnow().isoformat()

        try:
            # 更新されたタスクデータをJSONファイルに保存
            save_json(TASKS_FILE, self.tasks)
        except Exception as e:
            await interaction.followup.send(f"エラー: タスクの保存中に問題が発生しました。{e}", ephemeral=True)
            return

        # タスク完了確認のEmbedを作成して送信
        embed = discord.Embed(
            title="✅ タスクが完了しました！",
            description=f"タスクID: `{task_id}`",
            color=discord.Color.green()
        )
        embed.add_field(name="タイトル", value=found_task['title'], inline=False)
        embed.add_field(name="新しいステータス", value="完了済み", inline=True)
        embed.set_footer(text="タスク管理ボット")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task_delete", description="指定したタスクを削除します。")
    @app_commands.describe(
        task_id="削除するタスクのID"
    )
    async def task_delete(
        self, 
        interaction: discord.Interaction, 
        task_id: str
    ):
        """指定されたタスクを削除済みにマークします（履歴は保持）。"""
        await interaction.response.defer(ephemeral=True) # タイムアウトを防ぐため、即座に応答を保留

        found_task = None
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                found_task = task
                break

        if not found_task:
            await interaction.followup.send("エラー: 指定されたタスクは見つかりませんでした。", ephemeral=True)
            return

        if found_task['status'] == 'deleted':
            await interaction.followup.send("エラー: このタスクは既に削除済みです。", ephemeral=True)
            return

        # タスクのステータスを「削除済み」に更新し、削除日時を記録
        found_task['status'] = 'deleted'
        found_task['deleted_at'] = datetime.datetime.utcnow().isoformat()

        try:
            # 更新されたタスクデータをJSONファイルに保存
            save_json(TASKS_FILE, self.tasks)
        except Exception as e:
            await interaction.followup.send(f"エラー: タスクの保存中に問題が発生しました。{e}", ephemeral=True)
            return

        # タスク削除確認のEmbedを作成して送信
        embed = discord.Embed(
            title="🗑️ タスクが削除されました！",
            description=f"タスクID: `{task_id}`",
            color=discord.Color.red()
        )
        embed.add_field(name="タイトル", value=found_task['title'], inline=False)
        embed.add_field(name="新しいステータス", value="削除済み", inline=True)
        embed.set_footer(text="タスク管理ボット")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task_edit", description="指定したタスクの内容を編集します。")
    @app_commands.describe(
        task_id="編集するタスクのID",
        title="新しいタスクのタイトル (変更しない場合は省略)",
        description="新しいタスクの詳細 (変更しない場合は省略)",
        due_date="新しいYYYY-MM-DD形式の期限 (変更しない場合は省略)",
        assignee="新しいタスクの担当者 (変更しない場合は省略)"
    )
    async def task_edit(
        self, 
        interaction: discord.Interaction, 
        task_id: str, 
        title: typing.Optional[str] = None, 
        description: typing.Optional[str] = None, 
        due_date: typing.Optional[str] = None, 
        assignee: typing.Optional[discord.Member] = None
    ):
        """指定されたタスクの情報を編集します。"""
        await interaction.response.defer(ephemeral=True) # タイムアウトを防ぐため、即座に応答を保留

        found_task = None
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                found_task = task
                break

        if not found_task:
            await interaction.followup.send("エラー: 指定されたタスクは見つかりませんでした。", ephemeral=True)
            return

        # 提供された引数に基づいてタスク情報を更新
        if title is not None:
            found_task['title'] = title
        if description is not None:
            found_task['description'] = description
        if assignee is not None:
            found_task['assignee_id'] = assignee.id
        
        parsed_due_date = found_task['due_date'] # 既存の期限を保持
        if due_date is not None:
            if due_date == "none": # 期限をクリアするオプション
                parsed_due_date = None
            else:
                try:
                    # YYYY-MM-DD形式の期限を検証
                    datetime.datetime.strptime(due_date, '%Y-%m-%d')
                    parsed_due_date = due_date
                except ValueError:
                    await interaction.followup.send(
                        "エラー: 期限の形式が無効です。YYYY-MM-DD形式で入力するか 'none' でクリアしてください。", 
                        ephemeral=True
                    )
                    return
        found_task['due_date'] = parsed_due_date

        try:
            # 更新されたタスクデータをJSONファイルに保存
            save_json(TASKS_FILE, self.tasks)
        except Exception as e:
            await interaction.followup.send(f"エラー: タスクの保存中に問題が発生しました。{e}", ephemeral=True)
            return

        # タスク編集確認のEmbedを作成して送信
        embed = discord.Embed(
            title="✏️ タスクが編集されました！",
            description=f"タスクID: `{task_id}`",
            color=discord.Color.blue()
        )
        embed.add_field(name="タイトル", value=found_task['title'], inline=False)
        embed.add_field(name="詳細", value=found_task['description'] if found_task['description'] else "なし", inline=False)
        embed.add_field(name="期限", value=found_task['due_date'] if found_task['due_date'] else "なし", inline=True)
        
        assignee_mention = "未割り当て"
        if found_task['assignee_id']:
            assignee_user = self.bot.get_user(found_task['assignee_id']) or await self.bot.fetch_user(found_task['assignee_id'])
            if assignee_user: assignee_mention = assignee_user.mention
        embed.add_field(name="担当者", value=assignee_mention, inline=True)
        embed.add_field(name="ステータス", value=found_task['status'], inline=True)
        embed.set_footer(text="タスク管理ボット")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="task_detail", description="指定したタスクの詳細を表示します。")
    @app_commands.describe(
        task_id="詳細を表示するタスクのID"
    )
    async def task_detail(
        self, 
        interaction: discord.Interaction, 
        task_id: str
    ):
        """指定されたタスクの全詳細情報をEmbedで表示します。"""
        await interaction.response.defer(ephemeral=False) # 全員に見えるように応答を保留

        found_task = None
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                found_task = task
                break

        if not found_task:
            await interaction.followup.send("エラー: 指定されたタスクは見つかりませんでした。", ephemeral=True)
            return

        # タスクのステータスに基づいてEmbedの色を設定
        color = discord.Color.blue()
        if found_task['status'] == 'active':
            color = discord.Color.green()
        elif found_task['status'] == 'done':
            color = discord.Color.light_grey()
        elif found_task['status'] == 'deleted':
            color = discord.Color.red()

        # タスク詳細表示用のEmbedを作成
        embed = discord.Embed(
            title=f"🔍 タスク詳細: {found_task['title']}",
            description=f"タスクID: `{found_task['id']}`",
            color=color
        )

        embed.add_field(name="タイトル", value=found_task['title'], inline=False)
        embed.add_field(name="詳細", value=found_task['description'] if found_task['description'] else "なし", inline=False)
        embed.add_field(name="ステータス", value=found_task['status'].capitalize(), inline=True)
        embed.add_field(name="期限", value=found_task['due_date'] if found_task['due_date'] else "なし", inline=True)

        # 担当者IDをDiscordユーザー名に解決
        assignee_mention = "未割り当て"
        if found_task['assignee_id']:
            assignee = self.bot.get_user(found_task['assignee_id']) or await self.bot.fetch_user(found_task['assignee_id'])
            if assignee: assignee_mention = assignee.mention
        embed.add_field(name="担当者", value=assignee_mention, inline=True)

        # 作成者IDをDiscordユーザー名に解決
        creator_mention = "不明なユーザー"
        if found_task['creator_id']:
            creator = self.bot.get_user(found_task['creator_id']) or await self.bot.fetch_user(found_task['creator_id'])
            if creator: creator_mention = creator.mention
        embed.add_field(name="作成者", value=creator_mention, inline=True)

        embed.add_field(name="作成日時", value=found_task['created_at'], inline=False)
        if 'completed_at' in found_task and found_task['completed_at']:
            embed.add_field(name="完了日時", value=found_task['completed_at'], inline=False)
        if 'deleted_at' in found_task and found_task['deleted_at']:
            embed.add_field(name="削除日時", value=found_task['deleted_at'], inline=False)

        embed.set_footer(text="タスク管理ボット")

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TaskCog(bot))