import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import chardet
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

# FIXME: naming на русский поменять
# FIXME: docker



st.title('Анализ данных и проверка гипотез. Тестовое задание :full_moon_with_face:')
st.sidebar.title('Настройки :toolbox:')

# ==========================================================================================
# Загрузка данных
# ==========================================================================================

uploaded_file = st.sidebar.file_uploader('Загрузите файл CSV', type=["csv"])

if uploaded_file is not None: 

    raw_data = uploaded_file.read()
    enc = chardet.detect(raw_data)
    # Пришлось прибегать к следующему методу, поскольку так как в ноутбуке стримлит файл не считывал :(
    df_raw = uploaded_file.getvalue().decode(enc['encoding']).replace('"', '').split('\r\n')
    df_raw = [x.split(',') for x in df_raw]
    df = pd.DataFrame(df_raw[1:-1]) # первая строка - колонки, которые я и так меняю, последняя - None значения
    
    # Ради личного удобства
    df.columns = ['sick_leave_days', 'age', 'gender']
    df.loc[df['gender'] == "Ж", 'gender'] ='F'
    df.loc[df['gender'] == "М", 'gender'] ='M'

    df['sick_leave_days'] = df['sick_leave_days'].astype(int)
    df['age'] = df['age'].astype(int)


# ==========================================================================================
# Параметры
# ==========================================================================================

    # Фильтрация данных по возрасту и числу рабочих дней
    age_filter       = st.sidebar.slider(
                                            'Выберите возрастную группу - разделитель:', 
                                            min_value=min(df['age']), 
                                            max_value=max(df['age']), 
                                            value=35)
    
    work_days_filter = st.sidebar.slider(
                                            'Выберите минимальное количество нерабочих дней:', 
                                            min_value=0,
                                            max_value=max(df['sick_leave_days']), 
                                            value=2)
    
    alpha            = st.sidebar.number_input(
                                            'Выберите значение alpha для статистических тестов', 
                                            value=0.05
                                            )

    filtered_data = df[(df['sick_leave_days'] > work_days_filter)]

    st.subheader('Отфильтрованные данные')
    st.write(filtered_data)


# ==========================================================================================
# Графики
# ==========================================================================================

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    col1, col2 = st.columns(2)

    with col1:

        # График распределения sick_leave_days для мужчин и женщин (первоначальный масштаб) ----
        male_data   = filtered_data[filtered_data['gender'] == 'M']
        female_data = filtered_data[filtered_data['gender'] == 'F']

        fig1 = px.histogram(
                                filtered_data, x='sick_leave_days', 
                                color='gender', 
                                title='Распределение sick_leave_days по полу'
                            )
        
        fig1.update_layout(
            title='Распределение sick_leave_days по полу',
            xaxis=dict(title='sick_leave_days'),
            yaxis=dict(title='Частота'),
            width=400, 
            height=400  
        )

        st.plotly_chart(fig1)


        # График плотности
        fig1 = ff.create_distplot(
            [male_data['sick_leave_days'], female_data['sick_leave_days']],
            group_labels=['Мужчины', 'Женщины'],
            colors=['blue', 'red'],
            show_hist=False  # Hide histograms, show only density curves
        )

        fig1.update_layout(
            title='Плотность sick_leave_days по полу',
            xaxis=dict(title='sick_leave_days'),
            yaxis=dict(title='Плотность'),
            width=400,  
            height=400  
        )

        st.plotly_chart(fig1)

    with col2:

        # График распределения sick_leave_days для старше и моложе 35 лет (первоначальный масштаб)
        older_data   = filtered_data[filtered_data['age'] > age_filter]
        younger_data = filtered_data[filtered_data['age'] <= age_filter]

        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
                                        x=older_data['sick_leave_days'], 
                                        opacity=0.5, 
                                        name=f'Старше {age_filter} лет'), 
                                    )
        
        fig2.add_trace(go.Histogram(
                                        x=younger_data['sick_leave_days'], 
                                        opacity=0.5, 
                                        name=f'Моложе {age_filter} лет')
                                    )
        fig2.update_layout(
            title='Распределение sick_leave_days по возрасту',
            xaxis=dict(title='sick_leave_days'),
            yaxis=dict(title='Частота'), 
            width=400,  
            height=400  

        )
        st.plotly_chart(fig2)


        # График плотности
        fig1 = ff.create_distplot(
            [older_data['sick_leave_days'], younger_data['sick_leave_days']],
            group_labels=[f'Старше {age_filter}', f'Моложе {age_filter}'],
            colors=['blue', 'red'],
            show_hist=False  # Hide histograms, show only density curves
        )

        fig1.update_layout(
            title='Плотность sick_leave_days по возрасту',
            xaxis=dict(title='sick_leave_days'),
            yaxis=dict(title='Плотность'),
            width=400,  
            height=400  
        )

        st.plotly_chart(fig1)


# ==========================================================================================
# Гипотезы
# ==========================================================================================

    st.subheader("Гипотезы")
    st.sidebar.markdown('''***В обоих случаях нулевая гипотеза предполагает, 
                              что разницы между распределениями выборок нет***''')
    col1, col2 = st.columns(2)

    if len(filtered_data) > 0:

# ------------------------------ Первая гипотеза -------------------------------------------
        with col1:
            # Первая гипотеза: Мужчины пропускают в течение года более 2 рабочих дней значимо чаще женщин
            st.markdown(f'''**Первая альтернативная гипотеза:** 
                        *Мужчины пропускают в течение года более {work_days_filter} рабочих дней 
                        значимо чаще женщин.*''')
            
            # Проверка нормальности распределения (t-тест)
            # Нулевая гипотеза - распределение нормальное
            _, normal_male_p_value   = stats.normaltest(male_data['sick_leave_days'])
            _, normal_female_p_value = stats.normaltest(female_data['sick_leave_days'])

            st.write("Проверка нормальности распределения:")
            st.write(f"Мужчины: p-значение = {round(normal_male_p_value, 2)}")
            st.write(f"Женщины: p-значение = {round(normal_female_p_value, 2)}")

            # Проверка, является ли распределение нормальным на уровне значимости
            if normal_male_p_value > alpha and normal_female_p_value > alpha:
                # Распределения являются нормальными, поэтому можно использовать t-тест
                statistic, p_value = stats.ttest_ind(
                                                        male_data['sick_leave_days'], 
                                                        female_data['sick_leave_days'],
                                                        alternative='greater'
                                                    )
                st.write(f"t-статистика: {statistic}")
                st.write(f"p-значение: {round(p_value, 2)}")

                if p_value < alpha:
                    st.write("ВЫВОД: Отвергаем нулевую гипотезу. Существуют статистически значимые различия.")
                else:
                    st.write("ВЫВОД: Не отвергаем нулевую гипотезу. Различия статистически незначимы.")
            else:
                st.write("Распределения не являются нормальными, воспользуемся непараметрическим тестом Манна — Уитни.")

                statistic, p_value = stats.mannwhitneyu(
                                                          male_data['sick_leave_days'], 
                                                          female_data['sick_leave_days'], 
                                                          alternative='greater'
                                                        )
                st.write(' ')
                st.write(f"Статистика: {statistic}")
                st.write(f"p-значение: {round(p_value, 2)}")

                if p_value < alpha:
                    st.write("ВЫВОД: Отвергаем нулевую гипотезу. Существуют статистически значимые различия.")
                else:
                    st.write("ВЫВОД: Не отвергаем нулевую гипотезу. Различия статистически незначимы.")

# ------------------------------ Вторая гипотеза -------------------------------------------
        with col2:

            # Вторая гипотеза: Работники старше 35 лет пропускают в течение года более 2 рабочих дней значимо чаще своих более молодых коллег

            st.markdown(f'''**Вторая альтернативная гипотеза:** 
                        *Работники старше {age_filter} лет пропускают в течение года более {work_days_filter} рабочих дней 
                        значимо чаще своих более молодых коллег*.''')


            # Проверка нормальности распределения (t-тест)
            _, normal_older_p_value   = stats.normaltest(older_data['sick_leave_days'])
            _, normal_younger_p_value = stats.normaltest(younger_data['sick_leave_days'])

            st.write("Проверка нормальности распределения:")
            st.write(f"Старше {age_filter} лет: p-значение = {round(normal_older_p_value, 2)}")
            st.write(f"Моложе {age_filter} лет: p-значение = {round(normal_younger_p_value, 2)}")

            # Проверка, является ли распределение нормальным на уровне значимости
            if normal_older_p_value > alpha and normal_younger_p_value > alpha:
            # Распределения являются нормальными, поэтому можно использовать t-тест
                statistic, p_value = stats.ttest_ind(   older_data['sick_leave_days'], 
                                                        younger_data['sick_leave_days'], 
                                                        alternative='greater'
                                                    )
                st.write(f"t-статистика: {statistic}")
                st.write(f"p-значение: {round(p_value, 2)}")

                if p_value < alpha:
                        st.write("ВЫВОД: Отвергаем нулевую гипотезу. Существуют статистически значимые различия.")
                else:
                    st.write("ВЫВОД: Не отвергаем нулевую гипотезу. Различия статистически незначимы.")
            else:
                
                st.write(f"Распределения не являются нормальными, воспользуемся непараметрическим тестом Манна — Уитни.")

                statistic, p_value = stats.mannwhitneyu(
                                                          older_data['sick_leave_days'], 
                                                          younger_data['sick_leave_days'], 
                                                          alternative='greater'
                                                        )
                st.write(' ')
                st.write(f"Статистика: {statistic}")
                st.write(f"p-значение: {round(p_value, 2)}")

                if p_value < alpha:
                    st.write("ВЫВОД:Отвергаем нулевую гипотезу. Существуют статистически значимые различия.")
                else:
                    st.write("ВЫВОД: Не отвергаем нулевую гипотезу. Различия статистически незначимы.")

# ------------------------------ Бонус -------------------------------------------
    with st.expander("Бонус"):
        st.image('https://papik.pro/izobr/uploads/posts/2023-02/1676773778_papik-pro-p-bolnichnii-list-karikatura-12.jpg', 
                        caption='Бонус', use_column_width=True)


