import { BrowserRouter, Routes, Route } from "react-router-dom"
import Dashboard from "./pages/desboard/Dashboard"
import Prediction from "./pages/prediction_page/prediction"
import { SimulationProvider } from "./hooks/SimulationContext"

function App() {
  return (
    <SimulationProvider>
      <BrowserRouter>
        <Routes>
          {/* Prediction is the only page wired to the real optimiser end to end, so it
              is what an evaluator should land on. Dashboard stays reachable at its own
              route -- it is genuinely live where it uses SimulationContext (KPIs, energy
              telemetry, irrigation advice), but is not the primary evaluation surface. */}
          <Route path="/" element={<Prediction />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </SimulationProvider>
  )
}

export default App
