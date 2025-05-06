from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, scheduler
import astrbot.api.message_components as Comp

import os, json, random, time, hashlib, aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

@register("捕鱼大亨", "Koikokokokoro", "Astrbot捕鱼插件", "0.0.3")
class Fishing(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化文件路径
        self.DATA_DIR = os.path.join(os.getcwd(), "data", "plugins", "astrbot_plugin_fishing")
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.FISH_FILE = os.path.join(self.DATA_DIR, "fish_data.json")
        self.ITEM_FILE = os.path.join(self.DATA_DIR, "fish_item.json")
        self.GACHA_FILE = os.path.join(self.DATA_DIR, "gacha.json")
        self.PLAYER_DIR = os.path.join(self.DATA_DIR, "players")
        self.GROUP_DIR = os.path.join(self.DATA_DIR, "groups")
        os.makedirs(self.PLAYER_DIR, exist_ok=True)
        os.makedirs(self.GROUP_DIR, exist_ok=True)
        # 加载静态数据
        self.fish_data = self._load_json(self.FISH_FILE)
        self.item_data = self._load_json(self.ITEM_FILE)
        self.gacha_data = self._load_json(self.GACHA_FILE)

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _md5(self, s):
        import hashlib
        return hashlib.md5(s.encode()).hexdigest()

    def _buff_available(self, buff):
        import time
        expire = buff.get('expire', 0)
        times = buff.get('time', 999)
        return times > 0 and (expire == 0 or expire > time.time())

    class FishPlayer:
        def __init__(self, parent, qq):
            import os, json
            self.parent = parent
            self.qq = str(qq)
            self.file = os.path.join(parent.PLAYER_DIR, f"{self.qq}.json")
            self.data = {'name':'渔者','level':1,'exp':0,'gold':0,'score':0,
                         'fish_log':[],'bag':parent.item_data[:1],'buff':[]}
            if os.path.exists(self.file):
                try:
                    self.data = json.load(open(self.file,'r',encoding='utf-8'))
                except:
                    pass
        def save(self):
            import json
            json.dump(self.data, open(self.file,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
        def refresh_buff(self):
            self.data['buff'] = [b for b in self.data['buff'] if self.parent._buff_available(b)]
        @property
        def power(self):
            p = self.data['level']
            for it in self.data['bag']:
                if it.get('equipped'): p += it.get('power', 0)
            return p

    class FishGame:
        def __init__(self, parent, group):
            import os, json
            self.parent = parent
            self.group = str(group)
            self.file = os.path.join(parent.GROUP_DIR, f"{self.group}.json")
            self.data = {'fish_log':[],'buff':[],'day':0,'feed_time':0}
            if os.path.exists(self.file):
                try:
                    self.data = json.load(open(self.file,'r',encoding='utf-8'))
                except:
                    pass
            self.current_fish = None
            self.try_list = []
            self.leave_time = 0
        def save(self):
            import json
            json.dump(self.data, open(self.file,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
        def refresh_buff(self):
            self.data['buff'] = [b for b in self.data['buff'] if self.parent._buff_available(b)]
        # TODO: spawn_fish, count_down, catch, gacha, shop, buy, use_item, status

    async def initialize(self):
        logger.info("捕鱼大亨插件 v0.0.3 初始化完成")

    # 定时刷鱼
    @scheduler.scheduled_job('cron', minute='*')
    async def _task_spawn(self):
        # TODO: 遍历群组文件，spawn/count_down 并 yield 通知
        pass

    @filter.command("面板")
    async def panel(self, event: AstrMessageEvent):
        player = Fishing.FishPlayer(self, event.get_sender_id())
        player.refresh_buff(); player.save()
        # TODO: 调用绘图函数 create_character_panel
        yield event.plain_result("面板功能未完成")

    @filter.command("背包")
    async def bag(self, event: AstrMessageEvent):
        yield event.plain_result("背包功能未完成")

    @filter.command("捕鱼")
    async def catch_cmd(self, event: AstrMessageEvent):
        game = Fishing.FishGame(self, event.get_group_id()); game.refresh_buff(); game.save()
        player = Fishing.FishPlayer(self, event.get_sender_id()); player.refresh_buff(); player.save()
        res = game.catch(player)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("单抽")
    async def draw_one(self, event: AstrMessageEvent):
        player = Fishing.FishPlayer(self, event.get_sender_id()); player.save()
        game = Fishing.FishGame(self, event.get_group_id()); game.save()
        res = game.gacha(player, False)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("十连")
    async def draw_ten(self, event: AstrMessageEvent):
        player = Fishing.FishPlayer(self, event.get_sender_id()); player.save()
        game = Fishing.FishGame(self, event.get_group_id()); game.save()
        res = game.gacha(player, True)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("商店")
    async def shop_cmd(self, event: AstrMessageEvent):
        items = Fishing.FishGame(self, event.get_group_id()).shop()
        yield event.plain_result(f"商店物品: {[i['name'] for i in items]}")

    @filter.command("商店购买")
    async def buy_cmd(self, event: AstrMessageEvent, num: int):
        player = Fishing.FishPlayer(self, event.get_sender_id()); player.save()
        game = Fishing.FishGame(self, event.get_group_id())
        res = game.buy(player, num)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("使用")
    async def use_cmd(self, event: AstrMessageEvent, num: int):
        player = Fishing.FishPlayer(self, event.get_sender_id()); player.save()
        game = Fishing.FishGame(self, event.get_group_id())
        res = game.use_item(player, num)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("状态")
    async def status_cmd(self, event: AstrMessageEvent):
        msg = Fishing.FishGame(self, event.get_group_id()).status()
        yield event.plain_result(msg)

    async def terminate(self):
        logger.info("捕鱼大亨插件已停用")
