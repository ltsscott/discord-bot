import discord
from discord.ext import commands, tasks
import datetime
import sqlite3
import random
import os
from keep_alive import keep_alive

USER_ID = 770287150645116938

# ----------------------
# INTENTS
# ----------------------

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------
# DATABASE
# ----------------------

conn = sqlite3.connect("everflow.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS character (
 id INTEGER PRIMARY KEY,
 level INTEGER,
 xp INTEGER,
 awareness INTEGER,
 discipline INTEGER,
 growth INTEGER,
 balance INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS meta (
 key TEXT PRIMARY KEY,
 value TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS streak (
 id INTEGER PRIMARY KEY,
 current_streak INTEGER,
 longest_streak INTEGER,
 weak_days INTEGER,
 last_check TEXT,
 energy INTEGER,
 daily_actions INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shadow (
 id INTEGER PRIMARY KEY,
 shadow_level INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS decision_memory (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 date TEXT,
 time_block TEXT,
 action TEXT
)
""")

# ⭐ PRESENCE MEMORY TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS presence (
 id INTEGER PRIMARY KEY,
 last_action TEXT
)
""")

# ⭐ JOURNAL TABLE (ADDED)
cursor.execute("""
CREATE TABLE IF NOT EXISTS journal (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 date TEXT,
 entry TEXT
)
""")

# initialize rows
if cursor.execute("SELECT * FROM character WHERE id=1").fetchone() is None:
    cursor.execute("INSERT INTO character VALUES (1,1,0,0,0,0,0)")

if cursor.execute("SELECT * FROM streak WHERE id=1").fetchone() is None:
    cursor.execute("INSERT INTO streak VALUES (1,0,0,0,'',0,0)")

if cursor.execute("SELECT * FROM shadow WHERE id=1").fetchone() is None:
    cursor.execute("INSERT INTO shadow VALUES (1,0)")

if cursor.execute("SELECT * FROM presence WHERE id=1").fetchone() is None:
    cursor.execute("INSERT INTO presence VALUES (1,'')")

conn.commit()

# ----------------------
# ⭐ JOURNAL COMMAND (ADDED)
# ----------------------


@bot.command()
async def journal(ctx, *, text):
    today = datetime.date.today().isoformat()

    cursor.execute("INSERT INTO journal (date,entry) VALUES (?,?)",
                   (today, text))
    conn.commit()

    await ctx.send("📝 Entry recorded.")


# ----------------------
# ⭐ PRESENCE SYSTEM
# ----------------------


def update_presence():
    now = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE presence SET last_action=? WHERE id=1", (now, ))
    conn.commit()


def presence_message():

    row = cursor.execute(
        "SELECT last_action FROM presence WHERE id=1").fetchone()[0]

    if not row:
        return None

    last = datetime.datetime.fromisoformat(row)
    diff = (datetime.datetime.now() - last).total_seconds()

    if diff > 21600:
        return "You return to the current after a long quiet."
    elif diff > 7200:
        return "The current grew quiet for a while."
    elif diff < 900:
        return "The rhythm remains unbroken."

    return None


# ----------------------
# DECISION MEMORY
# ----------------------


def log_decision(time_block, action):
    today = datetime.date.today().isoformat()
    cursor.execute(
        "INSERT INTO decision_memory (date,time_block,action) VALUES (?,?,?)",
        (today, time_block, action))
    conn.commit()


def analyze_today():

    today = datetime.date.today().isoformat()

    rows = cursor.execute(
        """
        SELECT action FROM decision_memory
        WHERE date=?
    """, (today, )).fetchall()

    if not rows:
        return None

    counts = {"💪": 0, "📘": 0, "⚔️": 0, "🌿": 0, "❌": 0}

    for r in rows:
        if r[0] in counts:
            counts[r[0]] += 1

    observations = []

    if counts["💪"] >= 3:
        observations.append("The body was answered with consistency.")
    if counts["📘"] >= 3:
        observations.append("The mind was returned to often.")
    if counts["❌"] >= 3:
        observations.append("Avoidance appeared repeatedly.")
    if counts["🌿"] >= 3:
        observations.append("Balance was quietly protected.")
    if counts["⚔️"] >= 3:
        observations.append("Skill refinement shaped the day.")

    if not observations:
        observations.append("The day moved without a dominant pattern.")

    return random.choice(observations)


def personality_reflection():

    today = datetime.date.today().isoformat()

    rows = cursor.execute("SELECT action FROM decision_memory WHERE date=?",
                          (today, )).fetchall()

    if not rows:
        return None

    counts = {"💪": 0, "📘": 0, "⚔️": 0, "🌿": 0, "❌": 0}

    for r in rows:
        if r[0] in counts:
            counts[r[0]] += 1

    if counts["💪"] >= 4:
        state = "high_discipline"
    elif counts["📘"] >= 4:
        state = "mental_focus"
    elif counts["⚔️"] >= 3:
        state = "skill_growth"
    elif counts["🌿"] >= 3:
        state = "balanced_state"
    elif counts["❌"] >= 4:
        state = "avoidance_pattern"
    else:
        state = "low_momentum"

    return random.choice(personality_voice[state])


# ----------------------
# WEEKLY ANALYTICS
# ----------------------


def weekly_summary():

    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    rows = cursor.execute(
        """
        SELECT action FROM decision_memory
        WHERE date>=?
    """, (week_ago, )).fetchall()

    if not rows:
        return None

    counts = {"💪": 0, "📘": 0, "⚔️": 0, "🌿": 0, "❌": 0}

    for r in rows:
        if r[0] in counts:
            counts[r[0]] += 1

    dominant = max(counts, key=counts.get)

    mapping = {
        "💪": "Physical discipline dominated the week.",
        "📘": "Mental growth led the week.",
        "⚔️": "Skill refinement defined progress.",
        "🌿": "Balance guided decisions.",
        "❌": "Avoidance appeared frequently."
    }

    return "📊 Weekly Pattern:\n" + mapping[dominant]


# ----------------------
# ⭐ AI INNER VOICE SYSTEM (ADDED)
# ----------------------

ai_voice = {
    "focused": [
        "Attention sharpens through repetition.",
        "Consistency quietly reshapes identity.",
        "The path grows clearer through action."
    ],
    "balanced":
    ["Effort and recovery remain aligned.", "The rhythm feels sustainable."],
    "drifting": [
        "Momentum softens but has not vanished.",
        "Small corrections restore direction."
    ]
}


def ai_reflection():

    today = datetime.date.today().isoformat()

    rows = cursor.execute("SELECT action FROM decision_memory WHERE date=?",
                          (today, )).fetchall()

    if not rows:
        return None

    counts = {"💪": 0, "📘": 0, "⚔️": 0, "🌿": 0, "❌": 0}

    for r in rows:
        if r[0] in counts:
            counts[r[0]] += 1

    if counts["❌"] >= 4:
        state = "drifting"
    elif counts["🌿"] >= 3:
        state = "balanced"
    else:
        state = "focused"

    return random.choice(ai_voice[state])


# ----------------------
# TITLE SYSTEM
# ----------------------


def get_title(level):
    if level <= 2: return "🌱 Flow Initiate"
    elif level <= 5: return "🧭 Path Walker"
    elif level <= 9: return "⚔ Discipline Builder"
    elif level <= 14: return "🌊 Flow Adept"
    elif level <= 24: return "🔥 Momentum Keeper"
    elif level <= 39: return "🜂 Self Architect"
    else: return "🌌 Everflow Ascendant"


# ----------------------
# LEVEL MILESTONES
# ----------------------

milestones = {
    5: "The path is no longer accidental.",
    10: "Discipline begins to outlive motivation.",
    15: "Identity bends toward consistency.",
    20: "Momentum becomes self-sustaining.",
    30: "The self is being rebuilt deliberately.",
    50: "Action and intention move as one."
}


def milestone_text(level):
    return milestones.get(level, None)


# ----------------------
# SHADOW SYSTEM
# ----------------------


def get_shadow():
    return cursor.execute(
        "SELECT shadow_level FROM shadow WHERE id=1").fetchone()[0]


def add_shadow(amount=1):
    level = min(100, get_shadow() + amount)
    cursor.execute("UPDATE shadow SET shadow_level=? WHERE id=1", (level, ))
    conn.commit()


def reduce_shadow(amount=2):
    level = max(0, get_shadow() - amount)
    cursor.execute("UPDATE shadow SET shadow_level=? WHERE id=1", (level, ))
    conn.commit()


def shadow_state(value):
    if value < 20: return "Faint"
    elif value < 50: return "Stirring"
    elif value < 80: return "Rising"
    elif value < 95: return "Heavy"
    else: return "Overwhelming"


def shadow_multiplier():
    s = get_shadow()
    if s < 20: return 1.0
    elif s < 50: return 0.85
    elif s < 80: return 0.65
    else: return 0.40


# ----------------------
# OUTCOME ENGINE
# ----------------------

outcomes = {
    "positive": [
        "The current strengthens.", "Momentum gathers quietly.",
        "The path grows clearer.", "Flow deepens beneath the surface.",
        "A small victory settles into place."
    ],
    "shadow_reduce": [
        "Shadow loosens its grip.", "Light returns to the current.",
        "Resistance fades slightly.", "The weight of hesitation lifts."
    ],
    "neutral": [
        "The moment passes softly.", "Stillness leaves no mark.",
        "The current neither rises nor falls."
    ]
}


def build_outcome_text(emoji):

    if emoji == "❌":
        return random.choice(outcomes["neutral"])

    text = random.choice(outcomes["positive"])

    if random.random() < 0.5:
        text += "\n" + random.choice(outcomes["shadow_reduce"])

    return text


# ----------------------
# ⭐ PERSONALITY VOICE LINES
# ----------------------

personality_voice = {
    "high_discipline": [
        "Action repeated becomes identity.",
        "You did not negotiate with resistance today.",
        "Momentum is no longer accidental.",
        "Discipline is beginning to automate itself.",
        "Consistency compounds silently."
    ],
    "mental_focus": [
        "Attention returned where it mattered.",
        "Clarity grows through deliberate thought.",
        "You trained the mind instead of escaping it.",
        "Understanding deepened today.", "Focus sharpened through effort."
    ],
    "skill_growth": [
        "Refinement happened beneath the surface.",
        "Skill advances quietly before it becomes visible.",
        "Repetition shaped ability today.",
        "Progress hid inside small corrections.", "Mastery favors patience."
    ],
    "balanced_state": [
        "Effort and recovery stayed aligned.", "Balance prevented burnout.",
        "You sustained the rhythm instead of forcing it.",
        "Stability is progress too.", "Energy was protected wisely."
    ],
    "low_momentum": [
        "The current slowed but never vanished.",
        "Even imperfect movement prevents stagnation.",
        "Small returns rebuild direction.",
        "Momentum waits for your next action.", "The path remains open."
    ],
    "avoidance_pattern": [
        "Resistance spoke loudly today.",
        "Awareness notices hesitation without judgment.",
        "Avoidance reveals where growth hides.",
        "The system waits for re-engagement.",
        "Stillness can become intention again."
    ]
}

# ----------------------
# ⭐ STEP 4 — PERSONALITY VOICE LINES (EXPANDED)
# ----------------------

personality_voice = {
    "high_discipline": [
        "Action repeated becomes identity.",
        "You did not negotiate with resistance today.",
        "Momentum is no longer accidental.",
        "Discipline is beginning to automate itself.",
        "Consistency compounds silently."
    ],
    "mental_focus": [
        "Attention returned where it mattered.",
        "Clarity grows through deliberate thought.",
        "You trained the mind instead of escaping it.",
        "Understanding deepened today.", "Focus sharpened through effort."
    ],
    "skill_growth": [
        "Refinement happened beneath the surface.",
        "Skill advances quietly before it becomes visible.",
        "Repetition shaped ability today.",
        "Progress hid inside small corrections.", "Mastery favors patience."
    ],
    "balanced_state": [
        "Effort and recovery stayed aligned.", "Balance prevented burnout.",
        "You sustained the rhythm instead of forcing it.",
        "Stability is progress too.", "Energy was protected wisely."
    ],
    "low_momentum": [
        "The current slowed but never vanished.",
        "Even imperfect movement prevents stagnation.",
        "Small returns rebuild direction.",
        "Momentum waits for your next action.", "The path remains open."
    ],
    "avoidance_pattern": [
        "Resistance spoke loudly today.",
        "Awareness notices hesitation without judgment.",
        "Avoidance reveals where growth hides.",
        "The system waits for re-engagement.",
        "Stillness can become intention again."
    ]
}

# ----------------------
# STREAK SYSTEM
# ----------------------


def get_streak():
    return cursor.execute("SELECT * FROM streak WHERE id=1").fetchone()


def add_daily_action():
    cursor.execute(
        "UPDATE streak SET daily_actions=daily_actions+1 WHERE id=1")
    conn.commit()


def evaluate_day_if_needed():

    today = datetime.date.today().isoformat()
    _, streak, longest, weak, last_check, energy, actions = get_streak()

    if last_check == today:
        return None

    if actions >= 6:
        streak += 1
        weak = 0
        energy = min(100, energy + 10)
        longest = max(longest, streak)
        message = "🌊 The current flows steadily.\nScott honored the path today."

    elif actions >= 1:
        weak += 1
        energy = max(0, energy - 5)

        if weak >= 2:
            streak = 0
            weak = 0
            message = "🌑 The current has stilled.\nThe river begins again."
        else:
            message = "⚠️ The current weakens.\nOne drifting day is forgiven."
    else:
        streak = 0
        weak = 0
        energy = max(0, energy - 15)
        message = "🌑 Silence filled the day."

    cursor.execute(
        """
    UPDATE streak
    SET current_streak=?,longest_streak=?,weak_days=?,
        last_check=?,energy=?,daily_actions=0
    WHERE id=1
    """, (streak, longest, weak, today, energy))

    conn.commit()
    return message


# ----------------------
# CHARACTER HELPERS
# ----------------------


def get_character():
    return cursor.execute("SELECT * FROM character WHERE id=1").fetchone()


def xp_needed(level):
    return 50 + (level * 25)


def bar(value):
    filled = min(10, int(value / 2))
    return "█" * filled + "░" * (10 - filled)


# ----------------------
# CHARACTER SHEET
# ----------------------


def build_character_sheet():

    _, lvl, xp, aw, dis, gro, bal = get_character()
    _, streak, longest, _, _, energy, _ = get_streak()
    shadow = get_shadow()

    return ("🌊 **EVERFLOW — Character State**\n\n"
            f"Name: Scott\n"
            f"Title: {get_title(lvl)}\n"
            f"Level: {lvl}\n"
            f"XP: {xp}/{xp_needed(lvl)}\n\n"
            f"🔥 Streak: {streak} days\n"
            f"🏆 Longest Streak: {longest} days\n"
            f"🌊 Flow Energy: {energy}%\n"
            f"🌒 Shadow: {shadow}% ({shadow_state(shadow)})\n\n"
            f"🧠 Awareness\n{bar(aw)} {aw}\n\n"
            f"💪 Discipline\n{bar(dis)} {dis}\n\n"
            f"⚔ Growth\n{bar(gro)} {gro}\n\n"
            f"🌿 Balance\n{bar(bal)} {bal}")


async def update_character_sheet():

    result = cursor.execute(
        "SELECT value FROM meta WHERE key='sheet_id'").fetchone()

    if not result: return

    guild = bot.guilds[0]
    channel = discord.utils.get(guild.text_channels, name="character-sheet")

    msg = await channel.fetch_message(int(result[0]))
    await msg.edit(content=build_character_sheet())


# ----------------------
# REWARD SYSTEM
# ----------------------


async def apply_rewards(emoji):

    stats = {
        "💪": {
            "xp": 6,
            "discipline": 2,
            "growth": 1
        },
        "📘": {
            "xp": 5,
            "awareness": 2,
            "growth": 1
        },
        "⚔️": {
            "xp": 7,
            "growth": 3,
            "discipline": 1
        },
        "🌿": {
            "xp": 1,
            "balance": 1
        },
        "❌": {
            "xp": 0
        }
    }[emoji]

    _, lvl, xp, aw, dis, gro, bal = get_character()

    add_daily_action()
    reduce_shadow(2)

    mult = shadow_multiplier()
    xp_gain = int(stats.get("xp", 0) * mult)

    xp += xp_gain
    aw += stats.get("awareness", 0)
    dis += stats.get("discipline", 0)
    gro += stats.get("growth", 0)
    bal += stats.get("balance", 0)

    leveled = False
    milestone = None

    need = xp_needed(lvl)

    if xp >= need:
        xp -= need
        lvl += 1
        leveled = True
        milestone = milestone_text(lvl)

    cursor.execute(
        """
    UPDATE character
    SET level=?,xp=?,awareness=?,discipline=?,growth=?,balance=?
    WHERE id=1
    """, (lvl, xp, aw, dis, gro, bal))

    conn.commit()
    await update_character_sheet()

    stats["xp"] = xp_gain

    return leveled, lvl, stats, milestone


# ----------------------
# EVENTS + REACTIONS
# ----------------------

schedule = {
    "07:00": ("Morning begins quietly.", ["💪", "📘", "🌿", "❌"]),
    "07:30": ("Stillness returns.", ["🌿", "📘", "❌"]),
    "08:30": ("Words wait patiently.", ["📘", "🌿", "❌"]),
    "09:00": ("The market opens.", ["⚔️", "📘", "❌"]),
    "11:00": ("The body asks to be challenged.", ["💪", "🌿", "❌"]),
    "12:30": ("Pause. Breathe.", ["🌿", "❌"]),
    "14:00": ("Patterns reveal themselves.", ["⚔️", "📘", "❌"]),
    "15:00": ("Refinement through repetition.", ["⚔️", "📘", "❌"]),
    "16:00": ("Motion restores clarity.", ["💪", "🌿", "❌"]),
    "18:00": ("The day softens.", ["🌿", "❌"]),
    "18:30": ("What you build shapes tomorrow.", ["⚔️", "📘", "💪", "❌"]),
    "22:00": ("Look back gently.", ["📘", "🌿", "❌"])
}

labels = {
    "💪": "Train Body",
    "📘": "Sharpen Mind",
    "⚔️": "Refine Skill",
    "🌿": "Maintenance",
    "❌": "Let the moment pass"
}

active_events = {}


async def send_event(channel, text, emojis):

    opts = "\n".join(f"{e} {labels[e]}" for e in emojis)

    msg = await channel.send(
        f"<@{USER_ID}>\n🌊 **EVERFLOW — Decision Moment**\n\n"
        f"{text}\n\n**What will Scott do?**\n\n{opts}")

    active_events[msg.id] = {"time": datetime.datetime.now(), "block": text}

    for e in emojis:
        await msg.add_reaction(e)


@bot.event
async def on_reaction_add(reaction, user):

    if user.bot: return
    if reaction.message.author != bot.user: return

    emoji = str(reaction.emoji)
    if emoji not in labels: return

    event_data = active_events.get(reaction.message.id)
    if event_data:
        log_decision(event_data["block"], emoji)

    presence_line = presence_message()
    update_presence()

    leveled, new_level, stats, milestone = await apply_rewards(emoji)

    outcome_text = build_outcome_text(emoji)

    message = ("✨ Scott chose a path.\n\n"
               f"+{stats['xp']} XP\n\n"
               f"{outcome_text}")

    if presence_line:
        message += f"\n\n{presence_line}"

    await reaction.message.channel.send(message)

    if milestone:
        guild = bot.guilds[0]
        ch = discord.utils.get(guild.text_channels, name="level-ups")
        if ch:
            await ch.send(
                f"🌊 **Milestone Reached — Level {new_level}**\n\n{milestone}")


# ----------------------
# LOOPS
# ----------------------


@tasks.loop(minutes=5)
async def shadow_check():
    now = datetime.datetime.now()
    for msg_id, data in list(active_events.items()):
        if (now - data["time"]).total_seconds() > 1800:
            add_shadow(1)
            del active_events[msg_id]


@tasks.loop(minutes=10)
async def daily_eval():
    result = evaluate_day_if_needed()
    if result:
        guild = bot.guilds[0]
        ch = discord.utils.get(guild.text_channels, name="level-ups")
        if ch:
            await ch.send(result)
        await update_character_sheet()


@tasks.loop(hours=24)
async def observer_loop():
    observation = analyze_today()
    if observation:
        guild = bot.guilds[0]
        ch = discord.utils.get(guild.text_channels, name="level-ups")
        if ch:
            await ch.send("👁 **The Observer Speaks**\n\n" + observation)


# ⭐ AI DAILY REFLECTION LOOP
@tasks.loop(hours=24)
async def ai_daily_reflection():

    reflection = personality_reflection()

    if reflection:
        guild = bot.guilds[0]
        ch = discord.utils.get(guild.text_channels, name="level-ups")
        if ch:
            await ch.send("🧠 **Inner Voice**\n\n" + reflection)


# ⭐ WEEKLY REPORT LOOP
@tasks.loop(hours=168)
async def weekly_report():

    report = weekly_summary()

    if report:
        guild = bot.guilds[0]
        ch = discord.utils.get(guild.text_channels, name="level-ups")
        if ch:
            await ch.send(report)


@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.datetime.now().strftime("%H:%M")
    if now in schedule:
        guild = bot.guilds[0]
        ch = discord.utils.get(guild.text_channels, name="active-decision")
        if ch:
            text, emojis = schedule[now]
            await send_event(ch, text, emojis)


# ----------------------
# READY
# ----------------------


@bot.event
async def on_ready():

    print(f"Everflow awake as {bot.user}")

    guild = bot.guilds[0]
    channel = discord.utils.get(guild.text_channels, name="character-sheet")

    if cursor.execute(
            "SELECT value FROM meta WHERE key='sheet_id'").fetchone() is None:

        msg = await channel.send(build_character_sheet())
        cursor.execute("INSERT INTO meta VALUES ('sheet_id',?)",
                       (str(msg.id), ))
        conn.commit()

    await update_character_sheet()

    scheduler.start()
    daily_eval.start()
    shadow_check.start()
    observer_loop.start()
    ai_daily_reflection.start()
    weekly_report.start()


TOKEN = os.getenv("TOKEN")
keep_alive()
bot.run(TOKEN)
