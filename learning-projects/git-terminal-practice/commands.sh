#!/usr/bin/env bash
# Создаёт структуру учебного проекта и перемещает учебные файлы.
set -e
mkdir -p project/{src,data,docs}
if [ -f summary.py ]; then mv summary.py project/src/; fi
if [ -f sample.txt ]; then mv sample.txt project/data/; fi
echo 'це проект для практичної 4 тут я працюю з файлами через термінал' > project/docs/readme.txt
echo 'API_KEY=demo-1234-ce-ne-spravzhniy-kliuch' > project/config.local
cp project/data/sample.txt project/data/backup.txt
rm project/data/backup.txt
ls -lR project > structure.txt
grep -Rn 'коміт' project/data > found.txt
ls project/data | wc -l >> found.txt
