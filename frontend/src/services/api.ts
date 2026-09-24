import { decodeResponse } from './protocol.mjs';
import { buildApiHeaders } from './request.mjs';
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace(/\/$/,'');
const inFlightStatusRequests = new Map<string, Promise<unknown>>();
export function authHeaders(): Record<string,string> {
  const token = typeof window === 'undefined' ? '' : sessionStorage.getItem('ip-sakti-api-token');
  return token ? {Authorization:`Bearer ${token}`} : {};
}
export async function api(path:string, body?:unknown) {
  const isStatusRequest = path === '/status' && body === undefined;
  const requestKey = isStatusRequest ? `${API_BASE}/api/status:${authHeaders().Authorization || 'anonymous'}` : '';
  if (isStatusRequest) {
    const existing = inFlightStatusRequests.get(requestKey);
    if (existing) return existing;
  }
  const request = requestApi(path, body);
  if (isStatusRequest) {
    inFlightStatusRequests.set(requestKey, request);
    request.then(
      () => inFlightStatusRequests.delete(requestKey),
      () => inFlightStatusRequests.delete(requestKey),
    );
  }
  return request;
}
async function requestApi(path:string, body?:unknown) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const hasJsonBody = body !== undefined;
    const response = await fetch(`${API_BASE}/api${path}`, { method:hasJsonBody ? 'POST' : 'GET', credentials:'include', headers:buildApiHeaders(authHeaders(), hasJsonBody), body:hasJsonBody ? JSON.stringify(body) : undefined, signal:controller.signal });
    return await decodeResponse(response);
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw new Error('The request timed out. No successful result is asserted. Check the backend and retry.');
    if (error instanceof TypeError) throw new Error('Cannot reach the backend. Start it and check the API address and CORS settings.');
    throw error;
  } finally { clearTimeout(timeout); }
}
export async function download(path:string,filename:string) {
  const response=await fetch(`${API_BASE}/api${path}`,{credentials:'include',headers:authHeaders()});
  if(!response.ok) throw new Error(`Download failed (HTTP ${response.status}).`);
  const url=URL.createObjectURL(await response.blob());
  const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export async function fileBase64(file:File):Promise<string> {
  return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('File could not be read.'));reader.readAsDataURL(file);});
}
