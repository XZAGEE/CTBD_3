
import time
import random

class Retry:
    def __init__(
        self,
        maxAttempts=3,
        strategy="constant",
        retryOn=(Exception,),
        baseDelay=1,
        maxDelay=30,
        sleepFn=time.sleep,
        randomFn=random.uniform
    ):
        if maxAttempts < 1:
            raise ValueError("maxAttempts must be at least 1")

        if strategy not in ("constant", "exponential", "exponentialJitter"):
            raise ValueError("Unknown retry strategy")

        self.maxAttempts = maxAttempts
        self.strategy = strategy
        self.retryOn = retryOn
        self.baseDelay = baseDelay
        self.maxDelay = maxDelay

        # Функції можна замінити під час тестування
        self.sleepFn = sleepFn
        self.randomFn = randomFn

    def should_retry(self, error):
        for rule in self.retryOn:

            # Перевіряємо тип помилки
            if isinstance(rule, type) and issubclass(rule, BaseException):
                if isinstance(error, rule):
                    return True

            # Перевіряємо код помилки
            else:
                error_code = getattr(error, "code", None)

                if error_code is None:
                    error_code = getattr(error, "status_code", None)

                if error_code == rule:
                    return True

        return False

    def get_delay(self, attempt):
        if self.strategy == "constant":
            delay = self.baseDelay

        elif self.strategy == "exponential":
            delay = self.baseDelay * (2 ** (attempt - 1))

        else:
            delay = self.baseDelay * (2 ** (attempt - 1))
            delay = self.randomFn(0, delay)

        return min(delay, self.maxDelay)

    def execute(self, fn):
        for attempt in range(1, self.maxAttempts + 1):

            try:
                return fn()

            except Exception as error:

                # Якщо помилка не входить до retryOn,
                # повторювати операцію не потрібно
                if not self.should_retry(error):
                    raise

                # Якщо спроби закінчилися — повертаємо помилку
                if attempt == self.maxAttempts:
                    raise

                # Розраховуємо час очікування
                delay = self.get_delay(attempt)

                # Очікуємо перед наступною спробою
                self.sleepFn(delay)
