interface SidebarProps {
  pagina: string;
  setPagina: (pagina: string) => void;
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
}

export default function Sidebar({
  pagina,
  setPagina,
  isOpen,
  setIsOpen,
}: SidebarProps) {
  const navegar = (ruta: string) => {
    setPagina(ruta);
    setIsOpen(false);
  };

  return (
    <>
      {isOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setIsOpen(false)}
        />
      )}

      <aside className={`sidebar ${isOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-logo">
          <div className="logo-icon">◉</div>

          <div>
            <strong>FaceID</strong>
            <span>Recognition System</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <p className="nav-title">PRINCIPAL</p>

          <button
            className={pagina === "dashboard" ? "nav-item active" : "nav-item"}
            onClick={() => navegar("dashboard")}
          >
            <span>⌂</span>
            Dashboard
          </button>

          <button
            className={pagina === "reconocimiento" ? "nav-item active" : "nav-item"}
            onClick={() => navegar("reconocimiento")}
          >
            <span>◎</span>
            Reconocimiento
          </button>

          <button
            className={pagina === "login-facial" ? "nav-item active" : "nav-item"}
            onClick={() => navegar("login-facial")}
          >
            <span>⚿</span>
            Login Facial
          </button>

          <p className="nav-title">GESTIÓN</p>

          <button
            className={pagina === "registro" ? "nav-item active" : "nav-item"}
            onClick={() => navegar("registro")}
          >
            <span>＋</span>
            Registro Facial
          </button>

          <button
            className={pagina === "probabilidades" ? "nav-item active" : "nav-item"}
            onClick={() => navegar("probabilidades")}
          >
            <span>◒</span>
            Probabilidades
          </button>

          <button
            className={pagina === "historial" ? "nav-item active" : "nav-item"}
            onClick={() => navegar("historial")}
          >
            <span>▤</span>
            Historial
          </button>
        </nav>

        <div className="sidebar-status">
          <div className="status-dot" />

          <div>
            <strong>Sistema operativo</strong>
            <span>Todos los servicios activos</span>
          </div>
        </div>
      </aside>
    </>
  );
}

