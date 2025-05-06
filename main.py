from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
import os
import json
import random
import time
import hashlib
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

@register("捕鱼大亨", "Koikokokokoro", "群组捕鱼小游戏", "0.1.0")
class Fishing(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 数据目录与静态文件路径
        base = os.getcwd()
        self.data_dir = os.path.join(base, "data", "plugins", "fishing_tycoon")
        os.makedirs(self.data_dir, exist_ok=True)
        self.fish_file = os.path.join(self.data_dir, "fish_data.json")
        self.item_file = os.path.join(self.data_dir, "fish_item.json")
        self.gacha_file = os.path.join(self.data_dir, "gacha.json")
        # 游戏存档
        self.group_file = lambda gid: os.path.join(self.data_dir, f"group_{gid}.json")
        self.user_file = lambda uid: os.path.join(self.data_dir, f"user_{uid}.json")
        # 加载静态数据
        self.fish_data = self._load_static(self.fish_file)
        self.item_data = self._load_static(self.item_file)
        self.gacha_data = self._load_static(self.gacha_file)
        self.max_tries = 10

    def _load_static(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            logger.warning(f"无法加载静态文件 {path}")
            return []

    def _load_json(self, path, default):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default

    def _save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def initialize(self):
        logger.info("捕鱼大亨插件初始化完成")

    @filter.command("面板")
    async def panel(self, event: AstrMessageEvent):
        uid = str(event.get_sender_id())
        user = self._load_json(self.user_file(uid), {
            'qq': uid, 'name': '', 'level': 1, 'exp': 0, 'gold': 0,
            'score': 0, 'bag': self.item_data[:1], 'buff': []
        })
        # TODO: fetch avatar and draw panel
        yield event.plain_result(f"面板：等级{user['level']}，金币{user['gold']}")

    @filter.command("背包")
    async def bag(self, event: AstrMessageEvent):
        uid = str(event.get_sender_id())
        user = self._load_json(self.user_file(uid), {})
        items = user.get('bag', [])
        yield event.plain_result(f"背包物品：{[i['name'] for i in items]}")

    @filter.command("捕鱼")
    async def catch_cmd(self, event: AstrMessageEvent):
        gid = str(event.get_group_id())
        uid = str(event.get_sender_id())
        group = self._load_json(self.group_file(gid), {'current': None, 'tries': self.max_tries})
        # TODO: spawn logic checks
        res = "捕捞功能待实现"
        self._save_json(self.group_file(gid), group)
        yield event.plain_result(res)

    @filter.command("单抽")
    async def draw_one(self, event: AstrMessageEvent):
        uid = str(event.get_sender_id())
        user = self._load_json(self.user_file(uid), {})
        # TODO: perform gacha single
        res = "单抽功能待实现"
        self._save_json(self.user_file(uid), user)
        yield event.plain_result(res)

    @filter.command("十连")
    async def draw_ten(self, event: AstrMessageEvent):
        uid = str(event.get_sender_id())
        user = self._load_json(self.user_file(uid), {})
        # TODO: perform gacha ten
        res = "十连功能待实现"
        self._save_json(self.user_file(uid), user)
        yield event.plain_result(res)

    @filter.command("商店")
    async def shop_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(f"商店物品：{[i['name'] for i in self.item_data]}")

    @filter.command("商店购买")
    async def buy_cmd(self, event: AstrMessageEvent, idx: int):
        uid = str(event.get_sender_id())
        user = self._load_json(self.user_file(uid), {})
        # TODO: purchase logic
        res = "购买功能待实现"
        self._save_json(self.user_file(uid), user)
        yield event.plain_result(res)

    @filter.command("使用")
    async def use_cmd(self, event: AstrMessageEvent, idx: int):
        uid = str(event.get_sender_id())
        user = self._load_json(self.user_file(uid), {})
        # TODO: use item logic
        res = "使用功能待实现"
        self._save_json(self.user_file(uid), user)
        yield event.plain_result(res)

    @filter.command("状态")
    async def status_cmd(self, event: AstrMessageEvent):
        gid = str(event.get_group_id())
        group = self._load_json(self.group_file(gid), {})
        yield event.plain_result(f"状态：{group}")

    async def terminate(self):
        logger.info("捕鱼大亨插件已停用")
