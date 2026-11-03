/** Loopback-only Community demo server. No production host or authentication changes. */
import {createServer} from 'vite';
import {fileURLToPath} from 'node:url';
if(process.env.OPENDEV_DEMO!=='synthetic-local'||process.env.APP_ENV!=='testing'||['CHECKOUT_ENABLED','RECEIPT_PROCESSING_ENABLED','LLM_ENABLED'].some(k=>process.env[k]!=='false'))throw new Error('Explicit restricted local demo environment required');
if(process.env.ANALYTICS_STUDIO_EVALUATION==='true'||process.env.ANALYTICS_STUDIO_LICENSED==='true')throw new Error('Use the separate optional Studio evaluation procedure');
process.env.ANALYTICS_STUDIO_EVALUATION='false';
process.env.ANALYTICS_STUDIO_LICENSED='false';
process.env.VITE_API_URL='';
process.env.VITE_ANALYTICS_RENDERER='community';
const root=fileURLToPath(new URL('.',import.meta.url));
process.chdir(root);
const server=await createServer({root,envDir:false,server:{host:'127.0.0.1',port:5173,strictPort:true,proxy:{'/api':{target:'http://127.0.0.1:8000'}}}});
await server.listen();
server.printUrls();
let closing=false;
async function close(){if(closing)return;closing=true;await server.close();process.exit(0);}
process.once('SIGINT',close);process.once('SIGTERM',close);
