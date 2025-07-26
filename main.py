from dataclasses import dataclass
from typing import Sequence
import uuid
import pandas as pd
from dotenv import find_dotenv, load_dotenv

from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv(find_dotenv())

@dataclass
class UserPreferences:
    """Предпочтения клиента"""
    deposit_term: int # срок депозита в днях
    amount: int # сумма денег
    currency: str # валюта
    replenishment: bool # возможность пополнения
    withdrawal: bool # возможность снятия
    capitalization: bool # капитализация процентов


@tool
def choose_deposit(preferences: UserPreferences) -> str:
    """ Функция подберет наиболее подходящий вклад для клиента на основе его предпочтений.
    Вернет строку с названием вклада и ссылкой на него.
    Args:
        preferences (UserPreferences): предпочтения клиента
    Returns:
        str """

    print('START')
    print(preferences)
    deposits = pd.read_csv('Sber_test.csv')
    filtered = deposits.copy()

        # Фильтрация по сроку +-месяц от пожеланий
    filtered = filtered[filtered["term_days_min"] <= preferences.deposit_term]
    filtered = filtered[preferences.deposit_term - filtered["term_days_max"] <= 15]
    filtered = filtered[preferences.deposit_term - filtered["term_days_max"] >= -15]
        # Фильтрация по сумме
    filtered = filtered[filtered["min_amount"] <= preferences.amount]
        # Фильтрация по валюте
    filtered = filtered[filtered["currency"] == preferences.currency]
        # Фильтрация по возможности пополнения
    filtered = filtered[filtered["replenishment"] == preferences.replenishment]
        # Фильтрация по возможности снятия
    filtered = filtered[filtered["withdrawal"] == preferences.withdrawal]
        # Фильтрация по капитализации процентов
    filtered = filtered[filtered["capitalization"] == preferences.capitalization]
        # Выбираем лучший вариант сортируя по процентной ставке
    filtered = filtered.sort_values("interest_rate", ascending=False)
        # Формируем сообщение
    res = (f'Идеальный для Вас вариант\n{filtered.iloc[1]['name']}.\n'
           f'Подробнее узнайте тут:\n'
           f'{filtered.iloc[1]['link']}')

    return res

class LLMAgent:
    def __init__(self, model: LanguageModelLike, tools: Sequence[BaseTool]):
        self._model = model
        self._agent = create_react_agent(
            model,
            tools=tools,
            checkpointer=InMemorySaver())
        self._config: RunnableConfig = {
                "configurable": {"thread_id": uuid.uuid4().hex}}


    def invoke(
        self,
        content: str,
        temperature: float=0.1,
    ) -> str:
        """Отправляет сообщение в чат"""
        message: dict = {
            "role": "user",
            "content": content,
        }
        return self._agent.invoke(
            {"messages": [message], "temperature": temperature},
            config=self._config)["messages"][-1].content


def print_agent_response(llm_response: str) -> None:
    print(f"\033[35m{llm_response}\033[0m")


def get_user_prompt() -> str:
    return input("\nТы: ")


def main():
    model = GigaChat(
        model="GigaChat",
        verify_ssl_certs= False,
    )
    model.Config.max_tokens = 500
    agent = LLMAgent(model, tools=[choose_deposit])
    system_prompt = (
        """
       Ты сотрудник Сбера. Твоя задача подобрать вклад для клиента.
        Ты должен выясить у клиента его предпочтения и создать на основе опроса экземпляр класса UserPreferences.
        при создании экземпляра класса приведи ответы клиента к нужному типу данных:
        deposit_term: int # срок депозита в днях
        amount: int # сумма денег
        currency: str # валюта может принимать одно из значений RUB, USD, EURO. По умочанию используй RUB.
        replenishment: bool # возможность пополнения. По умолчанию используй False
        withdrawal: bool # возможность снятия. По умолчанию используй False
        capitalization: bool # капитализация процентов. По умолчанию используй False.
        Далее передай этот экземпляр функции choose_deposit() которая тебе передана в качестве tools.
        Результат этой выполнения функции верни в качестве ответного сообщения без изменений.
        Если после ответа пользователь решит уточнить или изменить свои предпочтения, 
        обнови экземпляр класса UserPreferences передай этот экземпляр функции choose_deposit.
        Результат этой выполнения функции верни в качестве ответного сообщения без изменений.
"""
    )
#     system_prompt = ("""Ты — виртуальный помощник Сбера, специализирующийся на подборе вкладов. Будь краток и вежлив.
#     ВЫПОЛНЯЙ ПО ШАГАМ!
#     1. Спроси у клиента какую сумму он хочет положить на вклад. Ответ клиента приведи к значению int
#     и сохрани в переменной user_amount с типом int.
#
#     2. Напиши сообщение с результатом функции choose_deposit(UserPreferences(deposit_term= 180, amount= 74000, currency= 'RUB', replenishment= 0, withdrawal= 0, capitalization= 0)
# """
#     )

    agent_response = agent.invoke(content=system_prompt)

    while True:
        print_agent_response(agent_response)
        agent_response = agent.invoke(get_user_prompt())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nМоё почтение")