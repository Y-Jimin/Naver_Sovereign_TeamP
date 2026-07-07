import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // 0.0.0.0으로 바인딩 — 서버 배포 시 외부 접속 허용, 로컬에선 LAN 테스트에도 유용
  },
});
