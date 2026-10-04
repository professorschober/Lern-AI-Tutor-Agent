import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir:'./tests', fullyParallel:false, workers:1, timeout:45000,
  use:{baseURL:'http://127.0.0.1:5173',headless:true,viewport:{width:1440,height:1000},
    launchOptions:{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || undefined}},
  webServer:[
    {command:'..\\.venv\\Scripts\\python.exe -m uvicorn tests.browser_server:app --app-dir ../backend --host 127.0.0.1 --port 8000',url:'http://127.0.0.1:8000/api/health',reuseExistingServer:false},
    {command:'npm run dev',url:'http://127.0.0.1:5173',env:{TUTOR_API_TARGET:'http://127.0.0.1:8000'},reuseExistingServer:false}
  ]
})
