# Учебное задание с генератором чётных чисел.
'''🔹 Задание 3: Чётные числа-генератор
Описание:
Класс EvenCounter, который при итерации выдает чётные числа от 0 до заданного максимума (включительно).

Требования:

Использовать __iter__ и __next__

Никаких yield, только ООП

Без наследования

'''
class EvenCounter:
    def __init__(self, max):
        self.max = max
        
    def __iter__(self):
        self.value = 0
        return self
    def __next__(self):
        if self.value  <= self.max: 
            self.value +=2
            return self.value
        else:
            raise StopIteration
    



evens = EvenCounter(6)
for x in evens:
    print(x)
