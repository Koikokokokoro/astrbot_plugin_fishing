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

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api import scheduler

# -- 配置 --
__plugin_name__ = "捕鱼大亨"
__version__ = "0.0.2"
DATA_DIR = os.path.join(os.getcwd(), "data", "plugins", "fishing_tycoon")
os.makedirs(DATA_DIR, exist_ok=True)
FISH_DATA = os.path.join(DATA_DIR, "fish_data.json")
ITEM_DATA = os.path.join(DATA_DIR, "fish_item.json")
GACHA_DATA = os.path.join(DATA_DIR, "gacha.json")
PLAYER_DIR = os.path.join(DATA_DIR, "players")
GROUP_DIR = os.path.join(DATA_DIR, "groups")
os.makedirs(PLAYER_DIR, exist_ok=True)
os.makedirs(GROUP_DIR, exist_ok=True)

# 加载静态数据
def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []
fish_data = load_json(FISH_DATA)
item_data = load_json(ITEM_DATA)
gacha_data = load_json(GACHA_DATA)

# 工具
def md5(s): return hashlib.md5(s.encode()).hexdigest()

def buff_available(buff):
    expire = buff.get('expire', 0)
    times = buff.get('time', 999)
    return times > 0 and (expire == 0 or expire > time.time())

# 玩家持久化
class FishPlayer:
    def __init__(self, qq):
        self.qq = str(qq)
        self.file = os.path.join(PLAYER_DIR, f"{self.qq}.json")
        self.data = {
            'name':'渔者','level':1,'exp':0,'gold':0,'score':0,
            'fish_log':[],'bag':item_data[:1],'buff':[]
        }
        if os.path.exists(self.file):
            try:
                self.data = json.load(open(self.file,'r',encoding='utf-8'))
            except:
                pass
    def save(self):
        json.dump(self.data, open(self.file,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    def refresh_buff(self):
        now = time.time()
        self.data['buff'] = [b for b in self.data['buff'] if buff_available(b)]
    @property
    def power(self):
        p = self.data['level']
        for it in self.data['bag']:
            if it.get('equipped'): p += it.get('power', 0)
        return p

# 群组持久化
class FishGame:
    def __init__(self, group):
        self.group = str(group)
        self.file = os.path.join(GROUP_DIR, f"{self.group}.json")
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
        json.dump(self.data, open(self.file,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    def refresh_buff(self):
        now = time.time()
        self.data['buff'] = [b for b in self.data['buff'] if buff_available(b)]
    # TODO: 实现 spawn_fish(), count_down(), catch(), gacha(), shop(), buy(), use_item(), status()

# 异步获取 QQ 头像
def fetch_avatar(qq, size=80):
    async def _inner():
        url=f'https://q1.qlogo.cn/g?b=qq&nk={qq}&s={size}'
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url); resp.raise_for_status()
            data = await resp.read()
        img = Image.open(BytesIO(data)); img.load(); return img
    return _inner()

# 图像面板示例（可用前述代码替换）
def create_character_panel(player, avatar):
    img = Image.new('RGB', (800,600), (40,42,54))
    # TODO: 绘制面板
    return img

def image_to_base64(img):
    buf = BytesIO(); img.save(buf,'PNG');
    return base64.b64encode(buf.getvalue()).decode()

# 定时任务：每分钟尝试刷鱼
@scheduler.scheduled_job('cron', minute='*')
async def spawn_task():
    # TODO: 遍历群组文件spawn/count_down并发送消息
    pass

@register(__plugin_name__, "Koikokokokoro", "参考Diving-Fish/Chiyuki-Bot捕鱼功能制作的Astrbot钓鱼插件", __version__)
class Fishing(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info(f"插件 {__plugin_name__} v{__version__} 初始化完成")

    @filter.command("面板")
    async def panel(self, event: AstrMessageEvent):
        player = FishPlayer(event.get_sender_id())
        player.refresh_buff(); player.save()
        avatar = await fetch_avatar(event.get_sender_id())
        img = create_character_panel(player, avatar)
        yield event.chain_result([Comp.Image.fromBase64(image_to_base64(img))])

    @filter.command("背包")
    async def bag(self, event: AstrMessageEvent):
        # TODO: 调用 create_inventory_panel
        yield event.plain_result("背包功能未完成")

    @filter.command("捕鱼")
    async def catch_cmd(self, event: AstrMessageEvent):
        game = FishGame(event.get_group_id()); game.refresh_buff(); game.save()
        player = FishPlayer(event.get_sender_id()); player.refresh_buff(); player.save()
        res = game.catch(player)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("单抽")
    async def draw_one(self, event: AstrMessageEvent):
        player = FishPlayer(event.get_sender_id()); player.save()
        game = FishGame(event.get_group_id()); game.save()
        res = game.gacha(player, False)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("十连")
    async def draw_ten(self, event: AstrMessageEvent):
        player = FishPlayer(event.get_sender_id()); player.save()
        game = FishGame(event.get_group_id()); game.save()
        res = game.gacha(player, True)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("商店")
    async def shop_cmd(self, event: AstrMessageEvent):
        items = FishGame(event.get_group_id()).shop()
        yield event.plain_result(f"商店物品: {[i['name'] for i in items]}")

    @filter.command("商店购买")
    async def buy_cmd(self, event: AstrMessageEvent, num: int):
        player = FishPlayer(event.get_sender_id()); player.save()
        game = FishGame(event.get_group_id())
        res = game.buy(player, num)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("使用")
    async def use_cmd(self, event: AstrMessageEvent, num: int):
        player = FishPlayer(event.get_sender_id()); player.save()
        game = FishGame(event.get_group_id())
        res = game.use_item(player, num)
        yield event.plain_result(res.get('message','功能未完成'))

    @filter.command("状态")
    async def status_cmd(self, event: AstrMessageEvent):
        msg = FishGame(event.get_group_id()).status()
        yield event.plain_result(msg)

    async def terminate(self):
        logger.info(f"插件 {__plugin_name__} 已停用")
