// frontend/src/pages/VideoPage.js

import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import ReactPlayer from 'react-player';
import axios from 'axios';
import Header from '../components/Header';
import VideoComments from '../components/VideoComments';
import './styles/VideoPage.css';

// Импортируем иконки, если используем, например, React Icons (нужно установить: npm install react-icons)
// import { FaThumbsUp as LikedIcon, FaRegThumbsUp as UnlikedIcon } from 'react-icons/fa'; // Пример иконок

const VideoPage = () => {
    const { id } = useParams();
    const [video, setVideo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const isLoggedIn = !!localStorage.getItem('access_token');

    // Состояние для лайков
    const [likesCount, setLikesCount] = useState(0);
    const [isLiked, setIsLiked] = useState(false);

    // useRef для отслеживания, был ли уже инкрементирован просмотр для текущего видео
    const hasIncrementedView = useRef(false);

    useEffect(() => {
        const fetchVideo = async () => {
            setLoading(true);
            setError('');
            try {
                // Добавляем токен авторизации для получения информации о лайках текущего пользователя
                const config = isLoggedIn ? {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                } : {};

                const response = await axios.get(`http://37.194.42.234:8000/api/videos/${id}/`, config);
                setVideo(response.data);
                // Устанавливаем состояния лайков из полученных данных
                setLikesCount(response.data.likes_count);
                setIsLiked(response.data.is_liked);

            } catch (err) {
                console.error('Ошибка при загрузке видео:', err);
                let errorMessage = 'Ошибка загрузки видео';
                if (err.response && err.response.status === 404) {
                    errorMessage = 'Видео не найдено';
                    setVideo(null);
                }
                setError(errorMessage);
            } finally {
                setLoading(false);
            }
        };

        fetchVideo();

        // Сбрасываем флаги, если ID видео меняется (для перехода между видео)
        return () => {
            hasIncrementedView.current = false;
        };
    }, [id, isLoggedIn]); // Зависимость от ID видео и состояния входа (для is_liked)

    // Отдельный useEffect для инкрементации просмотра
    useEffect(() => {
        if (video && !error && !hasIncrementedView.current) {
            const incrementViewCount = async () => {
                try {
                    const incrementResponse = await axios.post(`http://37.194.42.234:8000/api/videos/${video.id}/increment_view/`);
                    console.log('Ответ инкрементации:', incrementResponse.data);
                    
                    setVideo(prevVideo => {
                        if (prevVideo) {
                            return { ...prevVideo, views_count: incrementResponse.data.views_count };
                        }
                        return prevVideo;
                    });
                    
                    hasIncrementedView.current = true;
                } catch (err) {
                    console.error('Ошибка при инкрементации счетчика просмотров:', err);
                }
            };
            incrementViewCount();
        }
    }, [video, error]);

    // --- НОВАЯ ФУНКЦИЯ: Обработка лайков ---
    const handleLikeToggle = async () => {
        if (!isLoggedIn) {
            alert('Для того чтобы поставить лайк, пожалуйста, войдите в систему.');
            return;
        }

        try {
            const token = localStorage.getItem('access_token');
            const config = {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            };
            
            const response = await axios.post(`http://37.194.42.234:8000/api/videos/${video.id}/like_toggle/`, {}, config);
            
            console.log('Ответ лайка:', response.data);
            setLikesCount(response.data.likes_count);
            setIsLiked(response.data.is_liked);
            // Можно добавить небольшое уведомление об успешном лайке/дизлайке
            // alert(response.data.message); 

        } catch (err) {
            console.error('Ошибка при переключении лайка:', err);
            // Если ошибка 401 (Unauthorized), сообщить пользователю
            if (err.response && err.response.status === 401) {
                alert('Для выполнения этого действия вы должны быть авторизованы.');
            } else {
                alert('Произошла ошибка при попытке поставить/снять лайк.');
            }
        }
    };
    // --- КОНЕЦ НОВОЙ ФУНКЦИИ ---


    if (loading) return <div className="page-message">Загрузка...</div>;
    if (error && !video) return <div className="page-message">{error}</div>;
    if (!video && !loading) return <div className="page-message">Видео не найдено</div>;

    return (
        <div>
            <Header />
            <div className="content-layout">

                <div className="video-and-info">
                    <div className="player-wrapper">
                        <ReactPlayer
                            className="react-player"
                            url={video.file_url}
                            controls
                            width="100%"
                            height="100%"
                            config={{
                                file: {
                                    attributes: {
                                        controlsList: 'nodownload'
                                    }
                                }
                            }}
                        />
                    </div>

                    <div className="video-info">
                        <h1>{video.title}</h1>
                        <p>Просмотры: {video.views_count !== undefined ? video.views_count : 'Загрузка...'}</p>
                        <p>{video.author_username} • {new Date(video.uploaded_at).toLocaleDateString()}</p>
                        <p className="video-description-text">{video.description}</p> {/* Добавил класс для описания */}

                        {/* --- НОВАЯ КНОПКА ЛАЙКА --- */}
                        <div className="video-actions">
                            <button 
                                onClick={handleLikeToggle} 
                                className={`like-button ${isLiked ? 'liked' : ''}`}
                            >
                                {/* Можно использовать текст, или установить React Icons: npm install react-icons */}
                                {isLiked ? '❤️ Нравится' : '🤍 Нравится'} 
                                {/* Пример с иконками: {isLiked ? <LikedIcon /> : <UnlikedIcon />} Нравится */}
                            </button>
                            <span className="likes-count">
                                {likesCount} Лайков
                            </span>
                        </div>
                        {/* --- КОНЕЦ КНОПКИ ЛАЙКА --- */}

                    </div>
                </div>

                <div className="comments-sidebar">
                    <VideoComments videoId={id} isLoggedIn={isLoggedIn} />
                </div>

            </div>
        </div>
    );
};

export default VideoPage;