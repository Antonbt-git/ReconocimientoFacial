import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import RegistroFacial from "./pages/RegistroFacial";
import Reconocimiento from "./pages/Reconocimiento";
import LoginFacial from "./pages/LoginFacial";
import Probabilidades from "./pages/Probabilidades";
import Historial from "./pages/Historial";

export default function App() {
  const [pagina, setPagina] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderPagina = () => {
    switch (pagina) {
      case "registro":
        return <RegistroFacial />;

      case "reconocimiento":
        return <Reconocimiento />;

      case "login-facial":
        return <LoginFacial />;

      case "probabilidades":
        return <Probabilidades />;

      case "historial":
        return <Historial />;

      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        pagina={pagina}
        setPagina={setPagina}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
      />

      <div className="main-wrapper">
        <Header onMenuClick={() => setSidebarOpen(true)} />

        <main className="main-content">
          {renderPagina()}
        </main>
      </div>
    </div>
  );
}

