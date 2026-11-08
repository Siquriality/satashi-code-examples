#!/usr/bin/env bash
# Рисует декоративную анимацию терминала в стиле Matrix.

set -u

cols=$(tput cols 2>/dev/null || echo 80)
lines=$(tput lines 2>/dev/null || echo 24)
chars='01ABCDEFabcdef@$#%&*+-=/<>[]{}:;'

cleanup() {
  tput cnorm 2>/dev/null || true
  printf '\033[0m\033[2J\033[H'
}

trap cleanup EXIT INT TERM

tput civis 2>/dev/null || true
printf '\033[2J\033[H\033[1;32m'

rand_char() {
  local i=$((RANDOM % ${#chars}))
  printf '%s' "${chars:$i:1}"
}

noise_line() {
  local width=${1:-$cols}
  local out=''
  for ((i = 0; i < width; i++)); do
    out+="$(rand_char)"
  done
  printf '%s\n' "$out"
}

burst() {
  for ((r = 0; r < lines - 2; r++)); do
    if (( RANDOM % 4 == 0 )); then
      printf '\033[1;37m'
    elif (( RANDOM % 3 == 0 )); then
      printf '\033[0;32m'
    else
      printf '\033[1;32m'
    fi
    noise_line "$cols"
  done
}

status() {
  local msg=$1
  printf '\033[1;31m[%02d:%02d:%02d] %s\033[0;32m\n' \
    $((RANDOM % 24)) $((RANDOM % 60)) $((RANDOM % 60)) "$msg"
}

for ((i = 0; i < 3; i++)); do
  burst
  sleep 0.08
  printf '\033[H'
done

printf '\033[2J\033[H'
status 'incoming connection established'
sleep 0.25
status 'root handshake accepted'
sleep 0.2
status 'session token captured'
sleep 0.2
status 'firewall rule override'
sleep 0.25
status 'access granted'
sleep 0.35

for p in 03 09 17 24 31 42 56 63 71 84 91 99; do
  printf '\033[1;32mdeploying payload: [%-50s] %s%%\r' \
    "$(printf '%*s' $((p / 2)) '' | tr ' ' '#')" "$p"
  sleep 0.12
done
printf '\n'

for ((i = 0; i < 40; i++)); do
  case $((RANDOM % 7)) in
    0) status "scanning /dev/tty$((RANDOM % 9))" ;;
    1) status "opening port $((1024 + RANDOM % 55000))" ;;
    2) status "injecting code block 0x$(printf '%04X' "$RANDOM")" ;;
    3) status "mirror node $((RANDOM % 255)).$((RANDOM % 255)).$((RANDOM % 255)).$((RANDOM % 255)) online" ;;
    4) status "credential buffer: $(noise_line 18 | tr -d '\n')" ;;
    5) status "kernel trace rewritten" ;;
    6) status "terminal ownership changed" ;;
  esac
  sleep 0.055
done

while true; do
  printf '\033[H'
  burst
  row=$((1 + RANDOM % lines))
  col=$((1 + RANDOM % cols))
  printf "\033[%s;%sH\033[1;31mACCESS GRANTED\033[0;32m" "$row" "$col"
  sleep 0.045
done
