import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './JS/App.js';
import * as serviceWorker from './serviceWorker';
import { Provider } from 'react-redux';
import { store } from './JS/Storage.js';

createRoot(
  document.getElementById('root')
).render(  
<React.StrictMode>
  <Provider store = {store}>
    <App />
  </Provider>
</React.StrictMode>
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();