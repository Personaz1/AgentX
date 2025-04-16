import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <h1>NeuroRAT C2 - Панель управления</h1>
        <div>
          <button onClick={() => setCount((count) => count + 1)}>
            Счетчик: {count}
          </button>
        </div>
      </div>
    </>
  )
}

export default App
