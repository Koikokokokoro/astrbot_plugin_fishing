import os
import json
import random
import time
import hashlib
import string
from io import BytesIO
from collections import deque
import aiohttp
from PIL import Image, ImageDraw, ImageFont

from astraapi.event import filter, AstrMessageEvent, MessageEventResult
from astraapi.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api import scheduler
import redis

# -- 配置 --
__plugin_name__ = "捕鱼大亨"
__version__ = "0.0.1"
DATA_DIR = os.path.join(os.getcwd(), "data", "plugins", "fishing_tycoon")
for f in (DATA_DIR,):
    os.makedirs(f, exist_ok=True)
FISH_DATA = os.path.join(DATA_DIR, "fish_data.json")
ITEM_DATA = os.path.join(DATA_DIR, "fish_item.json")\GACHA_DATA = os.path.join(DATA_DIR, "gacha.json")

# 全局 Redis
redis_global = redis.Redis(host='localhost', port=6379, decode_responses=True)

def md5(s): return hashlib.md5(s.encode()).hexdigest()

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

fish_data = load_json(FISH_DATA)
item_data = load_json(ITEM_DATA)
gacha_data = load_json(GACHA_DATA)

class DictRedisData:
    def __init__(self, key, default):
        self.key = key
        val = redis_global.get(key)
        self.data = default if val is None else json.loads(val)
    def save(self):
        redis_global.set(self.key, json.dumps(self.data))

class FishPlayer(DictRedisData):
    def __init__(self, qq):
        super().__init__(f"fish_user_{md5(str(qq))}", {
            'level':1,'exp':0,'gold':0,'score':0,
            'bag':item_data[:1],'buff':[]
        })
        self.qq = str(qq)
    def refresh_buff(self):
        now = time.time()
        self.data['buff'] = [b for b in self.data['buff'] if (b.get('time',1)>0) and (b.get('expire',0)==0 or b['expire']>now)]
    @property
    def power(self):
        p = self.data['level']
        for it in self.data['bag']:
            if it.get('equipped'): p += it.get('power', 0)
        return p

class FishGame(DictRedisData):
    def __init__(self, group):
        super().__init__(f"fish_group_{group}", {'fish_log':[], 'buff':[], 'day':0, 'feed_time':0})
        self.group = group
        self.current_fish = None
        self.try_list = []
        self.leave_time = 0
    def save(self): super().save()
    def refresh_buff(self):
        now = time.time()
        self.data['buff'] = [b for b in self.data['buff'] if (b.get('time',1)>0) and (b.get('expire',0)==0 or b['expire']>now)]
    def spawn_fish(self):
        # TODO: 实现鱼的生成
        return None
    def count_down(self):
        # TODO: 实现倒计时
        pass
    def catch(self, player: FishPlayer):
        # TODO: 实现捕获逻辑
        return {'message':'功能未完成'}
    def gacha(self, player: FishPlayer, ten:bool):
        # TODO: 实现抽卡
        return {'message':'功能未完成'}
    def shop(self):
        return item_data
    def buy(self, player: FishPlayer, idx:int):
        # TODO: 实现购买
        return {'message':'功能未完成'}
    def use_item(self, player: FishPlayer, idx:int):
        # TODO: 实现使用道具
        return {'message':'功能未完成'}
    def status(self):
        # TODO: 实现状态展示
        return '状态功能未完成'

async def fetch_avatar(qq, size=80):
    avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq}&s={size}"
    async with aiohttp.ClientSession() as session:
        resp = await session.get(avatar_url)
        resp.raise_for_status()
        data = await resp.read()
    img = Image.open(BytesIO(data)); img.load(); return img

# 定时任务：每分钟尝试刷鱼
@scheduler.scheduled_job('cron', minute='*')
async def spawn_task():
    # TODO: 获取所有群列表，并调用 spawn_fish 和 count_down
    pass

@register(__plugin_name__, "Koikokokokoro", "参考Diving-Fish/Chiyuki-Bot捕鱼功能制作的Astrbot钓鱼插件", __version__)
class Fishing(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info(f"插件 {__plugin_name__} 初始化完成")

    @filter.command("面板")
    async def panel(self, event: AstrMessageEvent):
        player = FishPlayer(event.get_sender_id())
        player.refresh_buff()
        avatar = await fetch_avatar(event.get_sender_id())
        # TODO: 调用绘图函数 create_character_panel
        yield event.plain_result("面板功能未完成")

    @filter.command("背包")
    async def bag(self, event: AstrMessageEvent):
        # TODO: 展示背包
        yield event.plain_result("背包功能未完成")

    @filter.command("捕鱼")
    async def catch_cmd(self, event: AstrMessageEvent):
        game = FishGame(event.get_group_id())
        player = FishPlayer(event.get_sender_id())
        res = game.catch(player)
        yield event.plain_result(res['message'])

    @filter.command("单抽")
    async def draw_one(self, event: AstrMessageEvent):
        player = FishPlayer(event.get_sender_id())
        game = FishGame(event.get_group_id())
        res = game.gacha(player, False)
        yield event.plain_result(res.get('message',''))

    @filter.command("十连")
    async def draw_ten(self, event: AstrMessageEvent):
        player = FishPlayer(event.get_sender_id())
        game = FishGame(event.get_group_id())
        res = game.gacha(player, True)
        yield event.plain_result(res.get('message',''))

    @filter.command("商店")
    async def shop_cmd(self, event: AstrMessageEvent):
        items = FishGame(event.get_group_id()).shop()
        yield event.plain_result(f"商店物品: {[i['name'] for i in items]}")

    @filter.command("商店购买")
    async def buy_cmd(self, event: AstrMessageEvent, num: int):
        player = FishPlayer(event.get_sender_id())
        game = FishGame(event.get_group_id())
        res = game.buy(player, num)
        yield event.plain_result(res.get('message',''))

    @filter.command("使用")
    async def use_cmd(self, event: AstrMessageEvent, num: int):
        player = FishPlayer(event.get_sender_id())
        game = FishGame(event.get_group_id())
        res = game.use_item(player, num)
        yield event.plain_result(res.get('message',''))

    @filter.command("状态")
    async def status_cmd(self, event: AstrMessageEvent):
        msg = FishGame(event.get_group_id()).status()
        yield event.plain_result(msg)

    async def terminate(self):
        logger.info(f"插件 {__plugin_name__} 已停用")
