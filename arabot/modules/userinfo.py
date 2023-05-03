from collections import defaultdict

import disnake
from disnake.ext import commands
from disnake.utils import format_dt, utcnow

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyMember, AnyMemberOrUser


class GlobalOrGuildUserVariant(disnake.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds

    @disnake.ui.button(label="Global", style=disnake.ButtonStyle.blurple)
    async def global_variant(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.embeds[0])

    @disnake.ui.button(label="Server", style=disnake.ButtonStyle.blurple)
    async def guild_variant(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.embeds[1])


class Userinfo(Cog, category=Category.GENERAL):
    @commands.command(aliases=["a", "pfp"], brief="Show user's avatar", usage="[member]")
    async def avatar(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        avatars = (
            disnake.Embed()
            .set_image(url=(member.avatar or member.default_avatar).compat)
            .set_footer(text=ctx._("global_avatar").format(member.display_name)),
            disnake.Embed()
            .set_image(url=member.display_avatar.compat)
            .set_footer(text=ctx._("guild_avatar").format(member.display_name)),
        )

        if not member.guild_avatar:
            await ctx.send(embed=avatars[0])
            return

        await ctx.send(embed=avatars[1], view=GlobalOrGuildUserVariant(avatars))

    @commands.command(
        aliases=["b"],
        brief="Show user's global banner",
        usage="[member]",
        extras={"note": "Due to a Discord limitation, server banners are irretrievable"},
    )
    async def banner(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        banner = (await ctx.ara.fetch_user(member.id)).banner
        if not banner:
            await ctx.send_("no_banner")
            return
        await ctx.send(
            embed=disnake.Embed()
            .set_image(url=banner.maxres.compat)
            .set_footer(text=ctx._("their_banner", False).format(member.display_name))
        )

    @commands.command(
        aliases=["user", "dox", "doxx", "whois"], brief="View user's info", usage="[member]"
    )
    async def userinfo(self, ctx: Context, *, member: AnyMemberOrUser = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        embed = (
            disnake.Embed(
                title=member,
                url=f"https://discord.com/users/{member.id}",
                timestamp=utcnow(),
            )
            .set_author(
                name=member.id,
                icon_url="https://twemoji.maxcdn.com/v/latest/72x72/1f194.png",
                url=f"https://discord.com/users/{member.id}",
            )
            .set_thumbnail(url=(member.avatar or member.default_avatar).compat)
            .add_field(ctx._("created_on"), format_dt(member.created_at, "D"))
        )
        description = defaultdict(list)
        if member.bot:
            description[0].append(ctx._("bot", False))
        if member.public_flags.spammer:
            description[0].append(f"**{ctx._('spammer')}**")

        if isinstance(member, disnake.Member):
            embed.set_footer(
                text=member.guild.name,
                icon_url=ctx.guild.icon and ctx.guild.icon.as_icon.compat,
            )
            if member.guild_avatar:
                description[1].append(f"[{ctx._('guild_avatar')}]({member.guild_avatar})")
            if member.pending:
                description[0].append(ctx._("pending"))

            if member.joined_at:
                embed.add_field(ctx._("joined_on"), format_dt(member.joined_at, "D"))
            if member.nick:
                embed.add_field(ctx._("nickname", False), member.nick)
            if member.activity:
                embed.add_field(ctx._("discord_activity", False), member.activity.name)
            if member.premium_since:
                embed.add_field(ctx._("boosting_since"), format_dt(member.premium_since, "R"))
            if member.current_timeout:
                embed.add_field(ctx._("muted_until"), format_dt(member.current_timeout, "D"))
            elif member.voice and member.voice.channel:
                embed.add_field(ctx._("talking_in"), member.voice.channel.mention)
            embed.add_field(ctx._("top_perm_role"), member.top_perm_role.mention)
            member = await ctx.ara.fetch_user(member.id)  # `Member.banner` is always None
        elif not member.accent_color:  # Very unrealiable check if `User` is retrieved from cache
            member = await ctx.ara.fetch_user(member.id)  # Fetching as `User.banner` is not cached

        if member.accent_color:
            embed.color = member.accent_color
        if member.banner:
            embed.set_image(url=member.banner.with_size(512).compat)

        embed.description = "\n".join(", ".join(description[line]) for line in sorted(description))
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Userinfo())
