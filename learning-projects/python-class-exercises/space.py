# Учебный класс словаря с журналированием обращений.
'''Задание 2: Словарь по умолчанию с логом
Описание:
Создай класс LoggedDict, который работает как обычный словарь, но:

Запоминает все попытки чтения и записи значений (внутренний лог)

При обращении к несуществующему ключу — возвращает None, но записывает попытку доступа

Требования:

Использовать __getitem__ и __setitem__

Хранить лог обращений в списке self.log

Без наследования от dict'''
class LoggedDict:
    def __init__(self):
        self.dic = dict()
        self.log = list()
    def __getitem__(self, key):
        if key in self.dic:
            self.log.append(('get', key))
            return self.dic[key]
        else:
            self.log.append(('get', key))
            return None
    def __setitem__(self, key, value):
        if key not in self.dic:
            self.dic[key] = value
            self.log.append(('set', key, value))



d = LoggedDict()
d['a'] = 10
print(d['a'])      # 10
print(d['b'])      # None

print(d.log)
# [('set', 'a', 10), ('get', 'a'), ('get', 'b')]
