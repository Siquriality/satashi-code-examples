# Проверяет структуру и результаты практической работы по Git.
# Самоперевірка ПЕРЕД здачею.
#
# Запустіть цей скрипт із теки, де лежить ваша робота:
#     python self_check.py
#
# Він не ставить оцінку. Він перевіряє те саме, що й перевірка викладача,
# і каже, що ще не готове. Доки тут є хоч один рядок «НЕ ГОТОВО» —
# здавати зарано.

import os
import re
import subprocess
import sys

PROJECT = "project"
problems = []
lines = []


def show(mark, text):
    row = "%s %s" % (mark, text)
    print(row)
    lines.append(row)
    if mark == "НЕ ГОТОВО":
        problems.append(text)


def save():
    """Записує звіт у файл. Викликається ЗАВЖДИ, зокрема й при виході
    на півдорозі — інакше на диску лишиться звіт від попереднього запуску,
    у якому написано, що все гаразд."""
    with open("self_check_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def finish(message):
    print()
    print(message)
    save()
    sys.exit(0)


def git(*args):
    """Виконує команду git у теці project і повертає її вивід."""
    try:
        r = subprocess.run(["git"] + list(args), cwd=PROJECT,
                           capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.returncode
    except FileNotFoundError:
        return "", 127


print("=== Самоперевірка роботи ===")
print()

# --- 1. Файли частини 1
for name in ("commands.sh", "structure.txt", "found.txt", "report.md"):
    if os.path.exists(name):
        show("гаразд", "файл %s на місці" % name)
    else:
        show("НЕ ГОТОВО", "немає файлу %s" % name)

if not os.path.isdir(PROJECT):
    show("НЕ ГОТОВО", "немає теки %s — частину 1 не виконано" % PROJECT)
    finish("Далі перевіряти нічого. Поверніться до частини 1.")

# --- 2. Репозиторій
if os.path.isdir(os.path.join(PROJECT, ".git")):
    show("гаразд", "тека .git на місці")
else:
    show("НЕ ГОТОВО",
         "у теці %s НЕМАЄ теки .git — репозиторій не створено" % PROJECT)
    finish("Без .git уся частина 2 не зарахується. Поверніться до неї.")

out, code = git("--version")
if code == 127:
    show("НЕ ГОТОВО", "git не знайдено — його треба встановити")
    finish("Встановіть git і запустіть перевірку ще раз.")

# --- 3. Історія
log, _ = git("log", "--oneline")
commits = [l for l in log.split("\n") if l.strip()]
if len(commits) >= 5:
    show("гаразд", "комітів: %d" % len(commits))
else:
    show("НЕ ГОТОВО", "комітів лише %d, потрібно щонайменше 5" % len(commits))

author, _ = git("log", "-1", "--format=%an")
if author and author.lower() not in ("", "your name", "unknown"):
    show("гаразд", "автор комітів: %s" % author)
else:
    show("НЕ ГОТОВО", "не налаштовано ім'я автора (git config user.name)")

merges, _ = git("log", "--merges", "--format=%H")
merge_list = [m for m in merges.split("\n") if m.strip()]
if merge_list:
    parents, _ = git("log", "-1", "--format=%P", merge_list[0])
    if len(parents.split()) == 2:
        show("гаразд", "є коміт злиття з двома батьками")
    else:
        show("НЕ ГОТОВО", "коміт злиття є, але батьків у нього не два")
else:
    show("НЕ ГОТОВО", "немає коміта злиття — гілку не злито через merge")

status, _ = git("status", "--porcelain")
if status:
    show("НЕ ГОТОВО", "є незакомічені зміни (%d файлів)"
         % len(status.split("\n")))
else:
    show("гаразд", "робоча тека чиста, усе закомічено")

# --- 4. Маркери конфлікту
tracked, _ = git("ls-files")
bad = []
for rel in [t for t in tracked.split("\n") if t.strip()]:
    p = os.path.join(PROJECT, rel)
    if not os.path.isfile(p):
        continue
    try:
        text = open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    if re.search(r"^(<<<<<<< |=======$|>>>>>>> )", text, re.M):
        bad.append(rel)
if bad:
    show("НЕ ГОТОВО", "у файлах лишилися маркери конфлікту: %s"
         % ", ".join(bad))
else:
    show("гаразд", "маркерів конфлікту у файлах немає")

# --- 5. .gitignore реально працює
ignored_name = "config.local"
on_disk = os.path.exists(os.path.join(PROJECT, ignored_name))
in_git = ignored_name in tracked.split("\n")
if on_disk and not in_git:
    show("гаразд", "%s лежить на диску, але git його не відстежує" % ignored_name)
elif not on_disk:
    show("НЕ ГОТОВО", "немає файлу %s — його треба створити" % ignored_name)
else:
    show("НЕ ГОТОВО", "%s потрапив у репозиторій — .gitignore не працює"
         % ignored_name)

# --- 6. Секрети
leaks = []
cfg = os.path.join(PROJECT, ".git", "config")
if os.path.exists(cfg):
    text = open(cfg, encoding="utf-8", errors="replace").read()
    if re.search(r"://[^/\s:]+:[^/\s@]+@", text):
        leaks.append(".git/config містить пароль або токен у адресі remote")
patterns = [r"ghp_[A-Za-z0-9]{10,}", r"github_pat_[A-Za-z0-9_]{10,}",
            r"AKIA[0-9A-Z]{12,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
    for f in files:
        if not f.endswith((".txt", ".md", ".sh", ".py", ".local", ".json")):
            continue
        try:
            t = open(os.path.join(root, f), encoding="utf-8",
                     errors="replace").read()
        except OSError:
            continue
        for pat in patterns:
            if re.search(pat, t):
                leaks.append("схоже на справжній ключ у файлі %s" % f)
                break
if leaks:
    for l in leaks:
        show("НЕ ГОТОВО", "УВАГА, СЕКРЕТ: " + l)
    show("НЕ ГОТОВО", "приберіть це ПЕРЕД здачею — роботу бачитиме викладач")
else:
    show("гаразд", "справжніх ключів і паролів у роботі не знайдено")

# --- підсумок
print()
if problems:
    print("Не готово до здачі. Залишилося виправити: %d" % len(problems))
    for p in problems:
        print("   -", p)
else:
    print("Усе гаразд. Можна пакувати в zip і здавати.")
    print("ГОЛОВНЕ: архів МАЄ містити приховану теку project/.git")

save()
