---
theme: gaia
paginate: true
backgroundColor: #fff
footer: Профилирование и отладка / Python 2021 / УрФУ
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

# Профилирование и отладка

---

# План на пару

1. Расскажу про профилирование
2. Попробуем по-профилировать и пооптимизировать сами
3. Ещё чуток расскажу про отладку и логирование

---

# placeholder

Для другой презентации

---

# Задание на пару:

Дана домашка hw4.py.

Надо разобраться что тормозит и оптимизировать.

---

# Профилирование памяти

* [memory-profiler](https://pypi.org/project/memory-profiler/)
* guppy3, etc.

Как работают?
* следят за выделением и освобождением памяти
* могут анализировать объекты в памяти питона и группировать

---

# Отладка

* [pdb](https://docs.python.org/3/library/pdb.html)
* [ipdb](https://pypi.org/project/ipdb/)


p.s. порой проще воспользоваться PyCharm'ом.

---

# Логирование

Гораздо проще жить, когда программа сама говорит, что происходит)


```python

import logging

def main():
    args = parse_args()
    logging.basicConfig(filename='example.log', encoding='utf-8', level=(logging.DEBUG if args.verbose else logging.INFO) )
    logging.debug('This message should go to the log file only if verbose option is set')
    logging.info('And this one should always be there')
    logging.warning('Formatting works too: number %d, string %s;', 10, "some_string")
    logging.error('And non-ASCII stuff, too, like Øresund and Malmö')

```

P.S. Возможно я на отдельной паре попробую по-рассказывать best practices



