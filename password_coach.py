"""
password_coach_cheatsheet.py - PRESENTER COPY of the password coach agent.

The code is identical to password_coach.py. Only the comments are new.

Run:   python password_coach_cheatsheet.py     (Mac/Linux: python3 ...)
Stop:  type quit
"""

# =============================================================================
# THE BIG IDEA (say this before typing anything)
# =============================================================================
#
#   AGENT  =  MODEL  +  TOOLS  +  LOOP
#
#   MODEL  The AI. Ollama runs it on this laptop. It can only read and write
#          text. It cannot run code or count reliably.
#   TOOLS  Plain Python functions that WE write. They do the real work.
#   LOOP   Our code asks the model "what next?", runs the tool it picks,
#          hands back the result, and asks again until the model is done.
#
#   The model never runs a tool. It only ASKS for one. Our code runs it.
#
# =============================================================================
# SUGGESTED ORDER FOR LIVE CODING
# =============================================================================
#
#   1. Imports and MODEL
#   2. check_strength          (run it by hand first: print(check_strength("abc")))
#   3. PROMPT, TOOLS, messages
#   4. The loop                (now it is an agent with one tool)
#   5. is_common               (add the function, add its name to TOOLS)
#   6. make_password           (same two edits. Now the model has real choices)
#
#   Adding a tool is always the same two edits: write the function, then add
#   its name to the TOOLS line. Nothing in the loop changes.
#
# =============================================================================
# IF IT BREAKS ON STAGE
# =============================================================================
#
#   model 'llama3.2' not found      ->  ollama pull llama3.2
#   Failed to connect to Ollama     ->  Ollama is not running. Open the Ollama app.
#   No module named 'ollama'        ->  pip install ollama
#   First answer is very slow       ->  Normal. The model is loading. Wait.
#   Model answers without any tool  ->  Ask again, or be more direct:
#                                       "Use your tools to check Summer2026!"
#
# =============================================================================

# secrets: picks random characters in a way that is safe for passwords.
#          SAY: never use the "random" module for passwords. It is predictable.
# string:  ready-made lists of characters, like all letters and all digits.
# chat:    the one function we need from Ollama. It sends messages to the model.
import secrets
import string
from ollama import chat

# Which model to use. It must be downloaded first:  ollama pull llama3.2
# To try another model, change only this line.
MODEL = "llama3.2"

# -----------------------------------------------------------------------------
# THE PROMPT (does not count toward the 50 lines)
# -----------------------------------------------------------------------------
# This is the system prompt: standing instructions the model reads before every
# answer. It sets the job, tells the model to use tools and not guess, and
# gives the rule for strong vs weak so the verdict is consistent.
#
# SAY: the prompt is where we tell the model WHEN to use tools.
#      The code is where we decide WHAT the tools do.
PROMPT = """You are a password coach for students who are new to cybersecurity.

You cannot judge a password by looking at it. Never guess its length or strength.
Use your tools to get the facts, then explain them.

- To judge a password, call check_strength and is_common with the exact password.
- To create a password, call make_password. Never invent one yourself.

A password is strong when it has at least 12 characters, uses at least 3 of the
4 character types, and is not common. Otherwise it is weak.

Answer in two or three short, plain sentences. Say strong or weak, and why."""

# Our tiny "bad password" list. is_common looks passwords up in here.
# DEMO: ask "Is hunter2 common?" (it says no), add "hunter2" here, run again.
#       The agent only knows what its tools know.
COMMON = {"password", "123456", "qwerty", "letmein", "iloveyou", "admin", "welcome1", "password1"}


# =============================================================================
# TOOLS: three plain Python functions
# =============================================================================
# Two things in each function are read by the MODEL, not only by people:
#
#   1. The type hints      (password: str)  tell the model what to pass in.
#   2. The docstring       ("""...""")      tells the model what the tool is for.
#
# The ollama package turns those into a tool description for us.
# A vague docstring means the model picks the wrong tool. Write them clearly.
#
# Every tool returns a short string. That string goes back to the model.


# TOOL 1: check_strength
# What it does:  measures a password. It does not judge it.
# Takes:         the password, as text
# Gives back:    for example "length 11, uses 4 of 4 character types"
# Why a tool:    language models are bad at counting characters. Python is not.
def check_strength(password: str) -> str:
    """Measure a password: its length and how many character types it uses."""
    # Four yes/no questions about the password. Each line is True or False.
    # "any(...)" means: is this true for at least one character?
    types = [
        any(c.islower() for c in password),      # has a lowercase letter?
        any(c.isupper() for c in password),      # has an uppercase letter?
        any(c.isdigit() for c in password),      # has a digit?
        any(not c.isalnum() for c in password),  # has a symbol (not letter, not digit)?
    ]
    # len() counts the characters. sum() counts the Trues (True counts as 1).
    return f"length {len(password)}, uses {sum(types)} of 4 character types"


# TOOL 2: is_common
# What it does:  looks the password up in our COMMON list.
# Takes:         the password, as text
# Gives back:    "COMMON: ..." or "not on the common list"
# Why a tool:    the model cannot see our list unless a tool reads it.
def is_common(password: str) -> str:
    """Check whether a password is on the list attackers try first."""
    # .lower() makes the check ignore capitals, so "PASSWORD" still matches.
    if password.lower() in COMMON:
        return "COMMON: attackers try this one first"
    return "not on the common list"


# TOOL 3: make_password
# What it does:  builds a new random password.
# Takes:         how many characters. 16 if the model does not say.
# Gives back:    the password, for example "cwb3f16hr!NBsQ%E"
# Why a tool:    a model "inventing" a password is not random. secrets is.
def make_password(length: int = 16) -> str:
    """Generate a new random password with the given number of characters."""
    # Every character the password is allowed to use.
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    # Pick one random character, "length" times, and glue them together.
    # int(...)  : small models sometimes send "16" as text. This fixes that.
    # min(.., 64): stops a silly request like a million characters.
    return "".join(secrets.choice(alphabet) for _ in range(min(int(length), 64)))


# =============================================================================
# SETUP: the tool menu and the memory
# =============================================================================

# A lookup table from a tool's NAME to the actual function:
#   {"check_strength": check_strength, "is_common": is_common, ...}
# The model asks for a tool by name (text). This is how we find the function.
# NEW TOOL? Add its name inside the brackets. That is the only change needed.
TOOLS = {tool.__name__: tool for tool in (check_strength, is_common, make_password)}

# The conversation so far. This list IS the agent's memory.
# Every message has a role:
#   system     our standing instructions (the PROMPT)
#   user       what the person typed
#   assistant  what the model said, or which tools it asked for
#   tool       the result of a tool we ran
# The model has no memory of its own. We send this whole list every time.
messages = [{"role": "system", "content": PROMPT}]


# =============================================================================
# THE CHAT: keep asking the person for questions
# =============================================================================
# This outer loop is NOT the agent. It only keeps the chat going.

while True:
    question = input("\nyou> ")          # wait for the person to type something
    if question == "quit":
        break                            # leave the program
    messages.append({"role": "user", "content": question})   # remember the question

    # =========================================================================
    # >>>>>>>>>>>>>>>>>>>>>>>  THE AGENT IS HERE  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # =========================================================================
    # This inner loop is the agent. Each trip around it is one "think, then act":
    #
    #     ask the model  ->  did it ask for tools?
    #                           NO  -> it has its answer. Print it. Stop.
    #                           YES -> run them, give back the results, go again.
    #
    # Nothing here says which tool to use or in what order.
    # THE MODEL DECIDES. That is what makes this an agent and not a script.
    #
    # range(6) is a safety limit: at most 6 trips per question, so a confused
    # model cannot loop forever.
    for step in range(6):  # the agent loop: at most 6 rounds per question

        # THINK. Send the whole conversation plus the tool menu to the model.
        # It replies with EITHER a normal answer OR a request to run tools.
        reply = chat(model=MODEL, messages=messages, tools=list(TOOLS.values())).message
        messages.append(reply)           # remember what the model said

        # DONE? If the model asked for no tools, its reply is the final answer.
        if not reply.tool_calls:  # no tool requests means the model is done
            print("coach>", reply.content)
            break                        # leave the agent loop, back to "you>"

        # ACT. The model asked for one or more tools. Run each one.
        for call in reply.tool_calls:  # run each tool the model asked for
            # The model gives us a tool NAME and its ARGUMENTS, for example:
            #   name = "check_strength"     args = {"password": "Summer2026!"}
            name, args = call.function.name, call.function.arguments

            # Look up the function by name and run it.
            # **args turns {"password": "abc"} into check_strength(password="abc").
            # try/except: if the model asks for a tool that does not exist, or
            # sends the wrong arguments, we do not crash. We send the error
            # back so the model can read it and try again.
            try:
                result = TOOLS[name](**args)
            except Exception as error:
                result = f"error: {error!r}"

            # Show the room what just happened. These [tool] lines are the
            # best part of the demo: the model's decisions, in plain sight.
            print(f"  [tool] {name}({args}) -> {result}")

            # OBSERVE. Put the result into the conversation. On the next trip
            # around the loop the model reads it and decides what to do next.
            # SECURITY: whatever a tool returns, the model reads and trusts.
            #           That is the door prompt injection walks through.
            messages.append({"role": "tool", "tool_name": name, "content": result})

    # This "else" belongs to the "for". It runs only when the loop used all
    # 6 trips without the model finishing.
    else:
        print("coach> I got stuck in a loop. Try asking another way.")


# =============================================================================
# QUESTIONS TO ASK THE AI
# =============================================================================
#
# START HERE (one tool job each)
#   Is Summer2026! any good?              -> check_strength + is_common
#   What about password1?                 -> is_common (says COMMON)
#   Make me a password                    -> make_password
#   Make me a 24 character password       -> make_password with length 24
#
# THE AGENT MOMENTS (the model makes its own plan)
#   Make me one and prove it's strong.
#       -> make_password, THEN it feeds that result into the two checkers.
#          Nobody told it to do step two. Point at the [tool] lines.
#   Which is stronger, Tr0ub4dor&3 or correcthorsebatterystaple?
#       -> the checkers, once for each password.
#          HEADS UP: our rule calls BOTH weak. The first is 11 characters.
#          The second is 25 characters but uses only 1 character type.
#          Good discussion: is our rule right? Current NIST guidance says
#          length matters more than mixing character types.
#
# FOLLOW-UPS (shows the memory)
#   Why is that one weak?
#   Make it longer.
#
# WHY TOOLS MATTER
#   How many characters are in correcthorsebatterystaple?
#       -> check_strength counts 25. A model without tools often guesses wrong.
#
# THE LIMITS (the agent only knows what its tools know)
#   Is hunter2 on the common list?
#       -> "no". Then add "hunter2" to COMMON, run again, ask again.
#
# NO TOOLS NEEDED (the model just talks)
#   What makes a password strong?
#   Should I use a password manager?
#
# RULE FOR THE ROOM: use made-up passwords. Never type a real one.
#
# =============================================================================
# QUESTIONS TO ASK THE ROOM
# =============================================================================
#
#   - Which line makes this an agent?          (the inner "for step" loop)
#   - Who decides which tool runs?             (the model)
#   - Who actually runs the tool?              (our Python code)
#   - What does the model see from our function?  (name, type hints, docstring)
#   - What happens if a tool returns text that says
#     "ignore your instructions"?              (the model may obey: prompt injection)
#   - What tool would you add next?