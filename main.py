import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests

#Функция для загрузки данных
@st.cache
def load_data(file):
    return pd.read_csv(file, parse_dates=['timestamp'])

# Функция для получения текущей погоды
def get_current_weather(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return response.json()

# Интерфейс Streamlit
st.title("Анализ исторических данных и текущей погоды")

#Загрузка файла
uploaded_file = st.file_uploader("Загрузка файла с историческими данными (CSV)", type=["csv"])
if uploaded_file is not None:
    data = load_data(uploaded_file)
    st.write("Данные загружены:")
    st.write(data.head())

    #Выбор города
    city = st.selectbox("Выберите город", options=data['city'].unique())

    # Форма для ввода API-ключа
    api_key = st.text_input("Введите API-ключ OpenWeatherMap")

    #Текущая погода
    if api_key:
        weather = get_current_weather(city, api_key)
        if "cod" in weather and weather["cod"] == 401:
            st.error("Некорректный API-ключ. Пожалуйста, проверьте и попробуйте снова.")
        elif weather:
            #st.write(f"Текущая погода в {city}:")
            #st.write(weather)
            st.write(f"Текущая погода в {city}: {weather['main']['temp']} °C")

            #Проверка текущей температуры на соответствие сезону
            current_temp = weather['main']['temp']
            current_month = pd.Timestamp.now().month
            season = {12: 'winter', 1: 'winter', 2: 'winter',
                      3: 'spring', 4: 'spring', 5: 'spring',
                      6: 'summer', 7: 'summer', 8: 'summer',
                      9: 'autumn', 10: 'autumn', 11: 'autumn'}[current_month]

            seasonal_stats = data[data['city'] == city].groupby('season')['temperature'].agg(['mean', 'std']).reset_index()
            season_stats = seasonal_stats[seasonal_stats['season'] == season]

            if not season_stats.empty:
                mean_temp = season_stats['mean'].values[0]
                std_temp = season_stats['std'].values[0]

                if current_temp < mean_temp - 2 * std_temp or current_temp > mean_temp + 2 * std_temp:
                    st.warning(f"Текущая температура {current_temp} °C выходит за пределы нормы для сезона {season}.")
                else:
                    st.success(f"Текущая температура {current_temp} °C находится в пределах нормы для сезона {season}.")

    #Фильтрация данных для выбранного города
    city_data = data[data['city'] == city]

    #Описательная статистика
    st.subheader('Описательная статистика')
    st.write(city_data.describe())

    #Выбор типа графика
    graph_type = st.selectbox("Выберите тип графика", ["Гистограмма", "Boxplot", "Линейный график"])

    #Построение выбранного графика
    if graph_type == "Гистограмма":
        st.subheader("Гистограмма температуры")
        plt.figure(figsize=(8, 5))
        plt.hist(city_data['temperature'], bins=20, color='skyblue', edgecolor='black')
        plt.xlabel('Температура (°C)')
        plt.ylabel('Частота')
        plt.title('Гистограмма температуры')
        st.pyplot(plt)

    elif graph_type == "Boxplot":
        st.subheader("Boxplot температуры")
        plt.figure(figsize=(8, 5))
        plt.boxplot(city_data['temperature'], vert=False, patch_artist=True, boxprops=dict(facecolor='skyblue'))
        plt.xlabel('Температура (°C)')
        plt.title('Boxplot температуры')
        st.pyplot(plt)

    elif graph_type == "Линейный график":
        st.subheader("Линейный график температуры")
        plt.figure(figsize=(10, 5))
        plt.plot(city_data['timestamp'], city_data['temperature'], label='Температура', color='blue')
        plt.xlabel('Дата')
        plt.ylabel('Температура (°C)')
        plt.title('Линейный график температуры')
        plt.legend()
        st.pyplot(plt)

    # Временной ряд с выделением аномалий
    st.subheader("Временной ряд температур с выделением аномалий")
    city_data['is_anomaly'] = ((city_data['temperature'] < city_data['temperature'].mean() - 2 * city_data['temperature'].std()) |
                               (city_data['temperature'] > city_data['temperature'].mean() + 2 * city_data['temperature'].std()))

    plt.figure(figsize=(10, 5))
    plt.plot(city_data['timestamp'], city_data['temperature'], label='Температура')
    plt.scatter(city_data[city_data['is_anomaly']]['timestamp'],
                city_data[city_data['is_anomaly']]['temperature'],
                color='red', label='Аномалии')
    plt.xlabel('Дата')
    plt.ylabel('Температура (°C)')
    plt.legend()
    st.pyplot(plt)

    # Сезонные профили
    st.subheader("Сезонные профили")
    city_data['season'] = city_data['timestamp'].dt.month.map(lambda x: {12: 'winter', 1: 'winter', 2: 'winter',
                                                                         3: 'spring', 4: 'spring', 5: 'spring',
                                                                         6: 'summer', 7: 'summer', 8: 'summer',
                                                                         9: 'autumn', 10: 'autumn', 11: 'autumn'}[x])
    seasonal_stats = city_data.groupby('season')['temperature'].agg(['mean', 'std']).reset_index()
    st.write(seasonal_stats)

    # Визуализация сезонных профилей
    plt.figure(figsize=(8, 4))
    plt.bar(seasonal_stats['season'], seasonal_stats['mean'], yerr=seasonal_stats['std'], capsize=5, color='skyblue')
    plt.xlabel('Сезон')
    plt.ylabel('Средняя температура (°C)')
    plt.title('Сезонный профиль температур')
    st.pyplot(plt)
