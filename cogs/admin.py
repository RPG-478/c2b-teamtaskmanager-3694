from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from typing import TYPE_CHECKING, Dict, Any, Optional

# Assuming these helper functions exist in utils/helpers.py for config data
from utils.helpers import load_config_data, save_config_data

if TYPE_CHECKING:
    from main import MyBot


class AdminCog(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        # Load config data on cog init.
        # config_data will store settings per guild ID.
        # Example structure: {"guild_id_str": {"welcome_channel_id": 123, "logging_channel_id": 456}}
        self.config_data: Dict[str, Dict[str, Any]] = load_config_data()

    def _get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """
        指定されたギルドのコンフィグデータを取得します。
        もしギルドのコンフィグが存在しない場合は、新しい空の辞書を初期化して返します。
        """
        guild_id_str = str(guild_id)
        if guild_id_str not in self.config_data:
            self.config_data[guild_id_str] = {} # ギルド用の空の辞書を初期化
        return self.config_data[guild_id_str]

    @app_commands.command(name="ping", description="ボットの応答性を確認します。")
    async def ping(self, interaction: discord.Interaction):
        """
        ボットの応答性を確認するシンプルなコマンド。
        """
        await interaction.response.send_message("Pong!", ephemeral=True)

    @app_commands.group(name="config", description="ボットのサーバー設定を行います（管理者のみ）。")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_group(self, interaction: discord.Interaction):
        """
        サーバー設定コマンドのグループ。
        このコマンド自体は直接実行されず、サブコマンドを通じて設定を管理します。
        """
        # このベースコマンドは、サブコマンドが呼び出される際に権限チェックを行うために存在します。
        # 直接実行されることはありません。
        if interaction.guild is None:
            await interaction.response.send_message("このコマンドはサーバーでのみ実行できます。", ephemeral=True)
            return

    @config_group.command(name="show", description="現在のサーバー設定を表示します。")
    async def config_show(self, interaction: discord.Interaction):
        """
        現在のサーバー設定をEmbedで表示します。
        """
        if interaction.guild is None:
            await interaction.response.send_message("このコマンドはサーバーでのみ実行できます。", ephemeral=True)
            return

        guild_id = interaction.guild.id
        guild_config = self._get_guild_config(guild_id)

        embed = discord.Embed(
            title=f"⚙️ {interaction.guild.name} のサーバー設定",
            color=discord.Color.blue()
        )

        # ウェルカムチャンネルの設定表示
        welcome_channel_id = guild_config.get("welcome_channel_id")
        if welcome_channel_id:
            welcome_channel = interaction.guild.get_channel(welcome_channel_id)
            embed.add_field(name="ウェルカムチャンネル", value=welcome_channel.mention if welcome_channel else f"不明なチャンネル (ID: {welcome_channel_id})", inline=False)
        else:
            embed.add_field(name="ウェルカムチャンネル", value="未設定", inline=False)

        # ログチャンネルの設定表示
        logging_channel_id = guild_config.get("logging_channel_id")
        if logging_channel_id:
            logging_channel = interaction.guild.get_channel(logging_channel_id)
            embed.add_field(name="ログチャンネル", value=logging_channel.mention if logging_channel else f"不明なチャンネル (ID: {logging_channel_id})", inline=False)
        else:
            embed.add_field(name="ログチャンネル", value="未設定", inline=False)

        # 必要に応じて他の設定もここに追加

        embed.set_footer(text="設定を変更するには /config set_<設定名> コマンドを使用してください。")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @config_group.command(name="set_welcome_channel", description="ウェルカムメッセージを送信するチャンネルを設定します。")
    @app_commands.describe(channel="ウェルカムチャンネルとして設定するテキストチャンネル")
    async def config_set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        ウェルカムチャンネルを設定し、設定を保存します。
        """
        if interaction.guild is None:
            await interaction.response.send_message("このコマンドはサーバーでのみ実行できます。", ephemeral=True)
            return

        guild_id = interaction.guild.id
        guild_config = self._get_guild_config(guild_id)

        try:
            # ギルドコンフィグにウェルカムチャンネルIDを保存
            guild_config["welcome_channel_id"] = channel.id
            save_config_data(self.config_data) # 更新されたコンフィグデータをファイルに保存
            embed = discord.Embed(
                title="✅ ウェルカムチャンネル設定完了",
                description=f"ウェルカムチャンネルを {channel.mention} に設定しました。",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # 設定保存中にエラーが発生した場合のハンドリング
            embed = discord.Embed(
                title="❌ 設定エラー",
                description=f"ウェルカムチャンネルの設定中にエラーが発生しました: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @config_group.command(name="set_logging_channel", description="ボットのログを送信するチャンネルを設定します。")
    @app_commands.describe(channel="ログチャンネルとして設定するテキストチャンネル")
    async def config_set_logging_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        ログチャンネルを設定し、設定を保存します。
        """
        if interaction.guild is None:
            await interaction.response.send_message("このコマンドはサーバーでのみ実行できます。", ephemeral=True)
            return

        guild_id = interaction.guild.id
        guild_config = self._get_guild_config(guild_id)

        try:
            # ギルドコンフィグにログチャンネルIDを保存
            guild_config["logging_channel_id"] = channel.id
            save_config_data(self.config_data) # 更新されたコンフィグデータをファイルに保存
            embed = discord.Embed(
                title="✅ ログチャンネル設定完了",
                description=f"ログチャンネルを {channel.mention} に設定しました。",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # 設定保存中にエラーが発生した場合のハンドリング
            embed = discord.Embed(
                title="❌ 設定エラー",
                description=f"ログチャンネルの設定中にエラーが発生しました: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: MyBot):
    await bot.add_cog(AdminCog(bot))