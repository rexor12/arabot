from json import loads
from urllib.parse import quote_plus

from aiohttp import ClientSession
from disnake import Embed
from disnake.ext.commands import command

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import dsafe


class Wolfram(Cog, category=Category.LOOKUP, keys={"wolfram_id"}):
    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["calc"], brief="Answer a question (works mostly with mathematics)")
    async def wolfram(self, ctx: Context, *, question: str):
        await ctx.trigger_typing()
        question = question.strip("`")
        async with self.session.get(
            "https://api.wolframalpha.com/v2/query",
            params={
                "input": question,
                "format": "plaintext",
                "output": "json",
                "appid": self.wolfram_id,
                "units": "metric",
            },
        ) as wa:
            wa = loads(await wa.text())["queryresult"]
        embed = Embed(
            color=0xF4684C,
            title=dsafe(question),
            url=f"https://wolframalpha.com/input/?i={quote_plus(question)}",
        ).set_footer(
            text="Wolfram|Alpha",
            icon_url="https://cdn.iconscout.com/icon/free/png-512/wolfram-alpha-2-569293.png",
        )
        if wa["success"]:
            if "warnings" in wa:
                embed.description = wa["warnings"]["text"]
            for pod in wa["pods"]:
                if pod["id"] == ctx._("input"):
                    detected_input = pod["subpods"][0]["plaintext"]
                    embed.add_field(
                        "Input",
                        f"[{dsafe(detected_input)}]"
                        f"(https://wolframalpha.com/input/?i={quote_plus(detected_input)})",
                    )
                if "primary" in pod:
                    embed.add_field(
                        ctx._("result", False),
                        "\n".join(dsafe(subpod["plaintext"]) for subpod in pod["subpods"]),
                        inline=False,
                    )
                    break
        elif "tips" in wa:
            embed.description = wa["tips"]["text"]
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Wolfram(ara.session))
