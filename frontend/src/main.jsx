import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Self-hosted fonts: no requests to third-party servers.
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/nunito'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
