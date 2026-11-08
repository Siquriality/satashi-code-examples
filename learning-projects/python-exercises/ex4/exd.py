# Учебный пример класса Book и работы с его полями.
class Book:
    def __init__(self, title, author, year):
        self.title = title
        self.author = author
        self.year = year
    def __str__(self):
        return f'{self.title} ({self.author}, {self.year}'
class Reader:
    def __init__(self, name, books:list):
        self.name =  name
        self.books = list(books)
    def take_book(self, book):
        self.books.append(book)
    def return_book(self, book):
        self.books.remove(book)
    def __str__(self):
        return (' ').join(map(str, self.books)) 

class Library(Reader):
    def __init__(self, bookslib):
        self.bookslib = list(bookslib)
        self.reader = dict()

    def add_book(self, book):
        self.bookslib.append(book)
    def register_reader(self, reader):
        self.reader[reader] = []
    def give_book(self, book_title, reader_name):
        super().take_book(book_title)
        self.bookslib.remove(book_title)
        self.reader[reader_name].append(book_title)
    def return_book(self, book_title, reader_name):
        super().return_book(book_title)
        self.bookslib.append(book_title)
        self.reader[reader_name].remove(book_title)
    def report(self):
        return self.reader

book1 = Book("1984", "George Orwell", 1949)
book2 = Book("Dune", "Frank Herbert", 1965)

reader1 = Reader("Ivan", [123])
reader2 = Reader("Anna", [1233])

lib = Library([123, 4535, 2435, 4576])
lib.add_book(book1)
lib.add_book(book2)
lib.register_reader(reader1)
lib.register_reader(reader2)

lib.give_book("1984", "Ivan")
lib.give_book("Dune", "Anna")

lib.report()
     
     


        
    
    