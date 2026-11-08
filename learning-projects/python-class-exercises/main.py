# Учебный класс профиля пользователя и работа с его данными.
class UserProfile:
    
    def __init__(self, name = None, age = None, email = None, status= None, friends = []):
        self.name = name
        self.age = age
        self.friends = friends
        self._email = email
        self._status = status
    @property
    def get_email(self):
        return self._email
    @get_email.setter
    def get_email(self, email):
        if '@' in  email and '.' in email:

            self._email = email
        else:
            raise TypeError('/@')
    @property
    def get_status(self):
        return self._status
    @get_status.setter
    def get_status(self, status):
        if status in ('online', 'offline', 'away'):
            self._status = status
        else:
            raise TypeError('Online offline away')
    
    def add_friend(self, friend):
        self.friends.append(friend)
    def remove_friend(self, friend):
        self.friends.remove(friend)
    def show_info(self):
        return f'{self.name}, {self.age}, {self._email}, {self._status}, {(' ').join(self.friends)}'        
    def __bool__(self):

        return bool(self.name) and bool(self._email) and len(self.friends) > 0

user = UserProfile("Маша", 17, "masha@example.com")

print(bool(user))  

user.add_friend("Катя")
print(bool(user))  # True

user.show_info()
user.change_status("online")
user.email = "новый_email@mail.ru"
