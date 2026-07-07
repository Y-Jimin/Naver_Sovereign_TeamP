import logo from "../assets/logo.png";

export function Header() {
  return (
    <header className="app-header">
      <img src={logo} alt="Snap Meal" className="app-logo-img" />
      <p className="app-tagline">영수증 한 장으로 오늘 먹은 영양성분을 확인하세요</p>
    </header>
  );
}
