// src/App.js
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import VideoPage from './pages/VideoPage';
import Home from './pages/Home';
import Login from './pages/Login';
import Upload from './pages/Upload';
import VideoList from './pages/VideoList';
import Account from './pages/Account';
import Header from './components/Header';
import './App.css';

function App() {
  return (
    <Router>
      <Header /> {/* Отображается на всех страницах */}

      {/* Основное содержимое страниц, включая маршруты */}
      <div className="page-wrapper">
        {/* Весь блок <Routes> с конкретными <Route> теперь внутри! */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/upload" element={<Upload />} />
          {/* Убедитесь, что маршрут /videolist нужен, если главная страница уже показывает список */}
          <Route path="/videolist" element={<VideoList />} />
          <Route path="/video/:id" element={<VideoPage />} />
          <Route path="/account" element={<Account />} />
        </Routes>
      </div> {/* Конец page-wrapper */}

      {/* Если есть футер или другие элементы, которые должны быть всегда, они могут быть здесь, вне page-wrapper и Routes */}
    </Router>
  );
}

export default App;