import secrets
import string
import bisect
from typing import List, Tuple, Dict, Optional
import asyncio


class PromoGenerator:
    """
    Генератор промокодов с весами, переведённый на шкалу 1..10000.
    По умолчанию чаще выдаёт процентные купоны и реже — крупные фиксированные суммы.
    """

    def __init__(
            self,
            percents: List[int] = (3, 5, 7, 10, 15, 20, 30),
            fixed: List[int] = (500, 1000, 2000, 3000, 5000, 10000),
            pct_category_share: float = 0.8,  # доля вероятности на категорию "процентные" (0..1)
            total_scale: int = 10000,  # диапазон 1..total_scale
            code_len: int = 8,  # длина строки промокода
    ):
        assert 0.0 <= pct_category_share <= 1.0
        self.percents = list(percents)
        self.fixed = list(fixed)
        self.pct_category_share = pct_category_share
        self.total_scale = total_scale
        self.code_len = code_len

        # Посчитаем "сырые" веса (чем больше скидка — тем меньше вес)
        # Для процентных: вес ~ scale / percent
        # Для фиксированных: вес ~ scale_fixed / amount
        # Коэффициенты настроены так, чтобы получить разумные относительные вероятности.
        pct_coeff = 3000.0  # можно регулировать (чем больше — тем сильнее различие)
        fixed_coeff = 100000.0  # можно регулировать для фиксированных сумм

        raw_items: List[Tuple[str, int, float]] = []  # (category, value, raw_weight)
        for p in self.percents:
            w = max(1.0, pct_coeff / float(p))
            raw_items.append(("percent", p, w))
        for f in self.fixed:
            w = max(1.0, fixed_coeff / float(f))
            raw_items.append(("fixed", f, w))

        # Разделим общую "массу" между категориями (pct_category_share vs 1 - pct_category_share)
        sum_pct_raw = sum(w for (c, v, w) in raw_items if c == "percent")
        sum_fixed_raw = sum(w for (c, v, w) in raw_items if c == "fixed")

        entries: List[Tuple[str, int, float]] = []
        # Нормируем и распределяем по total_scale
        for (cat, val, w) in raw_items:
            if cat == "percent":
                portion = (w / sum_pct_raw) * (self.pct_category_share * self.total_scale)
            else:
                portion = (w / sum_fixed_raw) * ((1.0 - self.pct_category_share) * self.total_scale)
            entries.append((cat, val, max(1.0, portion)))

        # Чтобы работать с диапазоном 1..total_scale — округлим в целые и скорректируем суммарно
        counts = [int(round(e[2])) for e in entries]
        diff = self.total_scale - sum(counts)
        # корректируем в пользу самых "весомых" элементов (или просто первого, если diff небольшой)
        if diff != 0:
            # найдем индекс с максимальным raw portion (entries[i][2]) и поправим
            idx = max(range(len(entries)), key=lambda i: entries[i][2])
            counts[idx] += diff

        # Построим пороговые границы (cumulative)
        cum = []
        s = 0
        for cnt in counts:
            s += cnt
            cum.append(s)

        # Сохраняем
        self._entries = [(entries[i][0], entries[i][1]) for i in range(len(entries))]
        self._thresholds = cum  # длина == len(_entries)
        # Проста защита на случай краевых ошибок
        assert self._thresholds[-1] == self.total_scale

    def _make_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(self.code_len))

    async def generate(self) -> Dict[str, object]:
        """
        Асинхронно возвращает структуру:
        {
          "type": "percent" | "fixed",
          "value": int,            # процент или сумма в рублях
          "code": "ABC1234X",
          "meta": { "raw_random": int }  # при необходимости для логов
        }
        """
        # не блокирующая операция, но помечаем async для интеграции в event loop
        # Используем криптографический генератор для веса (secrets)
        r = secrets.randbelow(self.total_scale) + 1  # 1..total_scale
        idx = bisect.bisect_left(self._thresholds, r)
        cat, val = self._entries[idx]
        code = self._make_code()
        # Если нужно — можно сделать разные форматы кода в зависимости от типа:
        # e.g. P-XXXXXXX для процентов, F-XXXXXXX для fixed. Оставлю простой код.
        return {
            "type": cat,
            "value": val,
            "code": code,
            "meta": {"raw_random": r}
        }
