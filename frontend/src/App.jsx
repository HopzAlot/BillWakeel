import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import "./App.css";



function App() {
  return (
    <BrowserRouter>
      <header className="app-header">
        <Link to="/" className="brand">
          BillWakeel
        </Link>

        <nav>
          <Link to="/">Home</Link>
          <Link to="/upload">Upload Bill</Link>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;