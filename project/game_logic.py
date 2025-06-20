import random

matchmaking_queue = []
games = {}

def create_new_game_state():
    """建立一個新的、乾淨的遊戲狀態物件"""
    return {
        'players': {},          # key: player_id
        'player_order': [],     # 儲存 player_id 的順序
        'turn_index': 0,
        'board_size': 30,
        'status': 'lobby',      # 狀態: lobby, playing, finished
        'host_id': None,        # 房主的 player_id
        'winner': None,
        'used_sentences': set(),
        'player_sids': {}       # 映射: sid -> player_id
    }

# 遊戲中使用的常數 (不變)
GRAMMAR_QUESTIONS = [
    {"rule": "過去簡單式 (S + V-ed)", "prompt": "請用一個完整的句子，描述你「上週末」做的「一件」具體事情。"},
    {"rule": "過去進行式 (S + was/were + Ving)", "prompt": "請用一個完整的句子，描述「昨天晚上八點整」的時候，你「正在」做什麼？"},
    {"rule": "過去完成式 (S + had + p.p.)", "prompt": "請用一個完整的句子，描述一件你在「昨天上床睡覺之前」，就「已經完成」了的事情。"},
    {"rule": "過去完成進行式 (S + had been + Ving)", "prompt": "想像你昨天等了很久的公車。請用一個句子描述「在公車終於來之前」，你「一直持續在做」的感覺或動作。"}
]
CHANCE_CARDS = [
    {'type': 'move_relative', 'value': 2, 'text': '搭上順風車，前進 2 格！'},
    {'type': 'move_relative', 'value': 4, 'text': '靈感爆發，一口氣前進 4 格！'}
]
DESTINY_CARDS = [
    {'type': 'move_relative', 'value': -2, 'text': '踩到香蕉皮，滑退 2 格。'},
    {'type': 'swap_position_leader', 'text': '發動次元轉換，與目前的第一名玩家交換位置！'}
]

def get_random_question():
    return random.choice(GRAMMAR_QUESTIONS)