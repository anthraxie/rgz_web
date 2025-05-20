// src/pages/Home.js
import React, { useEffect, useState } from 'react';
// import Header from '../components/Header'; // Header должен рендериться в App.js
import VideoCard from '../components/VideoCard';
import axios from 'axios';
import backgroundImage from './background.png'; // <-- Импортируем файл фонового изображения (Убедитесь, что имя файла правильное)

// Определим основные цвета палитры прямо здесь для удобства
// В идеале, их лучше вынести в отдельный файл с константами или использовать CSS-переменные глобально
const colors = {
    darkGreenBg: '#1a241c', // Очень темный зеленый/почти черный из леса
    darkGreenAccent: '#283c2f', // Темный зеленый акцент
    forestGreen: '#3a5a40', // Более выраженный зеленый из леса
    lightGreenAccent: '#ffffff', // Светлый приглушенный зеленый для акцентов
    textLight: '#e0e0e0', // Светлый текст для темного фона (это будет наш белый/светло-серый)
    textMedium: '#b0b0b0', // Средний серый для менее важного текста
    errorRed: '#e57373', // Мягкий красный для ошибок на темном фоне
};


const Home = () => {
    // Состояние для хранения списка видео, полученных с бэкенда
    const [videos, setVideos] = useState([]);
    // Состояние для отслеживания загрузки данных
    const [loading, setLoading] = useState(true);
    // Состояние для хранения ошибок
    const [error, setError] = useState(null);

    // Хук useEffect для загрузки данных при монтировании компонента
    useEffect(() => {
        const fetchVideos = async () => {
            try {
                setLoading(true);
                setError(null); // Сбрасываем ошибку перед новым запросом

                const response = await axios.get('http://37.194.42.234:8000/api/videos/');
                setVideos(response.data);

            } catch (err) {
                console.error("Ошибка при загрузке видео:", err);
                // Улучшенная обработка ошибок API, если бэкенд предоставляет детали
                let errorMessage = 'Не удалось загрузить список видео.';
                   if (err.response && err.response.data && err.response.data.detail) {
                       errorMessage += ' ' + err.response.data.detail;
                   } else if (err.message) {
                        errorMessage += ' ' + err.message;
                   }
                setError(errorMessage);
            } finally {
                setLoading(false);
            }
        };

        fetchVideos();
    }, []); // Пустой массив зависимостей означает, что хук сработает один раз при монтировании

    // Стили для основного контейнера с фоном
    const mainContainerStyle = {
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
        width: '100vw',
        minHeight: '100vh',
        margin: 0,
        padding: 0,
        boxSizing: 'border-box',
        overflowX: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        // Убедитесь, что это значение соответствует высоте вашей шапки!
        paddingTop: '80px', // Примерное значение, скорректируйте по высоте Header
        color: colors.textLight, // Базовый цвет текста для всей страницы
    };

      // Стили для внутреннего контейнера контента
    const contentContainerStyle = {
        width: '100%',
        maxWidth: '1200px',
        margin: '20px auto', // Добавим вертикальные отступы сверху и снизу
        padding: '0 20px',
        boxSizing: 'border-box',
        flexGrow: 1, // Позволяет контенту заполнять доступное пространство
    };


    // Стили для сообщения загрузки
    const loadingStyle = {
        textAlign: 'center',
        marginTop: '80px', // Отступ от фиксированной шапки
        color: colors.lightGreenAccent, // Цвет текста загрузки
        fontSize: '1.2em',
        textShadow: '1px 1px 3px rgba(0,0,0,0.7)', // Тень для читаемости на фоне
    };

    // Стили для сообщения об ошибке
    const errorStyle = {
        textAlign: 'center',
        marginTop: '80px', // Отступ от фиксированной шапки
        color: colors.errorRed, // Цвет текста ошибки
        fontSize: '1.2em',
        textShadow: '1px 1px 3px rgba(0,0,0,0.7)', // Тень для читаемости
        backgroundColor: 'rgba(0, 0, 0, 0.5)', // Полупрозрачный фон для читаемости
        padding: '10px',
        borderRadius: '5px',
        margin: '20px auto', // Центрируем и добавляем отступы
        maxWidth: '600px', // Ограничиваем ширину блока ошибки
    };

    // Стили для заголовка H1
    const titleStyle = {
            textAlign: 'center',
            marginBottom: '30px',
            color: colors.lightGreenAccent, // Вернули светло-зеленый цвет
            textShadow: '2px 2px 6px rgba(0,0,0,0.8)', // Тень
            fontSize: '2.5em', // Вернули размер
    };

    // Стили для сообщения "Видео пока нет"
    const noVideosStyle = {
        textAlign: 'center',
        color: colors.textMedium, // Серый цвет текста
        textShadow: '1px 1px 3px rgba(0,0,0,0.5)',
        fontSize: '1.2em',
        marginTop: '50px',
    };

    // Стили для сетки видеокарточек
    const videoGridStyle = {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '30px',
        padding: '20px 0',
    };


    // Если данные загружаются, показываем сообщение о загрузке
    if (loading) {
        return (
            <div style={mainContainerStyle}>
                <div style={loadingStyle}>Загрузка видео...</div>
            </div>
        );
    }

    // Если произошла ошибка, показываем сообщение об ошибке
    if (error) {
        return (
            <div style={mainContainerStyle}>
                    <div style={errorStyle}>Ошибка: {error}</div>
            </div>
        );
    }

    // Если видео успешно загружены, отображаем их
    return (
        <div style={mainContainerStyle}>
            <div style={contentContainerStyle}>
                <h1 style={titleStyle}>
                    Добро пожаловать!
                </h1>

                {videos.length === 0 ? (
                    <div style={noVideosStyle}>Видео пока нет.</div>
                ) : (
                    <div className="video-grid" style={videoGridStyle}>
                        {videos.map(video => (
                            <VideoCard
                                key={video.id}
                                id={video.id}
                                title={video.title}
                                description={video.description}
                                thumbnail={video.thumbnail}
                                views_count={video.views_count} 
                                likes_count={video.likes_count} // Передаем likes_count
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Home;