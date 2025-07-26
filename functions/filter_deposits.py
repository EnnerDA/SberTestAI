import pandas as pd
from pandas import DataFrame

def filter_deposits(user_preferences, deposits: DataFrame, ):
    filtered = deposits.copy()

    # Фильтрация по валюте
    if "currency" in user_preferences:
        filtered = filtered[filtered["currency"] == user_preferences["currency"]]

    # Фильтрация по сроку
    if "min_term" in user_preferences:
        filtered = filtered[filtered["term_days_min"] <= user_preferences["min_term"]]
    if "max_term" in user_preferences:
        filtered = filtered[filtered["term_days_max"] <= user_preferences["max_term"]]

    # Фильтрация по сумме
    if "amount" in user_preferences:
        filtered = filtered[filtered["min_amount"] <= user_preferences["amount"]]

    # Фильтрация по возможности пополнения
    if "replenishment" in user_preferences:
        filtered = filtered[filtered["replenishment"] == user_preferences["replenishment"]]

    filtered = filtered.sort_values("interest_rate", ascending=False)

    res = (f'Идеальный для Вас вариант\n{filtered.loc[1, 'name']}.\n'
           f'Подробнее узнайте тут:\n'
           f'{filtered.loc[1, 'link']}')
    return res



if __name__ == '__main__':
    print()
    # Загрузка данных о вкладах
    deposits = pd.read_csv("../Sber_test.csv")

    user_input = {
        "currency": "RUB",
        "min_term": 120,
        "max_term": 180,
        "amount": 54000,
        "replenishment": 0
    }
    best_deposit = filter_deposits(user_input, deposits)
    print(best_deposit)
    # recommended = filtered_deposits.sort_values("interest_rate", ascending=False).head(3)
    #
    # print("Рекомендуемые вклады:")
    # print(recommended[["interest_rate", "term_days_max", "min_amount"]])
