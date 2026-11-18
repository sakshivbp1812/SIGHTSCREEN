import { createRoot } from 'react-dom/client';
import App from './App';
import { Standalone } from './components/CatchUp';
import './style.css';

createRoot(document.getElementById('root')!).render(new URLSearchParams(location.search).has('catchup') ? <Standalone /> : <App />);
