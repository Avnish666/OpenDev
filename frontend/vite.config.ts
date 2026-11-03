import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({mode})=>{
 const env=loadEnv(mode,process.cwd(),'');
 const enabled=((env.ANALYTICS_STUDIO_LICENSED==='true'&&Boolean(env.VITE_AG_STUDIO_LICENSE_KEY))||env.ANALYTICS_STUDIO_EVALUATION==='true')&&existsSync(fileURLToPath(new URL('./studio/node_modules/ag-studio-react/package.json',import.meta.url)));
 return {plugins:[react()],resolve:{dedupe:['react','react-dom'],alias:{'@opendev/studio-renderer':fileURLToPath(new URL(enabled?'./studio/ProjectAnalyticsStudioRenderer.tsx':'./src/components/StudioUnavailable.tsx',import.meta.url))}},define:{__STUDIO_INSTALLED__:JSON.stringify(enabled),__STUDIO_LICENSED__:JSON.stringify((env.ANALYTICS_STUDIO_LICENSED==='true'&&Boolean(env.VITE_AG_STUDIO_LICENSE_KEY))),__STUDIO_EVALUATION__:JSON.stringify(env.ANALYTICS_STUDIO_EVALUATION==='true')}};
})
