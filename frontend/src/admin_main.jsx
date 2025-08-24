import React from 'react';
import { createRoot } from 'react-dom/client';
import AdminApp from './AdminApp';
import './style.css';

const root = createRoot(document.getElementById('root'));
root.render(<AdminApp />);

