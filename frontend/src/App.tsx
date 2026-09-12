import { BrowserRouter, Routes, Route } from "react-router-dom"
import Dashboard from "./pages/desboard/Dashboard"
import Prediction from "./pages/prediction_page/prediction"
import { SimulationProvider } from "./hooks/SimulationContext"

function App() {
  return (
    <SimulationProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/prediction" element={<Prediction />} />
        </Routes>
      </BrowserRouter>
    </SimulationProvider>
  )
}

export default App
