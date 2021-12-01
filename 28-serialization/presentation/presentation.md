---
theme: gaia
paginate: true
backgroundColor: #fff
footer: Сериализация и валидация / Python 2021 / УрФУ
style: |
    section {
      font-family: "Open Sans", "Tahoma", "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji";
      font-size: 32px;
      letter-spacing: unset;
    }
    header,
    footer {
      font-size: 50%;
    }
    section::after {
      content: attr(data-marpit-pagination) ' / ' attr(data-marpit-pagination-total);
    }
---

<!-- _class: lead -->

# Сериализация и валидация

---

# Какую задачу решаем?

Хотим:
* сохранить состояние программы на диске/где-то ещё;
* передать состояние/данные из программы куда-нибудь;

Т.е. нам нужен формат данных для общения и уметь преобразовывать из/в него.

P.S. Формально сериализация - процесс перевода структуры данных в последовательность байтов.


---

# Форматы и способы хранения данных

* pickle
* json
* sqlite

И многие другие БД и форматы


---

# Pickle

Сохраняет любые python-объекты, покуда он может сохранить все его аттрибуты.

```python
import pickle

data = {
    'a': [1, 2.0, 3, 4+6j],
    'b': ("character string", b"byte string"),
    'c': {None, True, False}
}

with open('data.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
```


---

# Pickle load

Классы/функции/method'ы не могут быть запиклены.

```python
import pickle

with open('data.pickle', 'rb') as f:
    # The protocol version used is detected automatically, so we do not
    # have to specify it.
    data = pickle.load(f)
```


---

# Минусы и особенности pickle

* поддерживается только Python'ом
* Нечеловекочитаемый
* **!!НЕБЕЗОПАСНЫЙ!!**


---

# Json

Javascript Object Notation

```json
>>> import json
>>> print(json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4))
{
    "4": 5,
    "6": 7
}
```


---

# Особенности json

* (по-умолчанию) сериализует только словари, списки, числа, строки, bool и None
* текстовый и человекочитаемый
* используется повсеместно



---

# yaml
Более читаемый json

```yaml
# All about the character
name: Ford Prefect
age: 42
possessions:
- Towel
```

В python есть несколько внешних библиотек для него (pyyaml, ...)

P.S. Ещё есть toml

---

# Особенности yaml
* гораздо приятнее писать
* сложная спецификация
* парсеры на разных языках могут вести себя по разному
* породил кучу мемов


P.S: про неочевидные приколы с YAML'ами
* https://docs.saltproject.io/en/latest/topics/troubleshooting/yaml_idiosyncrasies.html
* https://github.com/cblp/yaml-sucks

---

![Yaaaaml](yaml_everywhere.jpg)

---

```python
# Использование БД (sqlite)

import sqlite3

con = sqlite3.connect(":memory:")
cur = con.cursor()
cur.execute("create table lang (name, first_appeared)")

cur.execute("insert into lang values (?, ?)", ("C", 1972))

lang_list = [
    ("Fortran", 1957),
    ("Python", 1991),
    ("Go", 2009),
]
cur.executemany("insert into lang values (?, ?)", lang_list)

cur.execute("select * from lang where first_appeared=:year", {"year": 1972})
print(cur.fetchall())

con.close()
```

---

# Валидация

* в sqlite'е в каком-то виде получается встроенная
* а вот в json/yaml...


---

# Schematics

https://schematics.readthedocs.io/en/latest/

```python
>>> from schematics.models import Model
>>> from schematics.types import StringType, URLType
>>> class Person(Model):
...     name = StringType(required=True)
...     website = URLType()
...
>>> person = Person({'name': u'Joe Strummer',
...                  'website': 'http://soundcloud.com/joestrummer'})
>>> person.name
u'Joe Strummer'
```

---

# Schematics (dumping)

```python
>>> import json
>>> json.dumps(person.to_primitive())
{"name": "Joe Strummer", "website": "http://soundcloud.com/joestrummer"}
```

---

# Schematics (loading)

```python
class Song(Model):
    name = StringType()
    artist = StringType()
    url = URLType()

>>> song_json = '{"url": "http://www.youtube.com/watch?v=67KGSJVkix0", "name": "Werewolf", "artist": "Fiona Apple"}'
>>> fiona_song = Song(json.loads(song_json))
>>> fiona_song.url
u'http://www.youtube.com/watch?v=67KGSJVkix0'
```

---

# ORM'ы (на примере peewee)

```python
from peewee import *

db = SqliteDatabase('people.db')

class Person(Model):
    name = CharField()
    birthday = DateField()

    class Meta:
        database = db # This model uses the "people.db" database.
```

---

# ORM'ы (на примере peewee)
```python
class Pet(Model):
    owner = ForeignKeyField(Person, backref='pets')
    name = CharField()
    animal_type = CharField()

    class Meta:
        database = db # this model uses the "people.db" database
```

---

# ORM'ы (на примере peewee): соединение, сохранение, удаление
```python
db.connect()
db.create_tables([Person, Pet])

from datetime import date
uncle_bob = Person(name='Bob', birthday=date(1960, 1, 15))
uncle_bob.save() # bob is now stored in the database
# Returns: 1

grandma = Person.create(name='Grandma', birthday=date(1935, 3, 1))
grandma.name = 'Grandma L.'
grandma.save()  # Update grandma's name in the database.

```

---

# Peewee: связанные объекты

```python
# связанный объект
bob_kitty = Pet.create(owner=uncle_bob, name='Kitty', animal_type='cat')
bob_kitty.save()
bob_kitty.delete_instance() # he had a great life
```
---

# Peewee: поиск и загрузка объектов
```python
# One object
grandma = Person.get(Person.name == 'Grandma L.')

# all persons
for person in Person.select():
    print(person.name)

# Cats
query = Pet.select().where(Pet.animal_type == 'cat')
for pet in query:
    print(pet.name, pet.owner.name)
```
---

# ORM/БД: Транзакции

```python
with db.atomic() as tx:
    grandma = Person.get(Person.name == 'Grandma L.')
    grandma.name = 'Rick A.'
    grandma.save()

    # Lol, jokeing
    tx.rollback()
```

---

# Осталось за рамками пары

* https://developers.google.com/protocol-buffers
* другие аналогичные бинарные форматы для сериализации
* XML (любили в 2000-х кажется, было относительно больно)


![height:6cm](xml_meme.png)

Fun fact: этот мем вероятно из той же эпохи, что и сам XML

---

# Восстановление после сбоев

Будем просто записывать периодически состояние в каком-то формате (например json).

Какие могут быть проблемы?

---

# Восстановление после сбоев

Записывать состояние в 2 этапа:
* записываем во временный файл
* `os.rename`'ом подменяем файл с состоянием на наш временный

---

# Append log

* дописываем выполняемые операции в конец файла
* не забываем делать `f.flush()`
* при восстановлении пытаемся читать операции подряд и "применять" их
* последняя операция может оказаться поврежденной
* если так, то просто считаем, что она не выполнена

---

# Задание на пару:

Даётся число N, надо вывести все простые числа от 1 до `N`.

Обработать внезапное прерывание процесса:
не выводить уже выведенные ранее при повторном запуске.

Попробовать придумать как это можно по-проверять.
