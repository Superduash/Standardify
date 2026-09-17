import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from './context/ToastContext'
import { ToastViewport } from './components/ui/toast/ToastViewport'
import { AppRouter } from './router'

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <AppRouter />
        <ToastViewport />
      </BrowserRouter>
    </ToastProvider>
  )
}

export default App
